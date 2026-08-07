#!/usr/bin/env python3
"""Build a deterministic main-PDF/SI pairing manifest for batch extraction."""
import hashlib
import json
import re
import sys
from pathlib import Path


FLAT_PATTERN = re.compile(r"^(?P<key>.+)_(?P<role>main|si)\.pdf$", re.IGNORECASE)


def digest(path):
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def relative(path, root):
    return path.relative_to(root).as_posix()


def add_role(groups, key, role, path, problems):
    record = groups.setdefault(key, {})
    if role in record:
        problems.append(f"{key}: duplicate {role} PDFs: {record[role]} | {path}")
    else:
        record[role] = path


def build(root):
    groups = {}
    problems = []
    ignored = []
    for path in sorted(root.rglob("*.pdf"), key=lambda item: str(item).lower()):
        match = FLAT_PATTERN.match(path.name)
        if match:
            add_role(groups, match.group("key"), match.group("role").lower(), path, problems)
            continue
        if path.name.lower() in {"main.pdf", "si.pdf"} and path.parent != root:
            add_role(groups, path.parent.name, path.stem.lower(), path, problems)
            continue
        ignored.append(relative(path, root))

    papers = []
    for key in sorted(groups, key=str.lower):
        record = groups[key]
        if "main" not in record:
            problems.append(f"{key}: SI exists without main PDF")
            continue
        main_path = record["main"]
        si_path = record.get("si")
        papers.append({
            "paper_id": key,
            "main_pdf": relative(main_path, root),
            "main_sha256": digest(main_path),
            "si_pdf": relative(si_path, root) if si_path else None,
            "si_sha256": digest(si_path) if si_path else None,
            "si_status": "paired" if si_path else "missing",
        })
    return {"schema_version": "1.0", "input_root": str(root.resolve()), "papers": papers, "ignored_pdfs": ignored}, problems


def main(input_text, output_text):
    root = Path(input_text)
    if not root.is_dir():
        raise SystemExit(f"Input directory not found: {root}")
    manifest, problems = build(root)
    if problems:
        raise SystemExit("PAIRING ERROR\n" + "\n".join(problems))
    Path(output_text).write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    missing = sum(item["si_status"] == "missing" for item in manifest["papers"])
    print(f"PAIRED: {len(manifest['papers'])} papers; {missing} missing SI; {len(manifest['ignored_pdfs'])} ignored PDFs")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("Usage: build_batch_manifest.py INPUT_DIR batch_manifest.json")
    main(sys.argv[1], sys.argv[2])
