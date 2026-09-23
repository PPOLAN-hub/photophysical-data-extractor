---
name: photophysical-data-extractor
description: Extract evidence-traceable photophysical and electronic-structure data, article KOI, innovation, and logical structure from organic-material paper PDFs and their Supporting Information, then produce validated JSON, condition-aligned HTML, Word, and configured Obsidian archive cards. Invoke for one paper whenever the user says "PDE" and for multiple papers whenever the user says "PDEmore". Also use for fluorescence, phosphorescence, RTP, afterglow, delayed fluorescence, TADF, persistent luminescence, PLQY, lifetime, spectra, CPL/CD dissymmetry factors, host-matrix, HOMO, LUMO, S1/T1 energies, singlet-triplet gaps, rate constants, deterministic main-SI pairing, and batch literature organization where every value or synthesized claim must link to source evidence.
---

# Photophysical Data Extractor

Extract evidence, not plausible values. Accept one organic photophysical paper PDF and optional SI, or a deterministically paired batch; write canonical JSON and deterministically render HTML, Word, and Obsidian archive views from it. Cover prompt fluorescence as well as long-lived emission while keeping every mechanism and measurement condition distinct.

Treat `PDE` as the single-paper invocation keyword. A single-paper upload may contain a main PDF plus one SI PDF with arbitrary filenames; treat them as one article set, distinguish main and SI from their document contents, and do not ask the user to rename or pair them. Treat `PDEmore` as the multi-paper invocation keyword and apply the deterministic batch naming rules below. Once local output and archive configuration exists, complete extraction, validation, rendering, preview, and archiving autonomously. Never ask the user to run validator or renderer commands.

## Python runtime

Require Python 3.9 or newer. If the ignored `runtime_config.local.json` exists, try its interpreter candidates first; then resolve the portable candidates from `runtime_config.json` in order, skipping paths or commands that do not exist. Portable candidates cover a Skill-local `.venv`, Windows `py -3`, and macOS/Linux `python3`. Never commit an absolute local path. Never invoke bare `python` on Windows because it may be the Microsoft Store placeholder. Run `scripts/check_environment.py` with the selected interpreter and proceed only when it reports `ready: true`. Do not silently fall back to Python 3.8 or older. If no compatible runtime exists, report the missing runtime instead of asking the user to run the renderer manually.

## Required deliverables

Before any formal extraction, load the confirmed `output_root` from the local configuration and run `scripts/prepare_output_dir.py` to create the task directory. Never write formal deliverables beside uploaded PDFs, in the current working directory, or inside the Obsidian Vault. Put transient `source_index.json` and `bibliography.json` under the task `_work/` subdirectory and expose only validated deliverables:

- `paper_data.json`: source of truth.
- `report.html`: generated only by `scripts/render_html.py`.
- `report.docx`: generated only by `scripts/render_docx.py`.

For a batch, also create `batch_report.json` with a `paper_data_files` list and render one consolidated `batch_report.html` and `batch_report.docx` after every per-paper JSON passes validation.

Run the read-only `scripts/audit_extraction.py paper_data.json`, resolve or record its review candidates, then run `scripts/validate_extraction.py paper_data.json` before rendering. After rendering, run `scripts/validate_report_html.py` and `scripts/validate_report_docx.py`. The audit script may identify weight-sum, cross-source-value, orphan-evidence, or row-reference candidates but must never modify canonical data or decide which conflicting value is correct. Do not hand-edit or independently recreate reports; always use the bundled renderers so display rules remain deterministic.

## Mandatory Obsidian configuration

Before the first formal `PDE` or `PDEmore` extraction, resolve the local config in this order: explicit `--archive-config`, `~/.pde/archive.json`, then `<current-working-directory>/.pde-archive.json`. If none exists, stop before extraction and guide the user through `scripts/configure_archive.py`. The user MUST select a persistent output root outside the Vault, a Vault root, a relative PDE archive directory, and a readable archive-convention file. Validate both locations with actual write/delete probes, display all four selected paths, and save only after explicit confirmation.

Read `references/archive-integration.md` whenever configuring or writing the archive. Every run MUST reread the selected convention file and verify its saved SHA-256. A changed convention requires reconfiguration and a new real-data preview. Run `scripts/archive_report.py ... --preview` without writing the Vault; after the user confirms that first preview, run it with `--yes`. Archive Markdown is a compact index/read card, not a replacement for the complete HTML, DOCX, or JSON. Never hard-code a personal Vault path in tracked files.

Use two deterministic preprocessing scripts before semantic extraction:

- Run `scripts/index_sources.py MAIN.pdf [SI.pdf] source_index.json` once. Read page text and table/figure/scheme anchors from this index during extraction; reopen the PDF only for visual inspection of a figure, equation, or layout ambiguity. Do not repeatedly extract the same PDF text.
- Run `scripts/fetch_bibliography.py --source-index source_index.json bibliography.json`. Copy DOI, authors, journal, year, volume, issue, article number, publisher URL, and citation provenance into `paper`. If `official_citation` is null because the publisher blocked automated access, retain the script's Crossref-based citation as provisional and verify the exact “How to cite” text on the official publisher page before labeling it official.

Read `references/extraction-policy.md` and `references/data-schema.md` before extracting. For more than one paper, read `references/batch-input.md` and build the manifest before opening PDFs. For installation, commands, configuration, and troubleshooting, read `references/usage-guide.md`.

Read `references/portable-agent-contract.md` before every extraction, including non-Codex runtimes. Its MUST/NEVER rules are cross-model execution invariants. They constrain how evidence is handled but must not add, remove, average, or silently choose scientific values.

Use the bundled `report_config.json` as the default main-table physical-column configuration. The renderer loads it automatically. Users may reorder, remove, relabel, or add supported physical fields and may change the physical-header font style. Pass a separate config as the renderer's optional third argument when the default file should remain unchanged. Read `references/html-report-style.md` only when changing presentation rules or renderer behavior; ordinary rendering does not require loading it into model context.

## Workflow

1. Confirm the supplied main PDF and whether SI is supplied. Record coverage; never claim SI was reviewed if unavailable.
2. Build `source_index.json` and `bibliography.json` with the bundled scripts. Use the indexed page text and anchors to locate relevant text, tables, captions, electrochemistry, theoretical-calculation sections, and measurement conditions. Search the keywords in the policy, then inspect every candidate source location; use the original PDF for visual confirmation when text order or graphics matter.
3. Define one record per unique test sample and condition. Do not merge measurements across compound, host/matrix or solvent, concentration, state, atmosphere, temperature, excitation, delay, or gate window. Extract all reported solution/film/crystal/powder and RT/77 K records, not only the headline ambient result.
4. Add field-level evidence before adding a specific value, including compound, host/matrix, concentration, sample state, and every measurement condition. Extract HOMO, LUMO, S1, T1, ΔEST, and CPL/CD dissymmetry factors when reported; separate experimental and calculated energies, distinguish `g_lum` from `g_abs`, and retain method, medium, sign, and measurement wavelength. Use short quotes and a resolvable page/table/figure/SI location.
5. Extract paper-level KOI, a one-sentence innovation, and a problem-to-application logic skeleton. Store these once under `article_analysis`; link every synthesized item to paper-level evidence with `row_id: PAPER`. End the one-sentence innovation with the DOI and the verified citation, or explicitly label a registry-formatted citation as provisional when publisher verification failed.
6. Mark missing information with a status, not a guessed value. Record cross-source conflicts and manual-review items.
7. Validate JSON and render HTML plus Word. In the HTML main table, render one subrow per sample/condition record and vertically merge only the compound label; every value on a horizontal subrow must come from that same JSON record. Keep solution solvent/concentration out of solid formulation cells and identify all conditions through footnotes. Preserve the existing RT/77 K highlighting rules. Validate both formats.
8. Confirm that JSON, HTML, and DOCX all reside below the configured output root. Render an Obsidian Markdown preview from the same JSON, validate it with `scripts/validate_archive_md.py`, then archive it only after the mandatory first-use confirmation. Report the task output directory, final deliverable paths, and archive path, not transient work files.

## Batch workflow

1. Require either `P01.pdf` with `S01.pdf` (recommended) or `1main.pdf` with `1SI.pdf`. Match the complete digit string and naming scheme exactly; never pair by title or upload order. Read `references/batch-input.md`.
2. Run `scripts/build_batch_manifest.py INPUT_DIR batch_manifest.json`; stop on pairing errors.
3. Process each manifest entry independently. Never carry values, evidence IDs, or SI content from one paper into another.
4. Write each result under `<task-dir>/outputs/<paper_id>/`. Keep Row IDs local; use `<paper_id>:<row_id>` as the global row key when consolidating.
5. Build `batch_report.json` from the validated per-paper JSON paths and render `batch_report.html` plus `batch_report.docx`. The HTML renderer namespaces repeated evidence IDs automatically. Create exactly one Obsidian Markdown card for the batch run.

## Evidence rules

- A reported numeric, categorical, or condition value needs an `evidence_id` that exists in `evidence_ledger`.
- Never use `inferred_by_model`. Allowed evidence types are `direct_text`, `table_value`, `figure_estimate`, `calculated_from_reported_values`, and `author_assignment`.
- A `figure_estimate` must say `图中估读` in its note and cannot be high confidence.
- A calculation must state formula, inputs, and input evidence IDs in its evidence note.
- Use `not_reported` only after searching the relevant paper/SI locations. Use `uncertain` where the source is ambiguous or inconsistent.

## Handoff format

Use only the JSON schema fields in the reference. Preserve source units in `raw_value` and `raw_unit`; normalized fields are optional and must include conversion evidence. HTML, Word, and Obsidian Markdown are read-only presentations of the JSON, never additional extraction passes.
