# Batch input and pairing

Use deterministic names. Never pair a main paper and SI by folder order, upload order, title similarity alone, or PDF metadata alone.

## Required flat-folder naming

Use either of these two naming schemes. The `P/S` prefix scheme is recommended because the roles are immediately visible and zero padding keeps file sorting stable:

```text
# Recommended
P01.pdf  <->  S01.pdf
P02.pdf  <->  S02.pdf
P03.pdf  <->  S03.pdf

# Compatible alternative
1main.pdf  <->  1SI.pdf
2main.pdf  <->  2SI.pdf
```

The digits are the pairing key and must match exactly, including zero padding. For example, `P01.pdf` does not pair with `S1.pdf`. Both files in a pair must use the same naming scheme. Do not use titles, upload order, PDF metadata, or folder names as pairing rules.

## Batch workflow

1. Run `scripts/prepare_output_dir.py --mode batch --topic <topic>` and place the manifest under the returned task `_work/` directory; then run `scripts/build_batch_manifest.py INPUT_DIR <work-dir>/batch_manifest.json`.
2. Stop on duplicate main files, duplicate SI files, an SI without a main paper, or an ambiguous role.
3. Permit a main PDF without SI, but mark `si_status: missing` and never claim SI coverage.
4. Process one manifest entry at a time into `<task-dir>/outputs/<paper_id>/paper_data.json`, `report.html`, and `report.docx`.
5. Keep sample Row IDs local to a paper (`S001`, `S002`, ...). The globally unique row key is `<paper_id>:<row_id>`.
6. In the human-facing consolidated table, create one condition subrow per JSON sample record and namespace it by paper. Vertically merge only the compound label within that paper. Do not merge the same compound across different papers solely because names match.
7. When consolidating records, retain `paper_id`, DOI, and every global Row ID behind that visual row.

## Consolidated HTML

After validating every per-paper JSON, create an index beside the batch outputs:

```json
{
  "paper_data_files": [
    "outputs/P01/paper_data.json",
    "outputs/P02/paper_data.json"
  ]
}
```

The Agent renders `batch_report.html` automatically. The renderer also accepts a JSON array of canonical paper objects or `{"papers": [...]}`. In a consolidated report, keep each article-information table open and keep that article's combined main-data/evidence-review region closed by default. Evidence anchors are automatically namespaced by paper and cannot collide across articles.

The manifest stores SHA-256 hashes so later runs can detect replacement or accidental cross-pairing.
