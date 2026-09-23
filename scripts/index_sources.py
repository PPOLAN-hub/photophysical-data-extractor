#!/usr/bin/env python3
"""Extract PDF text once and build stable page/table/figure anchors for PDE."""

import argparse
import hashlib
import json
import re
from pathlib import Path

import fitz


ANCHOR_PATTERN = re.compile(
    r"\b(?P<kind>Table|Figure|Fig\.|Scheme)\s+(?P<label>S?\d+[A-Za-z]?)\b",
    re.IGNORECASE,
)

SEARCH_ALIASES = {
    "room_temperature": ("RT", "room temperature", "ambient temperature", "293 K", "298 K", "300 K", "室温"),
    "cryogenic_77k": ("77 K", "77K"),
    "ambient_or_air": ("air", "ambient conditions", "under ambient"),
    "inert": ("N2", "nitrogen", "argon", "deaerated", "degassed"),
    "vacuum": ("vacuum",),
    "toluene": ("toluene", "Tol"),
    "pmma": ("PMMA", "poly(methyl methacrylate)"),
}


def compact(text: str) -> str:
    return " ".join(text.replace("\u00ad", "").replace("\x00", "").split())


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def classify_document(first_pages: str) -> str:
    text = first_pages.casefold()
    supporting_markers = (
        "supporting information",
        "supplementary information",
        "electronic supplementary information",
    )
    if any(marker in text for marker in supporting_markers):
        return "supporting_information"
    return "main"


def anchor_context(text: str, start: int, end: int, radius: int = 150) -> str:
    left = max(0, start - radius)
    right = min(len(text), end + radius)
    return compact(text[left:right])


def search_hits(text: str) -> dict[str, list[str]]:
    folded = text.casefold()
    return {
        canonical: [alias for alias in aliases if alias.casefold() in folded]
        for canonical, aliases in SEARCH_ALIASES.items()
        if any(alias.casefold() in folded for alias in aliases)
    }


def index_pdf(path: Path) -> dict:
    document = fitz.open(path)
    pages = []
    anchors = []
    leading_text = []
    for page_index, page in enumerate(document):
        text = page.get_text("text")
        if page_index < 2:
            leading_text.append(text)
        page_number = page_index + 1
        page_anchors = []
        for match in ANCHOR_PATTERN.finditer(text):
            kind = match.group("kind").lower().replace("fig.", "figure")
            anchor = {
                "kind": kind,
                "label": match.group("label"),
                "pdf_page": page_number,
                "location": f"PDF p. {page_number}, {match.group(0)}",
                "context": anchor_context(text, match.start(), match.end()),
            }
            page_anchors.append(anchor)
            anchors.append(anchor)
        pages.append(
            {
                "pdf_page": page_number,
                "text": text,
                "text_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
                "anchors": page_anchors,
                "search_alias_hits": search_hits(text),
            }
        )
    return {
        "path": str(path.resolve()),
        "filename": path.name,
        "sha256": digest(path),
        "page_count": len(document),
        "role": classify_document("\n".join(leading_text)),
        "pdf_metadata": document.metadata,
        "anchors": anchors,
        "pages": pages,
    }


def build_index(paths: list[Path]) -> dict:
    documents = [index_pdf(path) for path in paths]
    roles = [item["role"] for item in documents]
    if roles.count("main") > 1 or roles.count("supporting_information") > 1:
        raise ValueError(f"Expected at most one main PDF and one SI PDF; detected roles: {roles}")
    return {
        "schema_version": "1.0",
        "documents": documents,
        "coverage": {
            "main_pdf_present": "main" in roles,
            "supporting_information_present": "supporting_information" in roles,
            "total_pages": sum(item["page_count"] for item in documents),
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("pdf", nargs="+", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    for path in args.pdf:
        if not path.is_file():
            raise SystemExit(f"PDF not found: {path}")
    payload = build_index(args.pdf)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    counts = {item["role"]: item["page_count"] for item in payload["documents"]}
    anchor_count = sum(len(item["anchors"]) for item in payload["documents"])
    print(json.dumps({"output": str(args.output.resolve()), "pages": counts, "anchors": anchor_count}, ensure_ascii=False))


if __name__ == "__main__":
    main()
