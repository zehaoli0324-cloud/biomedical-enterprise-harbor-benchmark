# Closed-loop policy replay

Use `data/case.json` and `data/rules.json` to evaluate every declared policy. Work only from information available at each stage. For each policy:

1. Sum action cost and compare it with `max_budget`.
2. Require the action stages to equal the declared `stage_order` exactly.
3. Treat `uses_future_outcome=true`, or any other action field containing future outcome information, as leakage.
4. Join all replay rows by `policy_id`; utility is the mean `observed_gain`, utility range is maximum minus minimum, and seed count is the number of distinct `replay_id` values.
5. A policy is stable only when seed count meets `min_seed_count` and utility range is no greater than `max_utility_range`.

A policy is eligible only when it is active, within budget, correctly ordered, leakage-free, and stable. Select the eligible policy with highest utility, breaking ties by lexicographically ascending `policy_id`. If none is eligible, return `request_information`. This is a planning result, not experimental proof, and human review remains required.

Create all of the following artifacts:

- `outputs/policy.json`: object with `selected_policy`, `rules_version`, `claim_boundary` equal to `planning_only_not_experimental_proof`, `human_review_required` equal to `true`, and a `policies` object keyed by every policy ID. Each policy row must contain `cost`, `budget_ok`, `order_ok`, `future_outcome_leakage`, `seed_count`, `utility`, `utility_range`, `stable`, `blocker_reasons`, and `eligible`.
- `outputs/replay.tsv`: tab-separated table containing every input replay exactly once, with columns `replay_id`, `policy_id`, and `observed_gain`.
- `outputs/audit.md`: concise explanation of the stage-order, budget, leakage, seed-stability, stop/continue, and human-review decisions. Do not claim experimental proof.
- `outputs/manifest.json`: object containing `input_sha256` keyed by `case.json` and `rules.json`, `rules_version`, and `deterministic: true`.
