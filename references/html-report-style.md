# HTML report presentation rules

- Treat `paper_data.json` as the only data source and never modify extracted values during rendering.
- Do not display the raw JSON or the rate-constant calculation block in the human-facing HTML. Keep both in the canonical JSON for machine use and audit.
- Keep one independent sample/condition record per JSON object, but render one visual table row per compound within a paper. In the main comparison table, prefer the ambient/RT record for fields reported under several temperatures; use the TADF record only for delayed-fluorescence fields. Keep secondary 77 K and special-condition values in JSON and the Evidence Ledger instead of stacking them into the main cells.
- Use compact columns comparable to a literature spreadsheet: Compound, Host, Type, yields, wavelengths, lifetimes, and reported rate constants. Omit Row ID, doping, sample-state prose, and condition prose from the main comparison surface.
- Abbreviate common mechanisms and matrices in the main table: `RTP`, `TADF`, `DF`, `F/RTP`, `PMMA`, `PVA`, and `PMMA/PVA`. Preserve the full source wording in JSON and evidence.
- Keep main cells compact: show a reported average lifetime when available, otherwise a reported longest component, otherwise the component range. Compress semicolon-separated wavelength series to a range. Preserve every component and wavelength in JSON and the Evidence Ledger; never overwrite source data with the display summary.
- Render the logic skeleton and core argument as full-width rows before the compound rows, and the one-sentence innovation as a full-width row after them. Link synthesized claims to paper-level evidence.
- Use scientific HTML labels with subscripts: `λ<sub>P</sub>`, `τ<sub>P</sub>`, `Φ<sub>P</sub>`, `k<sub>ISC</sub>`, and analogous fluorescence/delayed-fluorescence labels. Never expose snake_case field names to readers.
- Show reported metrics prominently and keep missing fields out of the visual comparison area. This is a display choice only; do not remove missing statuses from JSON.
- Render evidence as readable cards containing the field label, extracted value, precise location, the shortest useful source-text fragment, extraction type, confidence, and manual-check note.
- Make every evidence citation in the main view link to its Evidence Ledger card.
- Use a clean research-review layout without gradients, animation, decorative illustrations, or external assets.
