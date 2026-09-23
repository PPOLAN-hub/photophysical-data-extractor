# Portable agent contract

These are execution invariants for every model and agent runtime. They constrain the workflow; they do not authorize invention, automatic conflict resolution, or new scientific fields outside `data-schema.md`.

Before a formal extraction, the runtime MUST resolve a confirmed local configuration containing a persistent output root outside the Vault, a valid Vault root, relative archive directory, and user-selected convention file. It MUST verify write access to both roots, create a task directory below the output root, reread the convention, and verify its saved SHA-256 on every run. Missing or changed configuration blocks formal extraction; the agent must not silently select a path, scatter deliverables, skip archiving, or write personal paths into tracked Skill files.

## Runtime gate

1. MUST run `index_sources.py` before semantic extraction. Do not repeatedly extract PDF text.
2. MUST use `source_index.json` as the text index. Reopen the PDF only for visual inspection of tables, figures, equations, captions, or ambiguous text order.
3. If the runtime cannot execute the required scripts, it MUST state `PDE script runtime unavailable` and MUST NOT claim that the semi-scripted PDE workflow completed.

## Record identity

4. MUST create a separate record for every materially different combination of compound, host or solvent, concentration, sample state, atmosphere, temperature, excitation, delay or gate, mechanism, and experimental versus calculated determination.
5. NEVER merge RT with 77 K, air with vacuum or inert atmosphere, solution with film/crystal/powder, different hosts, different concentrations, or experimental with calculated energies.

## Evidence and missingness

6. EVERY reported value MUST retain `raw_value`, `raw_unit`, `evidence_id`, document role, PDF page, and a resolvable table/figure/text location.
7. NEVER guess or silently complete missing information. Use `not_reported` or `uncertain`.
8. Preserve source units. Normalization or calculations require reproducible evidence and must not replace the raw value.

## Non-equivalence rules

9. NEVER equate afterglow-visible time with phosphorescence lifetime.
10. NEVER equate total PLQY with phosphorescence quantum yield.
11. NEVER copy a lifetime-monitoring wavelength into an emission-peak field.
12. NEVER assign delayed emission to TADF, phosphorescence, or another mechanism without author assignment or mechanism-specific evidence.
13. NEVER mix experimental and calculated energies or calculate `delta_e_st` from unmatched method, medium, phase, geometry, or determination type.
14. NEVER substitute `g_abs` for `g_lum` or the reverse. Preserve the reported sign, wavelength, sample identity, phase or medium, and polarization convention; a reported `|g|` remains an unsigned magnitude.

## Lifetimes and conflicts

15. Preserve every reported multi-exponential component, weight, reported average, and average definition. NEVER replace the longest component with an average or vice versa.
16. Preserve every cross-source conflict. NEVER select, average, overwrite, or “correct” conflicting values unless the source publishes an explicit correction.
17. Audit warnings locate review candidates only. Scripts MUST NOT decide mechanism assignments or resolve scientific conflicts.

## Synthesis and completion

18. Keep author claims separate from extractor synthesis. Preserve tentative language such as `may`, `suggest`, and `consistent with`.
19. Use only fields defined by `data-schema.md`. Do not invent field names to hide unsupported measurements; place relevant unsupported measurements in evidence-backed notes or manual review.
20. Treat canonical JSON as the only scientific source of truth. HTML, DOCX, and Obsidian Markdown MUST be deterministic read-only views of that JSON and MUST pass their bundled validators.
21. In HTML, render one horizontal subrow per JSON sample/condition record. Values from different conditions MUST NOT be independently stacked into visually corresponding positions.
22. Keep transient indexes and bibliography files in the task `_work/` directory. Store validated JSON, HTML, and DOCX only below the configured output root; the Obsidian card is a link-bearing archive view, not the primary file store.
20. MUST run `audit_extraction.py`, resolve or record every warning, and pass `validate_extraction.py` before rendering.
21. MUST NOT claim completion if required scripts failed, validation failed, SI coverage is misstated, or unresolved conflicts were silently discarded.

## Output stability

These constraints are guardrails, not a request to add or remove scientific results. For the same PDFs and schema, a compliant agent should preserve the same values, units, condition splits, mechanism assignments, evidence locations, and conflict list. Wording of KOI synthesis may vary, but it must not strengthen or alter the source claims.
