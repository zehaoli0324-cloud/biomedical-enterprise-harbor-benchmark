# Donor-stratified perturbation signal under partial identifiability

Use only the supplied offline CSV and JSON. Evaluate every active candidate at the biological donor-by-state level. `method_shadow` is not active and must be excluded.

For each candidate, donor and state, first average all QC-passing technical replicates within each condition. The donor effect is treatment mean minus control mean. A donor is identifiable only when both condition means exist. Never count technical replicates as independent donors and never replace donor-level effects with an observation-row pooled difference.

For each state, report the identifiable donor count, mean donor effect and donor-effect range (`maximum - minimum`). Apply state-specific thresholds from `policy.json`. State status is:

1. `INSUFFICIENT` when the identifiable donor count is below that state's minimum;
2. otherwise `CONTRADICTORY` when any identifiable donor effect is less than or equal to zero;
3. otherwise `WEAK` when the mean effect is below the state's minimum or the range exceeds the state's maximum;
4. otherwise `SUPPORTED`.

Candidate decision precedence is `INSUFFICIENT`, then `CONTRADICTORY`, then `WEAK`, then `SUPPORTED`: use the earliest status present across states. A locally insufficient donor/state cell does not force the state or candidate to `INSUFFICIENT` when the state's donor-count requirement is still met.

Only `SUPPORTED` candidates are eligible for selection. Rank them by descending worst-state mean effect, then ascending maximum state range, then ascending candidate ID. Select rank 1; use `hold_for_human_review` if none is eligible. This is analytical triage, not mechanism, target-engagement or efficacy evidence.

Round reported computed numbers to six decimal places using decimal round-half-up. JSON numeric values and TSV numeric cells are compared numerically, so trailing zeroes are optional. Sets use sorted JSON arrays; row order is not significant.

Write exactly four files under `outputs/`:

- `outputs/candidate_summary.tsv`: columns `candidate_id`, `decision`, `eligible`, `worst_state_mean_effect`, `maximum_state_effect_range`, `rank`. Include every active candidate once. Ineligible summary metrics and rank are blank.
- `outputs/state_diagnostics.tsv`: columns `candidate_id`, `state`, `identifiable_donor_count`, `missing_donors`, `nonpositive_donors`, `mean_effect`, `effect_range`, `status`. Include every active candidate/state pair. `missing_donors` and `nonpositive_donors` are sorted JSON arrays. When no donor is identifiable, numeric cells are blank.
- `outputs/decision.json`: fields `decision`, `selected_candidate`, `rules_version`, `claim_boundary`, and `human_review_required`. `decision` is `proceed_to_profile_review` when a candidate is selected, otherwise `hold_for_human_review`. `human_review_required` is true.
- `outputs/provenance.json`: `input_sha256` maps `observations.csv` and `policy.json` to their SHA-256 values; also include `rules_version`, `network`=`off`, and `deterministic`=true.
