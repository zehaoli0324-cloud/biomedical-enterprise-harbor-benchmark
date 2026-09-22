# EB010 Closed-Loop Replay Trial Analysis

## Scope

- Model: `gpt-5.6-sol`
- Trial: `trial-gpt56-sol-001`
- Backend: local process runner, `process_cwd_only`
- Agent exit: `0`
- Timeout: `false`
- Scientific decision: `policy_safe`
- Contract replay: `PASS_AFTER_CONTRACT_REPLAY`
- Artifact changed after the first run: `false`

## Model Behavior

The model inspected both visible JSON inputs, derived all three policy rows, and selected `policy_safe`. It correctly recognized that `policy_peek` has the highest nominal utility but is invalid because it uses a future outcome, and that `policy_overrun` is invalid because cost `8.0` exceeds the budget `7.0`. It produced all four required artifacts, covered all six replay records, preserved both input hashes, and declared the planning-only claim boundary and human review requirement.

The transcript shows one failed self-check caused by a malformed shell `awk` command. The model recovered and completed later JSON, replay coverage, and hash checks. This is a minor delivery-process observation, not a scientific reasoning failure.

## Failure Attribution

The first host-side verifier run returned `verifier_fail` with two errors:

1. The model used the semantically valid blocker label `cost_exceeds_max_budget`; the verifier expected only `budget`.
2. The model emitted numeric values such as `1.10`; the verifier compared replay values as strings and rejected equivalent numeric formatting.

These are verifier contract defects. The model exited normally, chose the correct policy, and produced complete artifacts. After the verifier accepted blocker aliases and numeric tolerance, the unchanged artifacts passed replay with zero errors. The result must therefore be recorded as a contract-replay pass, not as a model failure.

## Baseline Separation

| Strategy | Result | Attribution |
| --- | --- | --- |
| `reference_solution` | pass | verifier and fixture are executable |
| `simple_legal_baseline` | fail | wrong policy selection |
| `always_abstain` | fail | incomplete delivery |
| `template_or_keyword` | fail | incomplete policy coverage and derived fields |
| `target_model` | pass after contract replay | correct scientific decision; initial verifier schema defect |

The baseline matrix rejects both forced abstention and superficial/template behavior. It does not establish comparative model difficulty by itself.

## Evidence Boundary

This is one successful local process trial. It supports that the current task is solvable and that this run exercised temporal ordering, leakage detection, budget gating, replay aggregation, and bounded claim language. It does not establish repeatability, target-model discrimination, practitioner validity, or Harbor readiness. Fixed-container replay, repeated trials, trajectory analysis, and practitioner review remain open.

## Recommended Follow-up

Run at least three additional trials with identical inputs, then add metamorphic variants for policy/replay row order, numeric formatting, near-budget cost, and utility range at the stability boundary. Keep model success separate from contract compatibility, and only update the L5 difficulty claim after fixed-container replay and independent domain review.
