# Data schema

`paper_data.json` contains one object with `paper`, `samples`, `evidence_ledger`, `manual_review`, and `rate_calculations` keys.

Each sample has `row_id`, an `identity` object, a `conditions` object, a `fields` object, and `notes`. Identity includes compound, host_matrix, doping_ratio, and sample_state. Conditions include atmosphere, temperature, excitation, delay, and gate_window. Every value in all three objects uses the field shape below, so identity and conditions are evidence-bearing too. Create a separate record when sample preparation or the mechanism-specific measurement conditions differ materially.

Every entry in `identity`, `conditions`, and `fields` uses this shape:

```json
{"status":"reported","raw_value":"487","raw_unit":"nm","evidence_id":"E012","measurement_context":{"excitation":"355 nm","temperature":"RT"}}
```

`measurement_context` is optional and records conditions specific to one field when they differ from the sample-level conditions. Use `status: not_reported` or `status: uncertain` with `raw_value: null` when appropriate. Field names include `emission_assignment`, `afterglow_color`, `afterglow_visible_time`, `phi_pl`, `lambda_f`, `tau_f`, `phi_f`, `lambda_df`, `tau_df`, `phi_df`, `lambda_p`, `tau_p`, `phi_p`, `k_isc`, `k_risc`, `k_rp`, and `knr_p`.

Each evidence entry has `evidence_id`, `row_id`, `field_name`, `extracted_value`, `location`, `quote`, `type`, `confidence`, and `manual_check_note`. Confidence is `high`, `medium`, or `low`.
