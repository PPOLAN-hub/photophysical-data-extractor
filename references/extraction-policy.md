# Pure-organic long-lived emission extraction policy

## Non-negotiable interpretation boundaries

- Do not equate afterglow-visible time, persistent-luminescence duration, or image-display time with phosphorescence lifetime `tau_p`.
- Do not equate total PLQY / `phi_pl` with phosphorescence quantum yield `phi_p`.
- Do not label delayed emission as phosphorescence/RTP unless the authors explicitly assign it or the supplied evidence supports that assignment. Record the author-assigned mechanism as phosphorescence/RTP, delayed fluorescence, TADF, persistent luminescence, or unresolved long-lived emission.
- Keep fluorescence, delayed fluorescence, TADF, phosphorescence, persistent luminescence, and total PL quantities separate. A paper may contribute more than one mechanism-specific record for the same molecular formulation when sample preparation or measurement conditions differ.
- Record all multi-exponential lifetime components plus the reported average and its definition.
- Preserve source units. A normalized value is optional and must be reproducible from source values.
- Extract every reported photophysical spectrum, peak, yield, and lifetime for each materially different phase and condition, including solution, doped film, neat film, crystal, powder, aggregate, RT, 77 K, air, inert gas, and vacuum. Do not keep only the headline room-temperature film result.
- Treat solution fluorescence at RT and solution phosphorescence at 77 K as separate evidence-bearing records when reported. Record solvent and concentration in `host_matrix` and `doping_ratio`, respectively.

## Evidence location format

Use a stable location such as `Main PDF p. 4, Table 1, row 2`, `SI p. 12, Table S3`, or `Main PDF p. 6, Fig. 3c caption`. For figures, record the visual feature and the estimate method.

## Article-level KOI

- Treat KOI as a retrieval-oriented paper summary: research problem, knowledge gap, design strategy, mechanism, key result, application, and boundaries.
- Base the one-sentence innovation on what is new relative to the paper's stated gap, not on a generic restatement of the abstract.
- Build the logic skeleton as a causal chain such as `problem -> design -> mechanism -> validation -> result -> application`.
- Link every synthesized item to one or more short source quotes. Use `row_id: PAPER`; do not reuse a sample row merely because that sample is the paper's headline material.
- Separate author claims from the extractor's synthesis. Do not strengthen tentative language such as `may`, `suggest`, or `consistent with` into a confirmed mechanism.

## Search terms

Search at minimum: `room-temperature phosphorescence`, `RTP`, `organic phosphorescence`, `afterglow`, `persistent luminescence`, `delayed emission`, `delayed fluorescence`, `TADF`, `long-lived emission`, `lifetime`, `transient`, `time-resolved`, `PLQY`, `quantum yield`, `host`, `matrix`, `doped`, `air`, `nitrogen`, `oxygen`, `vacuum`, `77 K`, `excitation`, `delay`, `gate`, `kISC`, `kRISC`, `kr`, and `knr`.

## Required manual-review items

List SI-only values, figure estimates, source conflicts, ambiguous yield/lifetime definitions, and likely DF/TADF/excimer/aggregate/impurity confounders. Name the five highest-value source locations for a human check when applicable.
