#!/usr/bin/env python3
"""Verify that a PDE HTML report was produced by the bundled renderer and preserves key highlights."""
import re
import sys
from pathlib import Path

import render_html


TARGET_FIELDS = ("lambda_p", "tau_p", "phi_p")


def reported(sample, name):
    field = sample.get("fields", {}).get(name)
    return isinstance(field, dict) and field.get("status") == "reported"


def expected_highlights(documents):
    expected = {
        "rt": False,
        "77k": False,
        "best_rt_tau": False,
        "best_rt_phi": False,
        "best_77k_tau": False,
    }
    for document in documents:
        for sample in document.get("samples", []):
            for name in TARGET_FIELDS:
                field = sample.get("fields", {}).get(name)
                if not reported(sample, name):
                    continue
                kind = render_html.doped_matrix_temperature(sample, field)
                if kind == "rt":
                    expected["rt"] = True
                    expected["best_rt_tau"] |= name == "tau_p"
                    expected["best_rt_phi"] |= name == "phi_p"
                elif kind == "77k":
                    expected["77k"] = True
                    expected["best_77k_tau"] |= name == "tau_p"
    return expected


def has_value_class(source, class_name):
    pattern = rf"<span\s+class=['\"][^'\"]*\b{re.escape(class_name)}\b[^'\"]*['\"]"
    return re.search(pattern, source) is not None


def main(json_path, html_path, config_path=None):
    source_path = Path(json_path)
    report_path = Path(html_path)
    documents = render_html.load_documents(source_path)
    source = report_path.read_text(encoding="utf-8")
    expected = expected_highlights(documents)
    problems = []

    expected_sample_rows = sum(len(document.get("samples", [])) for document in documents)
    actual_sample_rows = len(re.findall(r"<tr class=['\"]sample-row['\"]", source))
    if actual_sample_rows != expected_sample_rows:
        problems.append(
            f"sample-condition row mismatch: expected {expected_sample_rows}, found {actual_sample_rows}"
        )
    rendered_rows = {}
    for row_id, body in re.findall(
        r"<tr class=['\"]sample-row['\"] data-row-id=['\"]([^'\"]+)['\"][^>]*>(.*?)</tr>",
        source,
        flags=re.DOTALL,
    ):
        rendered_rows.setdefault(row_id, []).append(body)
    for document in documents:
        for sample in document.get("samples", []):
            row_id = str(sample.get("row_id") or "未标注")
            bodies = rendered_rows.get(row_id, [])
            if not bodies:
                problems.append(f"missing rendered sample-condition row: {row_id}")
                continue
            expected_evidence = [
                field.get("evidence_id")
                for field in sample.get("fields", {}).values()
                if isinstance(field, dict) and field.get("status") == "reported" and field.get("evidence_id")
            ]
            body = next(
                (candidate for candidate in bodies if all(f"[{item}]" in candidate for item in expected_evidence)),
                bodies[0],
            )
            for name, field in sample.get("fields", {}).items():
                if not isinstance(field, dict) or field.get("status") != "reported":
                    continue
                evidence_id = field.get("evidence_id")
                if evidence_id and f"[{evidence_id}]" not in body:
                    problems.append(
                        f"sample-condition row {row_id} does not contain {name} evidence {evidence_id}"
                    )

    table_columns, _ = render_html.load_report_config(config_path)
    for name, label, group in table_columns:
        if group != "fields" or name == "emission_assignment":
            continue
        expected_header = f"<th class='metric-header'>{label}</th>"
        if expected_header not in source:
            problems.append(f"missing configured physical table header: {name}")

    if '<meta name="pde-renderer" content="photophysical-data-extractor">' not in source:
        problems.append("report was not produced by the bundled PDE renderer")
    if ".doped-rt-phosphor{color:#D9001B}" not in source:
        problems.append("room-temperature doped phosphorescence color is not #D9001B")
    if ".doped-77k-phosphor{color:#0000FF}" not in source:
        problems.append("77 K doped phosphorescence color is not #0000FF")

    checks = (
        ("rt", "doped-rt-phosphor", "missing red RT doped-matrix λP/τP/ΦP highlighting"),
        ("77k", "doped-77k-phosphor", "missing blue 77 K doped-matrix λP/τP/ΦP highlighting"),
        ("best_rt_tau", "best-lifetime", "missing bold/underlined maximum RT τP"),
        ("best_rt_phi", "best-efficiency", "missing bold/underlined maximum RT ΦP"),
        ("best_77k_tau", "best-77k-lifetime", "missing bold maximum 77 K τP"),
    )
    for flag, class_name, message in checks:
        if expected[flag] and not has_value_class(source, class_name):
            problems.append(message)

    if problems:
        for problem in problems:
            print(f"ERROR: {problem}")
        raise SystemExit(1)
    print("HTML highlight validation passed")


if __name__ == "__main__":
    if len(sys.argv) not in {3, 4}:
        raise SystemExit("Usage: validate_report_html.py paper_data.json report.html [report_config.json]")
    main(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) == 4 else None)
