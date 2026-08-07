#!/usr/bin/env python3
"""Build a deterministic main-PDF/SI pairing manifest for batch extraction."""
import hashlib
import json
import re
import sys
from pathlib import Path


PAIR_PATTERNS = (
    ("ps-prefix", re.compile(r"^(?P<role>[ps])(?P<index>\d+)\.pdf$", re.IGNORECASE)),
    ("main-si-suffix", re.compile(r"^(?P<index>\d+)(?P<role>main|si)\.pdf$", re.IGNORECASE)),
)


def digest(path):
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def relative(path, root):
    return path.relative_to(root).as_posix()


def add_role(groups, index, scheme, role, path, problems):
    paper_id = f"P{index}"
    record = groups.setdefault(index, {"_scheme": scheme, "_paper_id": paper_id})
    if record["_scheme"] != scheme:
        problems.append(
            f"{paper_id}: mixed naming schemes are not allowed: "
            f"{record['_scheme']} | {scheme}"
        )
        return
    if role in record:
        problems.append(f"{paper_id}: duplicate {role} PDFs: {record[role]} | {path}")
    else:
        record[role] = path


def build(root):
    groups = {}
    problems = []
    ignored = []
    for path in sorted(root.rglob("*.pdf"), key=lambda item: str(item).lower()):
        for scheme, pattern in PAIR_PATTERNS:
            match = pattern.match(path.name)
            if match:
                index = match.group("index")
                raw_role = match.group("role").lower()
                role = "main" if raw_role in {"p", "main"} else "si"
                add_role(groups, index, scheme, role, path, problems)
                break
        else:
            ignored.append(relative(path, root))

    papers = []
    for index in sorted(groups, key=str.lower):
        record = groups[index]
        paper_id = record["_paper_id"]
        if "main" not in record:
            problems.append(f"{paper_id}: SI exists without main PDF")
            continue
        main_path = record["main"]
        si_path = record.get("si")
        papers.append({
            "paper_id": paper_id,
            "naming_scheme": record["_scheme"],
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
