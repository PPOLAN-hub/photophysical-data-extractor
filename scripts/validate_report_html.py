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


def main(json_path, html_path):
    source_path = Path(json_path)
    report_path = Path(html_path)
    documents = render_html.load_documents(source_path)
    source = report_path.read_text(encoding="utf-8")
    expected = expected_highlights(documents)
    problems = []

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
    if len(sys.argv) != 3:
        raise SystemExit("Usage: validate_report_html.py paper_data.json report.html")
    main(sys.argv[1], sys.argv[2])
