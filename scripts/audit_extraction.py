#!/usr/bin/env python3
"""Read-only heuristic audit for PDE JSON; emits warnings and never rewrites data."""

import json
import re
import sys
from collections import defaultdict
from pathlib import Path


COMPONENT_PATTERN = re.compile(r"(?:τ|tau)\s*[123]\b", re.IGNORECASE)
PERCENT_PATTERN = re.compile(r"(?<![\d.])(\d+(?:\.\d+)?)\s*%")


def audit(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    warnings = []
    samples = data.get("samples", [])
    row_ids = [sample.get("row_id") for sample in samples]
    duplicates = sorted({row_id for row_id in row_ids if row_id and row_ids.count(row_id) > 1})
    if duplicates:
        warnings.append({"kind": "duplicate_row_id", "row_ids": duplicates})

    rows = {sample.get("row_id"): sample for sample in samples if sample.get("row_id")}
    for sample in samples:
        row_id = sample.get("row_id")
        for field_name in ("tau_f", "tau_df", "tau_p"):
            field = sample.get("fields", {}).get(field_name)
            if not isinstance(field, dict) or field.get("status") != "reported":
                continue
            raw = str(field.get("raw_value") or "")
            if len(COMPONENT_PATTERN.findall(raw)) < 2:
                continue
            weights = [float(value) for value in PERCENT_PATTERN.findall(raw)]
            if len(weights) >= 2 and not 99.5 <= sum(weights) <= 100.5:
                warnings.append(
                    {
                        "kind": "component_weight_sum",
                        "row_id": row_id,
                        "field": field_name,
                        "weights": weights,
                        "sum_percent": sum(weights),
                    }
                )
        for field_name in ("g_lum", "g_abs"):
            field = sample.get("fields", {}).get(field_name)
            if not isinstance(field, dict) or field.get("status") != "reported":
                continue
            raw_value = str(field.get("raw_value") or "").strip()
            context = field.get("measurement_context")
            wavelength = str(context.get("wavelength") or "").strip() if isinstance(context, dict) else ""
            if not wavelength:
                warnings.append(
                    {
                        "kind": "dissymmetry_missing_wavelength",
                        "row_id": row_id,
                        "field": field_name,
                    }
                )
            if raw_value and not re.match(r"^[+\-−]", raw_value):
                warnings.append(
                    {
                        "kind": "dissymmetry_sign_not_explicit",
                        "row_id": row_id,
                        "field": field_name,
                        "raw_value": raw_value,
                    }
                )

    evidence_groups = defaultdict(list)
    referenced = set()
    for sample in samples:
        for group in ("identity", "conditions", "fields"):
            for field in sample.get(group, {}).values():
                if isinstance(field, dict) and field.get("evidence_id"):
                    referenced.add(field["evidence_id"])
    analysis = data.get("article_analysis") or {}
    for item in list((analysis.get("koi") or {}).values()) + [analysis.get("one_sentence_innovation")]:
        if isinstance(item, dict):
            referenced.update(item.get("evidence_ids") or [])
    for item in analysis.get("logic_skeleton") or []:
        if isinstance(item, dict):
            referenced.update(item.get("evidence_ids") or [])

    for evidence in data.get("evidence_ledger", []):
        evidence_id = evidence.get("evidence_id")
        row_id = evidence.get("row_id")
        if row_id not in rows and row_id != "PAPER":
            warnings.append({"kind": "unknown_evidence_row", "evidence_id": evidence_id, "row_id": row_id})
        key = (row_id, evidence.get("field_name"))
        value = str(evidence.get("extracted_value") or "").strip()
        if value:
            evidence_groups[key].append((evidence_id, value))
        if evidence_id and evidence_id not in referenced:
            warnings.append({"kind": "unreferenced_evidence", "evidence_id": evidence_id})

    for (row_id, field_name), entries in evidence_groups.items():
        distinct = sorted({value for _, value in entries})
        if len(distinct) > 1:
            warnings.append(
                {
                    "kind": "cross_source_value_candidate",
                    "row_id": row_id,
                    "field": field_name,
                    "values": distinct,
                    "evidence_ids": [evidence_id for evidence_id, _ in entries],
                }
            )
    return {"status": "review" if warnings else "clear", "warning_count": len(warnings), "warnings": warnings}


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("Usage: audit_extraction.py paper_data.json")
    print(json.dumps(audit(Path(sys.argv[1])), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
