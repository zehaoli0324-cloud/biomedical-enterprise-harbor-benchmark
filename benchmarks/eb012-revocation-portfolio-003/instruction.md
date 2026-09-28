# Revocation-aware cross-stage portfolio replay

Use only the three supplied JSON files. Replay events in ascending `sequence` at checkpoints T0, T1, and T2. State persists until a later event changes it. At every checkpoint, a chain is eligible only when its source is active, sensitivity is `stable`, and the requested claim does not exceed the minimum permission across its four stages. A chain is checkpoint-robust only if eligible at all three checkpoints.

Evaluate every two-chain combination. A portfolio is eligible only when both chains are checkpoint-robust and their `lot_id` values differ. Its checkpoint total is the sum of member utilities; its robust score is the minimum of the three checkpoint totals. Select the eligible portfolio with highest robust score, breaking an exact tie by ascending joined chain IDs. Round numeric outputs to six decimals.

Write exactly four artifacts:

- `outputs/decision.json`: object with `rules_version`, `selected_portfolio`, `robust_score`, and `portfolios`. `portfolios` is the complete 15-row combination list in ascending input combination order; each row has `chain_ids`, `eligible`, sorted `blockers`, `checkpoint_totals`, and `robust_score`. Blocker labels may be concise semantic descriptions; eligible rows have no blockers and ineligible rows name every failed gate.
- `outputs/replay.tsv`: exactly 18 rows with header `chain_id`, `checkpoint`, `source_active`, `sensitivity`, `eligible`, `blockers`, `effective_claim`, `utility`, `lot_id`. Use lowercase `true`/`false`; join concise semantic blocker descriptions with semicolons in rule order; use an empty blockers field when none.
- `outputs/audit.md`: explain retraction propagation, checkpoint persistence, shared-lot exclusion, claim boundary, human review, and why this does not constitute experimental proof.
- `outputs/manifest.json`: `input_sha256` mapping the exact filenames `chains.json`, `events.json`, `rules.json` to SHA-256 values, plus `rules_version` and `deterministic=true`.
