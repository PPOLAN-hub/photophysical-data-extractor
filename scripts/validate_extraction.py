#!/usr/bin/env python3
"""Check evidence integrity for a canonical RTP extraction JSON file."""
import json
import sys
from pathlib import Path

VALID_TYPES = {"direct_text", "table_value", "figure_estimate", "calculated_from_reported_values", "author_assignment"}
VALID_STATUS = {"reported", "not_reported", "uncertain"}


def validate_analysis_item(label, item, ledger, problems):
    if not isinstance(item, dict) or not str(item.get("text", "")).strip():
        problems.append(f"{label}: needs non-empty text")
        return
    evidence_ids = item.get("evidence_ids")
    if not isinstance(evidence_ids, list) or not evidence_ids:
        problems.append(f"{label}: needs evidence_ids")
        return
    for evidence_id in evidence_ids:
        if evidence_id not in ledger:
            problems.append(f"{label}: unknown evidence_id {evidence_id}")


def main(path_text: str) -> int:
    data = json.loads(Path(path_text).read_text(encoding="utf-8"))
    problems = []
    ledger = {e.get("evidence_id"): e for e in data.get("evidence_ledger", [])}
    if len(ledger) != len(data.get("evidence_ledger", [])):
        problems.append("duplicate or missing evidence_id")
    for evidence_id, e in ledger.items():
        if not evidence_id or e.get("type") not in VALID_TYPES:
            problems.append(f"invalid evidence type/id: {evidence_id}")
        if e.get("type") == "figure_estimate" and e.get("confidence") == "high":
            problems.append(f"{evidence_id}: figure estimate cannot be high confidence")
        if e.get("type") == "figure_estimate" and "图中估读" not in e.get("manual_check_note", ""):
            problems.append(f"{evidence_id}: figure estimate note must contain 图中估读")
    for sample in data.get("samples", []):
        row_id = sample.get("row_id")
        for group in ("identity", "conditions", "fields"):
            for name, field in sample.get(group, {}).items():
                if not isinstance(field, dict):
                    problems.append(f"{row_id}.{group}.{name}: must use the evidence-bearing field object")
                    continue
                status = field.get("status")
                if status not in VALID_STATUS:
                    problems.append(f"{row_id}.{group}.{name}: invalid status")
                evidence_id = field.get("evidence_id")
                if status == "reported" and (field.get("raw_value") is None or evidence_id not in ledger):
                    problems.append(f"{row_id}.{group}.{name}: reported value needs valid evidence_id")
                if status != "reported" and field.get("raw_value") is not None:
                    problems.append(f"{row_id}.{group}.{name}: non-reported status must have null raw_value")
                if name == "tau_p" and status == "reported":
                    evidence = ledger.get(evidence_id) or {}
                    quote = evidence.get("quote", "").lower()
                    field_name = evidence.get("field_name", "").lower()
                    if "phosphor" not in quote and "rtp" not in quote and "tau_p" not in field_name and "τp" not in quote:
                        problems.append(f"{row_id}.tau_p: evidence must explicitly identify phosphorescence/RTP or tau_p")
    analysis = data.get("article_analysis")
    if analysis is not None:
        if not isinstance(analysis, dict):
            problems.append("article_analysis: must be an object")
        else:
            for key, item in analysis.get("koi", {}).items():
                validate_analysis_item(f"article_analysis.koi.{key}", item, ledger, problems)
            validate_analysis_item("article_analysis.one_sentence_innovation", analysis.get("one_sentence_innovation"), ledger, problems)
            skeleton = analysis.get("logic_skeleton", [])
            if not isinstance(skeleton, list) or not skeleton:
                problems.append("article_analysis.logic_skeleton: needs at least one stage")
            else:
                for index, item in enumerate(skeleton, start=1):
                    validate_analysis_item(f"article_analysis.logic_skeleton[{index}]", item, ledger, problems)
    if problems:
        print("INVALID")
        print("\n".join(problems))
        return 1
    print(f"VALID: {len(data.get('samples', []))} samples, {len(ledger)} evidence records")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Usage: validate_extraction.py paper_data.json")
    raise SystemExit(main(sys.argv[1]))
