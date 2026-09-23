# Photophysical data extraction policy

## Non-negotiable interpretation boundaries

- Do not equate afterglow-visible time, persistent-luminescence duration, or image-display time with phosphorescence lifetime `tau_p`.
- Do not equate total PLQY / `phi_pl` with phosphorescence quantum yield `phi_p`.
- Do not label delayed emission as phosphorescence/RTP unless the authors explicitly assign it or the supplied evidence supports that assignment. Record the author-assigned mechanism as phosphorescence/RTP, delayed fluorescence, TADF, persistent luminescence, or unresolved long-lived emission.
- Keep fluorescence, delayed fluorescence, TADF, phosphorescence, persistent luminescence, and total PL quantities separate. A paper may contribute more than one mechanism-specific record for the same molecular formulation when sample preparation or measurement conditions differ.
- Preserve the authors' complete emission assignment in canonical JSON. For the HTML comparison table only, normalize the Type column to `RTP`, `TADF`, `RTP/TADF`, or the fallback `Tranditional-F`; use the fallback only when neither RTP nor TADF is supported.
- Record all multi-exponential lifetime components plus the reported average and its definition.
- Preserve source units. A normalized value is optional and must be reproducible from source values.
- Extract every reported photophysical spectrum, peak, yield, and lifetime for each materially different phase and condition, including solution, doped film, neat film, crystal, powder, aggregate, RT, 77 K, air, inert gas, and vacuum. Do not keep only the headline room-temperature film result.
- Treat solution fluorescence at RT and solution phosphorescence at 77 K as separate evidence-bearing records when reported. Record solvent and concentration in `host_matrix` and `doping_ratio`, respectively.
- Extract HOMO, LUMO, S1, T1, and the S1–T1 energy gap whenever reported. Search both experimental/electrochemical sections and theoretical-calculation tables or figures. Keep experimental and calculated values on separate records and label the determination method, computational level, and medium in `measurement_context`.
- Do not calculate `delta_e_st` from energy values obtained with different methods, media, geometries, or phases. When the paper does not explicitly report the gap, calculate `E(S1) - E(T1)` only from a matched pair, use evidence type `calculated_from_reported_values`, and state the formula plus both input evidence IDs.
- Do not treat an optical gap, oxidation-derived HOMO, calculated orbital energy, or excited-state energy as interchangeable. Preserve the sign of HOMO/LUMO energies and the author's state character such as `1CT`, `1LE`, or `3LE` in `measurement_context` or notes.
- Keep the signed CPL luminescence dissymmetry factor `g_lum` separate from the CD/ECD absorption dissymmetry factor `g_abs`. Never convert one into the other, never discard the sign, and never report a source value written as `|g|` as though its handedness were known.
- A dissymmetry factor is dimensionless, not a percentage. Preserve the author's formula or polarization convention when reported. Record the wavelength of the quoted value or maximum, because a peak `g` value without its spectral position is incomplete context. Keep solution, film, crystal, aggregate, temperature, excitation, and enantiomer/sample identity distinct.

## Evidence location format

Use a stable location such as `Main PDF p. 4, Table 1, row 2`, `SI p. 12, Table S3`, or `Main PDF p. 6, Fig. 3c caption`. For figures, record the visual feature and the estimate method.

Keep the ledger compact. For high-confidence table evidence, put the exact table identifier in `location`, keep `quote` to a table/cell cue instead of repeating the extracted values, and leave `manual_check_note` empty. For other high-confidence evidence, retain only the first 6–10 useful source words in `quote` and leave `manual_check_note` empty. Preserve a complete short clause and an explicit manual-check note only for medium/low confidence, conflicts, figure estimates, ambiguous definitions, or calculations.

## Article-level KOI

- Treat KOI as a retrieval-oriented paper summary: research problem, knowledge gap, design strategy, mechanism, key result, application, and boundaries.
- Base the one-sentence innovation on what is new relative to the paper's stated gap, not on a generic restatement of the abstract.
- Build the logic skeleton as a causal chain such as `problem -> design -> mechanism -> validation -> result -> application`.
- Link every synthesized item to one or more short source quotes. Use `row_id: PAPER`; do not reuse a sample row merely because that sample is the paper's headline material.
- Separate author claims from the extractor's synthesis. Do not strengthen tentative language such as `may`, `suggest`, or `consistent with` into a confirmed mechanism.

## Search terms

Search at minimum: `room-temperature phosphorescence`, `RTP`, `organic phosphorescence`, `afterglow`, `persistent luminescence`, `delayed emission`, `delayed fluorescence`, `TADF`, `long-lived emission`, `lifetime`, `transient`, `time-resolved`, `PLQY`, `quantum yield`, `CPL`, `circularly polarized luminescence`, `CP-EL`, `luminescence dissymmetry`, `dissymmetry factor`, `g_lum`, `glum`, `CD`, `ECD`, `circular dichroism`, `absorption dissymmetry`, `g_abs`, `gabs`, `host`, `matrix`, `doped`, `air`, `nitrogen`, `oxygen`, `vacuum`, `77 K`, `excitation`, `delay`, `gate`, `HOMO`, `LUMO`, `energy level`, `singlet`, `triplet`, `S1`, `T1`, `ΔEST`, `energy gap`, `cyclic voltammetry`, `DFT`, `TD-DFT`, `NTO`, `kISC`, `kRISC`, `kr`, and `knr`.

## Required manual-review items

List SI-only values, figure estimates, source conflicts, ambiguous yield/lifetime definitions, unsigned `|g|` values, dissymmetry factors without a reported wavelength, and likely DF/TADF/excimer/aggregate/impurity confounders. Name the five highest-value source locations for a human check when applicable.
