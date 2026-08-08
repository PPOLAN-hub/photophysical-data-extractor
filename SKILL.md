---
name: photophysical-data-extractor
description: Extract evidence-traceable photophysical data, article KOI, innovation, and logical structure from organic-material paper PDFs and their Supporting Information, then automatically produce validated JSON and HTML review reports. Invoke for one paper whenever the user says "PDE" and for multiple papers whenever the user says "PDEmore". Also use for fluorescence, phosphorescence, RTP, afterglow, delayed fluorescence, TADF, persistent luminescence, PLQY, lifetime, spectra, host-matrix, rate constants, deterministic main-SI pairing, and batch literature organization where every value or synthesized claim must link to source evidence.
---

# Photophysical Data Extractor

Extract evidence, not plausible values. Accept one organic photophysical paper PDF and optional SI, or a deterministically paired batch; write canonical JSON and render HTML audit reports. Cover prompt fluorescence as well as long-lived emission while keeping every mechanism and measurement condition distinct.

Treat `PDE` as the single-paper invocation keyword. A single-paper upload may contain a main PDF plus one SI PDF with arbitrary filenames; treat them as one article set, distinguish main and SI from their document contents, and do not ask the user to rename or pair them. Treat `PDEmore` as the multi-paper invocation keyword and apply the deterministic batch naming rules below. Once invoked, complete extraction, JSON validation, and HTML rendering autonomously. Never ask the user to run validator or renderer commands.

## Python runtime

Require Python 3.9 or newer. Resolve the interpreter from `runtime_config.json` in order, skipping paths or commands that do not exist. This machine is configured to prefer `D:\Tool\Pathon\python.exe`; portable fallbacks cover a Skill-local `.venv`, `py -3`, and `python3`. Never invoke bare `python` on Windows because it may be the Microsoft Store placeholder. Run `scripts/check_environment.py` with the selected interpreter and proceed only when it reports `ready: true`. Do not silently fall back to Python 3.8 or older. If no compatible runtime exists, report the missing runtime instead of asking the user to run the renderer manually.

## Required deliverables

Create these files beside the input paper:

- `paper_data.json`: source of truth.
- `report.html`: generated only by `scripts/render_html.py`.

For a batch, also create `batch_report.json` with a `paper_data_files` list and render one consolidated `batch_report.html` after every per-paper JSON passes validation.

Run `scripts/validate_extraction.py paper_data.json` before rendering and `scripts/validate_report_html.py paper_data.json report.html` after rendering. Do not hand-edit or independently recreate `report.html`; always use the bundled renderer so display rules remain deterministic.

Read `references/extraction-policy.md` and `references/data-schema.md` before extracting. For more than one paper, read `references/batch-input.md` and build the manifest before opening PDFs. For installation, commands, configuration, and troubleshooting, read `references/usage-guide.md`.

Use the bundled `report_config.json` as the default main-table physical-column configuration. The renderer loads it automatically. Users may reorder, remove, relabel, or add supported physical fields and may change the physical-header font style. Pass a separate config as the renderer's optional third argument when the default file should remain unchanged. Read `references/html-report-style.md` only when changing presentation rules or renderer behavior; ordinary rendering does not require loading it into model context.

## Workflow

1. Confirm the supplied main PDF and whether SI is supplied. Record coverage; never claim SI was reviewed if unavailable.
2. Read the paper and SI in full enough to locate relevant text, tables, captions, and measurement conditions. Search the keywords in the policy, then inspect every candidate source location.
3. Define one record per unique test sample and condition. Do not merge measurements across compound, host/matrix or solvent, concentration, state, atmosphere, temperature, excitation, delay, or gate window. Extract all reported solution/film/crystal/powder and RT/77 K records, not only the headline ambient result.
4. Add field-level evidence before adding a specific value, including compound, host/matrix, concentration, sample state, and every measurement condition. Use short quotes and a resolvable page/table/figure/SI location.
5. Extract paper-level KOI, a one-sentence innovation, and a problem-to-application logic skeleton. Store these once under `article_analysis`; link every synthesized item to paper-level evidence with `row_id: PAPER`.
6. Mark missing information with a status, not a guessed value. Record cross-source conflicts and manual-review items.
7. Validate JSON and render HTML. In the main table, show each solid formulation's Host and doping ratio once; keep solution solvent/concentration out of those two cells and identify solution, RT/77 K, and doped-film conditions through metric footnotes. For doped-matrix phosphorescence values, render room-temperature λP, τP, and ΦP in `#D9001B`; render 77 K counterparts in `#0000FF`; bold and underline the longest room-temperature τP and highest room-temperature ΦP, and bold the longest 77 K τP. Treat `RT`, `RT (ambient)`, `room temperature`, `ambient temperature`, `室温`, and 293/298/300 K as room temperature. Run the HTML validator and report the output paths.

## Batch workflow

1. Require either `P01.pdf` with `S01.pdf` (recommended) or `1main.pdf` with `1SI.pdf`. Match the complete digit string and naming scheme exactly; never pair by title or upload order. Read `references/batch-input.md`.
2. Run `scripts/build_batch_manifest.py INPUT_DIR batch_manifest.json`; stop on pairing errors.
3. Process each manifest entry independently. Never carry values, evidence IDs, or SI content from one paper into another.
4. Write each result under `outputs/<paper_id>/`. Keep Row IDs local; use `<paper_id>:<row_id>` as the global row key when consolidating.
5. Build `batch_report.json` from the validated per-paper JSON paths and run `scripts/render_html.py batch_report.json batch_report.html [custom_report_config.json]`. The renderer namespaces repeated evidence IDs automatically.

## Evidence rules

- A reported numeric, categorical, or condition value needs an `evidence_id` that exists in `evidence_ledger`.
- Never use `inferred_by_model`. Allowed evidence types are `direct_text`, `table_value`, `figure_estimate`, `calculated_from_reported_values`, and `author_assignment`.
- A `figure_estimate` must say `图中估读` in its note and cannot be high confidence.
- A calculation must state formula, inputs, and input evidence IDs in its evidence note.
- Use `not_reported` only after searching the relevant paper/SI locations. Use `uncertain` where the source is ambiguous or inconsistent.

## Handoff format

Use only the JSON schema fields in the reference. Preserve source units in `raw_value` and `raw_unit`; normalized fields are optional and must include conversion evidence. HTML is a read-only presentation of the JSON, not a second extraction pass.
