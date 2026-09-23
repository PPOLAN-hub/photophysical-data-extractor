#!/usr/bin/env python3
"""Resolve a DOI and obtain evidence-bearing bibliographic metadata for PDE."""

import argparse
import html
import json
import re
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

import fitz


DOI_PATTERN = re.compile(r"10\.\d{4,9}/[-._;()/:A-Z0-9]+", re.IGNORECASE)
USER_AGENT = "photophysical-data-extractor/1.0 (bibliographic metadata audit)"
PUBLISHER_STYLE_JOURNALS = {
    "Angewandte Chemie International Edition": "Angew. Chem. Int. Ed.",
    "Angewandte Chemie": "Angew. Chem.",
}


def clean_doi(value: str) -> str:
    value = urllib.parse.unquote(value).strip()
    value = re.sub(r"^https?://(?:dx\.)?doi\.org/", "", value, flags=re.IGNORECASE)
    return value.rstrip(".,;:)]}")


def doi_from_pdf(path: Path) -> str | None:
    document = fitz.open(path)
    text = "\n".join(page.get_text("text") for page in list(document)[:3])
    match = DOI_PATTERN.search(text)
    return clean_doi(match.group(0)) if match else None


def doi_from_index(path: Path) -> str | None:
    payload = json.loads(path.read_text(encoding="utf-8"))
    for document in payload.get("documents", []):
        if document.get("role") != "main":
            continue
        text = "\n".join(page.get("text", "") for page in document.get("pages", [])[:3])
        match = DOI_PATTERN.search(text)
        if match:
            return clean_doi(match.group(0))
    return None


def request_text(url: str, accept: str = "application/json") -> str:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": accept})
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read().decode(response.headers.get_content_charset() or "utf-8", errors="replace")


def crossref_record(doi: str) -> dict:
    url = "https://api.crossref.org/works/" + urllib.parse.quote(doi, safe="")
    payload = json.loads(request_text(url))
    return payload["message"]


def first(value, fallback=None):
    if isinstance(value, list):
        return value[0] if value else fallback
    return value if value not in (None, "") else fallback


def issued_year(record: dict):
    for key in ("published-print", "issued", "published-online", "created"):
        parts = record.get(key, {}).get("date-parts")
        if isinstance(parts, list) and parts and parts[0]:
            return parts[0][0]
    return None


def initials(given: str) -> str:
    tokens = re.findall(r"[A-Za-z]+", given or "")
    return " ".join(token[0].upper() + "." for token in tokens)


def author_text(authors: list[dict]) -> list[str]:
    rendered = []
    for author in authors:
        family = str(author.get("family") or "").strip()
        given = initials(str(author.get("given") or ""))
        rendered.append(" ".join(part for part in (given, family) if part))
    return rendered


def generated_citation(record: dict, doi: str) -> str:
    authors = ", ".join(author_text(record.get("author") or []))
    full_journal = first(record.get("container-title")) or ""
    journal = PUBLISHER_STYLE_JOURNALS.get(full_journal) or first(record.get("short-container-title")) or full_journal
    year = issued_year(record) or ""
    volume = record.get("volume") or ""
    article = record.get("article-number") or record.get("page") or ""
    core = ", ".join(part for part in (authors, str(journal), str(year), str(volume), str(article)) if part)
    return f"{core}. https://doi.org/{doi}"


def visible_text(source: str) -> str:
    source = re.sub(r"<script\b[^>]*>.*?</script>", " ", source, flags=re.IGNORECASE | re.DOTALL)
    source = re.sub(r"<style\b[^>]*>.*?</style>", " ", source, flags=re.IGNORECASE | re.DOTALL)
    source = re.sub(r"<[^>]+>", " ", source)
    return " ".join(html.unescape(source).split())


def publisher_how_to_cite(url: str) -> str | None:
    source = request_text(url, accept="text/html,application/xhtml+xml")
    text = visible_text(source)
    match = re.search(r"How to cite\s*:?\s*(.+?)(?:COPY TEXT|Download Citation|Citation manager)", text, re.IGNORECASE)
    if not match:
        return None
    citation = match.group(1).strip(" -")
    return citation if 25 <= len(citation) <= 1200 else None


def build_payload(doi: str) -> dict:
    record = crossref_record(doi)
    publisher_url = (
        record.get("resource", {}).get("primary", {}).get("URL")
        or record.get("URL")
        or f"https://doi.org/{doi}"
    )
    official_citation = None
    citation_source = None
    publisher_error = None
    try:
        official_citation = publisher_how_to_cite(publisher_url)
        if official_citation:
            citation_source = publisher_url
    except (OSError, urllib.error.URLError, ValueError) as exc:
        publisher_error = str(exc)
    citation = official_citation or generated_citation(record, doi)
    if citation_source is None:
        citation_source = "Crossref metadata; citation formatted deterministically"
    return {
        "doi": doi,
        "title": first(record.get("title")),
        "authors": author_text(record.get("author") or []),
        "journal": first(record.get("container-title")),
        "journal_abbreviation": first(record.get("short-container-title")),
        "year": issued_year(record),
        "volume": record.get("volume"),
        "issue": record.get("issue"),
        "article_number": record.get("article-number") or record.get("page"),
        "publisher": record.get("publisher"),
        "publisher_url": publisher_url,
        "official_citation": official_citation,
        "publisher_style_citation": generated_citation(record, doi),
        "citation": citation,
        "citation_source": citation_source,
        "registry_source": f"https://api.crossref.org/works/{doi}",
        "publisher_fetch_error": publisher_error,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--doi")
    source.add_argument("--pdf", type=Path)
    source.add_argument("--source-index", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    if args.doi:
        doi = clean_doi(args.doi)
    elif args.source_index:
        doi = doi_from_index(args.source_index)
    else:
        doi = doi_from_pdf(args.pdf)
    if not doi:
        raise SystemExit("No DOI found")
    payload = build_payload(doi)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"output": str(args.output.resolve()), "doi": doi, "official_citation": bool(payload["official_citation"])}, ensure_ascii=False))


if __name__ == "__main__":
    main()
