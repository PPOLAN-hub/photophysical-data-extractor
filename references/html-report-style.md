# HTML report presentation rules

- Treat `paper_data.json` as the only data source and never modify extracted values during rendering.
- Do not display the raw JSON or the rate-constant calculation block in the human-facing HTML. Keep both in the canonical JSON for machine use and audit.
- Render the main extraction as one wide comparison table: one independent sample/condition record per row and one fixed parameter per column. Repeat the compound name when conditions differ; Row ID is the stable record key. Use a horizontally scrollable container and sticky Row ID/Compound columns rather than compound cards.
- Place article-level KOI, one-sentence innovation, and logic skeleton above the data table. Show them once per paper and link every synthesized claim to paper-level evidence.
- Use scientific HTML labels with subscripts: `λ<sub>P</sub>`, `τ<sub>P</sub>`, `Φ<sub>P</sub>`, `k<sub>ISC</sub>`, and analogous fluorescence/delayed-fluorescence labels. Never expose snake_case field names to readers.
- Show reported metrics prominently and keep missing fields out of the visual comparison area. This is a display choice only; do not remove missing statuses from JSON.
- Render evidence as readable cards containing the field label, extracted value, precise location, the shortest useful source-text fragment, extraction type, confidence, and manual-check note.
- Make every evidence citation in the main view link to its Evidence Ledger card.
- Use a clean research-review layout without gradients, animation, decorative illustrations, or external assets.
