#!/usr/bin/env python3
"""Create the mandatory PDE output and Obsidian archive configuration."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path

from archive_common import DEFAULT_USER_CONFIG, file_sha256, validate_config, write_json_atomic


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root", required=True, type=Path)
    parser.add_argument("--vault-root", required=True, type=Path)
    parser.add_argument("--archive-dir", required=True)
    parser.add_argument("--convention", required=True, type=Path)
    parser.add_argument("--config", type=Path, default=DEFAULT_USER_CONFIG)
    parser.add_argument(
        "--confirm",
        action="store_true",
        help="Confirm the displayed locations and permit saving the local configuration.",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    vault = args.vault_root.expanduser().resolve()
    output_root = args.output_root.expanduser().resolve()
    output_root.mkdir(parents=True, exist_ok=True)
    convention = args.convention.expanduser().resolve()
    config = {
        "schema_version": 2,
        "output_root": str(output_root),
        "vault_root": str(vault),
        "archive_dir": args.archive_dir,
        "convention_path": str(convention),
        "convention_sha256": file_sha256(convention) if convention.is_file() else "",
        "naming": {
            "batch": "{date}_{topic}",
            "single": "{paper_id}-{title_short}",
            "file": "{name}.md",
        },
        "index": {
            "file": "_索引.md",
            "begin": "<!-- PDE:INDEX:BEGIN -->",
            "end": "<!-- PDE:INDEX:END -->",
        },
        "conflict": {"mode": "version-then-replace", "backup_dir": "_历史"},
        "links": {"style": "file_uri_absolute", "mark_missing": True},
        "configured_at": datetime.now(timezone.utc).isoformat(),
        "preview_confirmed": False,
    }
    validate_config(config, require_write=True)
    print(f"output_root={output_root}")
    print(f"vault_root={vault}")
    print(f"archive_dir={args.archive_dir}")
    print(f"convention={convention}")
    print(f"convention_sha256={config['convention_sha256']}")
    if not args.confirm:
        raise SystemExit("Configuration validated but not saved; rerun with --confirm after user confirmation.")
    output = args.config.expanduser().resolve()
    write_json_atomic(output, config)
    print(f"PDE local configuration saved: {output}")
    print("A real-data --preview is still mandatory before the first archive write.")


if __name__ == "__main__":
    main()
