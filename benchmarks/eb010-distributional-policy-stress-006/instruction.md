# Distributionally robust adaptive-policy stress test

Use only the supplied offline JSON files. First apply hard eligibility gates: active scope, exactly one branch for every required observation, no future-outcome use, known actions, and every realized branch within budget. Ineligible policies cannot define a profile optimum.

For every eligible policy and weight profile, compute expected utility. Compute lower-tail CVaR at `cvar_alpha` by sorting scenario utilities ascending (scenario ID breaks exact utility ties), consuming profile probability mass until alpha, allowing a fractional final scenario, and dividing the accumulated weighted utility by alpha. For each profile, compute the best expected utility and every policy's regret from that best. A policy's robust CVaR is its minimum CVaR across profiles; its maximum profile regret is its largest profile regret.

Select by descending robust CVaR, ascending maximum profile regret, descending nominal expected utility, then ascending policy ID. Recompute the selection after leaving out each one weight profile; this is a stability report, not an eligibility gate.

Round every reported computed numeric value to six decimal places. JSON numeric values and TSV numeric cells are compared numerically, so trailing zeroes are optional.

Write exactly five artifacts under `outputs/`:

- `outputs/policy.json`: `selected_policy`, `rules_version`, `claim_boundary`=`planning_only_not_experimental_proof`, `human_review_required`=true, `profile_best_expected`, `profile_winners`, `leave_one_profile_out_winners`, and `policies` keyed by every policy ID. Each policy contains `eligible`, sorted unique `blockers`, `robust_cvar`, `max_profile_regret`, `nominal_expected_utility`, `branches`, and `profiles`. `branches` is an object keyed by scenario ID; each branch contains `observation`, `site`, `action`, `total_cost`, `utility`. `profiles` is an object keyed by profile name; each eligible profile contains `expected_utility`, `lower_tail_cvar`, `regret`. Ineligible policies use an empty profile object and null summary metrics. Blocker labels: `scope`, `branch_completeness`, `future_outcome_leakage`, `unknown_action`, `budget`.
- `outputs/branches.tsv`: every policy/scenario pair with columns `policy_id`, `scenario_id`, `observation`, `site`, `action`, `total_cost`, `utility`, `eligible`, `blockers`.
- `outputs/profiles.tsv`: every eligible policy/profile pair with columns `policy_id`, `profile`, `expected_utility`, `lower_tail_cvar`, `regret`.
- `outputs/manifest.json`: `input_sha256` maps every JSON path relative to `data/` to SHA-256; include `rules_version`, `deterministic`=true.
- `outputs/audit.md`: explain distribution shift, lower-tail CVaR, profile regret, leave-one-profile-out, future outcome and budget gates, human review, and why this is not experimental proof.
