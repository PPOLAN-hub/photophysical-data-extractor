---
name: rtp-paper-extractor
description: Extract evidence-traceable photophysical data from a single pure-organic room-temperature phosphorescence paper PDF and its Supporting Information, then produce validated JSON and an HTML review report. Use for RTP, afterglow, phosphorescence, delayed-emission, PLQY, lifetime, host-matrix, and rate-constant extraction where every reported value must be linked to source evidence.
---

# RTP Paper Extractor

Extract evidence, not plausible values. Accept one paper PDF and optional SI; write a canonical JSON file and render an HTML audit report from it.

## Required deliverables

Create these files beside the input paper:

- `paper_data.json`: source of truth.
- `report.html`: generated only by `scripts/render_html.py`.

Run `scripts/validate_extraction.py paper_data.json` before rendering. Do not hand-edit `report.html`.

Read `references/extraction-policy.md` and `references/data-schema.md` before extracting.

## Workflow

1. Confirm the supplied main PDF and whether SI is supplied. Record coverage; never claim SI was reviewed if unavailable.
2. Read the paper and SI in full enough to locate relevant text, tables, captions, and measurement conditions. Search the keywords in the policy, then inspect every candidate source location.
3. Define one record per unique test sample and condition. Do not merge measurements across compound, host/matrix, concentration, state, atmosphere, temperature, excitation, delay, or gate window.
4. Add field-level evidence before adding a specific value. Use short quotes and a resolvable page/table/figure/SI location.
5. Mark missing information with a status, not a guessed value. Record cross-source conflicts and manual-review items.
6. Validate JSON, render HTML, and report the output paths.

## Evidence rules

- A reported numeric, categorical, or condition value needs an `evidence_id` that exists in `evidence_ledger`.
- Never use `inferred_by_model`. Allowed evidence types are `direct_text`, `table_value`, `figure_estimate`, `calculated_from_reported_values`, and `author_assignment`.
- A `figure_estimate` must say `图中估读` in its note and cannot be high confidence.
- A calculation must state formula, inputs, and input evidence IDs in its evidence note.
- Use `not_reported` only after searching the relevant paper/SI locations. Use `uncertain` where the source is ambiguous or inconsistent.

## Handoff format

Use only the JSON schema fields in the reference. Preserve source units in `raw_value` and `raw_unit`; normalized fields are optional and must include conversion evidence. HTML is a read-only presentation of the JSON, not a second extraction pass.
