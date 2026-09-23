#!/usr/bin/env python3
"""Validate deterministic PDE Obsidian Markdown against core archive invariants."""

from __future__ import annotations

import re
import sys
from pathlib import Path


def table_column_count(line):
    return max(0, len(re.findall(r"(?<!\\)\|", line)) - 1)


def main(path_text):
    path = Path(path_text)
    source = path.read_text(encoding="utf-8")
    problems = []
    if not source.startswith("---\n"):
        problems.append("missing YAML frontmatter")
    if "skill: photophysical-data-extractor" not in source:
        problems.append("missing skill marker")
    if "archive_convention_sha256:" not in source:
        problems.append("missing archive convention digest")
    if not any(marker in source for marker in ("<!-- PDE:SLOT:BEGIN -->", "<!-- PDE:BATCH:BEGIN -->")):
        problems.append("missing stable-block begin marker")
    if not any(marker in source for marker in ("<!-- PDE:SLOT:END -->", "<!-- PDE:BATCH:END -->")):
        problems.append("missing stable-block end marker")
    heading_count = len(re.findall(r"^#{1,2}\s", source, flags=re.MULTILINE))
    if heading_count > 8:
        problems.append(f"too many level-1/2 headings: {heading_count}")
    for line in source.splitlines():
        if line.startswith("|") and table_column_count(line) > 5:
            problems.append(f"table exceeds five columns: {line[:80]}")
    if "## 🎯 30 秒版" not in source:
        problems.append("missing ADHD 30-second section")
    else:
        section = source.split("## 🎯 30 秒版", 1)[1].split("\n## ", 1)[0]
        bullets = [line for line in section.splitlines() if line.startswith("- **")]
        if len(bullets) != 5:
            problems.append(f"30-second section must contain exactly five bullets: {len(bullets)}")
        for line in bullets:
            content = line.split("：", 1)[-1]
            plain = re.sub(r"[`*_\[\]()]", "", content)
            if len(plain) > 40:
                problems.append(f"30-second bullet exceeds 40 characters: {plain[:45]}")
    if "## 📄 报告文件" not in source:
        problems.append("missing external artifact links section")
    if re.search(r"model:\s*[\"']?(未知|unknown)", source, flags=re.IGNORECASE):
        problems.append("model must not be unknown")
    key_section_name = "## 🔢 关键数据" if "## 🔢 关键数据" in source else "## 📊 论文清单"
    if key_section_name in source:
        key_section = source.split(key_section_name, 1)[1].split("\n## ", 1)[0]
        table_rows = [
            line for line in key_section.splitlines()
            if line.startswith("|") and "|---" not in line and not re.search(r"\|\s*(样品|序号)\s*\|", line)
        ]
        for line in table_rows:
            cells = [cell.strip() for cell in line.strip("|").split("|")]
            metric_cells = cells[1:4] if key_section_name.startswith("## 🔢") else cells[1:2]
            for cell in metric_cells:
                if re.search(r"\d", cell) and "**" not in cell:
                    problems.append(f"key numeric table cell is not bold: {cell}")
    if problems:
        for problem in problems:
            print(f"ERROR: {problem}")
        raise SystemExit(1)
    print("Obsidian Markdown validation passed")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Usage: validate_archive_md.py archived_report.md")
    main(sys.argv[1])
