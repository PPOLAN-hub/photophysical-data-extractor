#!/usr/bin/env python3
"""Create a deterministic PDE run directory under the configured output root."""

from __future__ import annotations

import argparse
import json
import re
from datetime import date
from pathlib import Path

from archive_common import load_config


def safe_name(value: str, limit=72) -> str:
    value = re.sub(r'[\\/:*?"<>|]+', "-", str(value or "")).strip(" .-")
    value = re.sub(r"\s+", "-", value)
    return (value[:limit].rstrip(" .-") or "untitled")


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", required=True, choices=("single", "batch"))
    parser.add_argument("--paper-id", default="P1")
    parser.add_argument("--title")
    parser.add_argument("--doi")
    parser.add_argument("--topic", default="PDE-batch")
    parser.add_argument("--date", default=date.today().isoformat())
    parser.add_argument("--archive-config", type=Path)
    return parser.parse_args()


def main():
    args = parse_args()
    _, config = load_config(args.archive_config)
    root = Path(config["output_root"]).expanduser().resolve()
    year = safe_name(args.date[:4], 4)
    if args.mode == "single":
        identity = args.doi or args.paper_id
        folder = f"{safe_name(identity, 36)}_{safe_name(args.title or 'paper', 48)}"
        run_dir = root / year / "PDE" / folder
    else:
        folder = f"{safe_name(args.date, 10)}_{safe_name(args.topic, 56)}"
        run_dir = root / year / "PDEmore" / folder
    work_dir = run_dir / "_work"
    work_dir.mkdir(parents=True, exist_ok=True)
    print(json.dumps({
        "output_root": str(root),
        "run_dir": str(run_dir),
        "work_dir": str(work_dir),
        "deliverables": {
            "json": str(run_dir / ("paper_data.json" if args.mode == "single" else "batch_report.json")),
            "html": str(run_dir / ("report.html" if args.mode == "single" else "batch_report.html")),
            "docx": str(run_dir / ("report.docx" if args.mode == "single" else "batch_report.docx")),
        },
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
