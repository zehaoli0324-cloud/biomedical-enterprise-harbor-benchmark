# Adaptive policy minimax-regret review

Use only the supplied offline JSON files. Evaluate every policy as a complete observation-to-action tree. A policy is eligible only when its scope is active, it has exactly one branch for each observation in `rules.required_observations`, it does not use a future outcome, every action exists, and every realized branch remains within `max_budget`.

For each policy/scenario branch, compute `total_cost = initial_cost + action.cost` and `utility = gain - risk_weight * risk - cost_weight * total_cost`. Among eligible policies, compute the best utility separately for every scenario, then branch regret as `scenario_best - utility`. Rank eligible policies by ascending maximum regret, descending worst utility, descending mean utility, then ascending policy ID. Do not average away a bad branch and do not let an ineligible policy define scenario best.

Write exactly four artifacts under `outputs/`:

- `outputs/policy.json`: object fields `selected_policy`, `rules_version`, `claim_boundary`=`planning_only_not_experimental_proof`, `human_review_required`=true, and `policies`, an object keyed by every policy ID. Each policy contains `eligible`, sorted unique `blockers`, `max_regret`, `worst_utility`, `mean_utility`, and `branches`. `branches` is keyed by scenario ID; each branch contains `observation`, `action`, `total_cost`, `utility`, and `regret`. Ineligible policy summary metrics and regrets are null. Blocker labels are `scope`, `branch_completeness`, `future_outcome_leakage`, `unknown_action`, and `budget`.
- `outputs/branches.tsv`: one row for every policy/scenario pair with columns `policy_id`, `scenario_id`, `observation`, `action`, `total_cost`, `utility`, `regret`, `eligible`, and `blockers`.
- `outputs/manifest.json`: `input_sha256` maps every JSON path relative to `data/` to its SHA-256 hash; also include `rules_version` and `deterministic`=true.
- `outputs/audit.md`: explain minimax regret, budget, future outcome exclusion, branch completeness, human review, and why this is not experimental proof.
