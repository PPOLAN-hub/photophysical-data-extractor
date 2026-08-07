---
name: rtp-paper-extractor
description: Extract evidence-traceable photophysical data, article KOI, innovation, and logical structure from one or a batch of pure-organic long-lived-emission paper PDFs and their Supporting Information, then produce validated JSON and HTML review reports. Use for RTP, phosphorescence, afterglow, delayed fluorescence, TADF, persistent luminescence, PLQY, lifetime, host-matrix, rate constants, main/SI pairing, and batch literature organization where every value or synthesized claim must link to source evidence.
---

# Pure-Organic Long-Lived Emission Extractor

Extract evidence, not plausible values. Accept one paper PDF and optional SI, or a deterministically paired batch; write canonical JSON and render HTML audit reports.

## Required deliverables

Create these files beside the input paper:

- `paper_data.json`: source of truth.
- `report.html`: generated only by `scripts/render_html.py`.

Run `scripts/validate_extraction.py paper_data.json` before rendering. Do not hand-edit `report.html`.

Read `references/extraction-policy.md` and `references/data-schema.md` before extracting. Read `references/html-report-style.md` before rendering the HTML report. For more than one paper, read `references/batch-input.md` and build the manifest before opening PDFs.

## Workflow

1. Confirm the supplied main PDF and whether SI is supplied. Record coverage; never claim SI was reviewed if unavailable.
2. Read the paper and SI in full enough to locate relevant text, tables, captions, and measurement conditions. Search the keywords in the policy, then inspect every candidate source location.
3. Define one record per unique test sample and condition. Do not merge measurements across compound, host/matrix, concentration, state, atmosphere, temperature, excitation, delay, or gate window.
4. Add field-level evidence before adding a specific value, including compound, host/matrix, concentration, sample state, and every measurement condition. Use short quotes and a resolvable page/table/figure/SI location.
5. Extract paper-level KOI, a one-sentence innovation, and a problem-to-application logic skeleton. Store these once under `article_analysis`; link every synthesized item to paper-level evidence with `row_id: PAPER`.
6. Mark missing information with a status, not a guessed value. Record cross-source conflicts and manual-review items.
7. Validate JSON, render HTML, and report the output paths.

## Batch workflow

1. Require `_main.pdf` and `_SI.pdf` suffixes sharing the exact same paper ID, or the folder-per-paper form in `references/batch-input.md`.
2. Run `scripts/build_batch_manifest.py INPUT_DIR batch_manifest.json`; stop on pairing errors.
3. Process each manifest entry independently. Never carry values, evidence IDs, or SI content from one paper into another.
4. Write each result under `outputs/<paper_id>/`. Keep Row IDs local; use `<paper_id>:<row_id>` as the global row key when consolidating.

## Evidence rules

- A reported numeric, categorical, or condition value needs an `evidence_id` that exists in `evidence_ledger`.
- Never use `inferred_by_model`. Allowed evidence types are `direct_text`, `table_value`, `figure_estimate`, `calculated_from_reported_values`, and `author_assignment`.
- A `figure_estimate` must say `图中估读` in its note and cannot be high confidence.
- A calculation must state formula, inputs, and input evidence IDs in its evidence note.
- Use `not_reported` only after searching the relevant paper/SI locations. Use `uncertain` where the source is ambiguous or inconsistent.

## Handoff format

Use only the JSON schema fields in the reference. Preserve source units in `raw_value` and `raw_unit`; normalized fields are optional and must include conversion evidence. HTML is a read-only presentation of the JSON, not a second extraction pass.
