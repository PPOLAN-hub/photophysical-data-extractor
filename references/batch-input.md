# Batch input and pairing

Use deterministic names. Never pair a main paper and SI by folder order, upload order, title similarity alone, or PDF metadata alone.

## Preferred flat-folder naming

Use the same paper ID followed by an explicit suffix:

```text
P001_Liu_2024_main.pdf
P001_Liu_2024_SI.pdf
P002_Zhang_2025_main.pdf
P002_Zhang_2025_SI.pdf
```

The exact text before `_main.pdf` or `_SI.pdf` is the pairing key. IDs such as `1.pdf` and `1SI.pdf` are not accepted in strict mode because the role boundary is ambiguous. A simple numeric scheme is acceptable when written as `001_main.pdf` and `001_SI.pdf`.

## Folder-per-paper alternative

Use this when a paper has several supplementary files:

```text
P001_Liu_2024/main.pdf
P001_Liu_2024/SI.pdf
P001_Liu_2024/extra-data.xlsx
```

## Batch workflow

1. Run `scripts/build_batch_manifest.py INPUT_DIR batch_manifest.json`.
2. Stop on duplicate main files, duplicate SI files, an SI without a main paper, or an ambiguous role.
3. Permit a main PDF without SI, but mark `si_status: missing` and never claim SI coverage.
4. Process one manifest entry at a time into `outputs/<paper_id>/paper_data.json` and `report.html`.
5. Keep sample Row IDs local to a paper (`S001`, `S002`, ...). The globally unique row key is `<paper_id>:<row_id>`.
6. In the human-facing consolidated table, create one visual row per `<paper_id>:<compound>` and stack its condition records inside cells. Do not merge the same compound across different papers solely because names match.
7. When consolidating records, retain `paper_id`, DOI, and every global Row ID behind that visual row.

The manifest stores SHA-256 hashes so later runs can detect replacement or accidental cross-pairing.
