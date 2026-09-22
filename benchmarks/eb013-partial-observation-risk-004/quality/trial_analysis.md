# GPT-5.6-sol Trial: Partial-Observation Risk

## Result

- Task: `eb013-partial-observation-risk-004`, frozen version 1.0.0.
- Trial: `partial-risk-gpt56sol-001`, model `gpt-5.6-sol`.
- Raw result: PASS; agent exit code 0; normal `turn.completed` event recorded.
- Unchanged-artifact replay: PASS, no verifier errors and no output repair.
- Wall time: approximately 739 seconds (12 minutes 19 seconds), including agent
  execution and runner verification. The run was not stopped on artifact creation.
- All nine frozen package files, five agent-visible input hashes and five final
  output hashes matched before archive/replay.

This is one pass in one valid local trial. The escalation did NOT defeat the
model. It does not establish a population pass rate or held-out generalization.

## What Was Solved

The model selected P2 and the observation policy a=B, b=A, c=B, d=C. It reported
setup cost 1.5, worst total cost 3.5, robust CVaR 0.215 and worst-model mean loss
0.1565, matching both exact author-side oracles. It supplied the best feasible
policy for every probe, all six world rows, every probability model's risk values,
and the evidence-revision audit. The two aliased worlds W2 and W3 both use A.

The model correctly resolved B revision 2, excluded E after its withdrawal, and
excluded future-only F. It retained the human-review and synthetic-planning claim
boundary and recorded all four data hashes. No field aliases, missing values,
semantic defaults or repaired scientific outputs were needed to obtain PASS.

| Probability model | Mean loss | CVaR |
| --- | --- | --- |
| nominal | 0.1565 | 0.215 |
| shift | 0.1475 | 0.1975 |
| rare | 0.156 | 0.205 |

## Process Errors and Attribution

An intermediate enumeration/self-check script used a dictionary key where a
numeric cost was intended, producing a type error during a later check. The
model corrected its calculation and re-enumerated the alternatives. Some git
inspection commands also failed because the isolated working directory is not a
repository. Neither issue invalidated the final artifacts. They are retained in
the event log, but are not counted as scientific failures or verifier failures.

The output contract and verifier were frozen before launch and did not change
during execution. The complete-turn adapter waited for normal exit. This avoids
the false-failure mechanism observed in the prior artifact-existence diagnostic.

## Difficulty Interpretation

Twenty pre-trial controls and the independent oracle checks demonstrate that the
added mechanisms affect decisions: world revelation, nominal-only optimization,
withdrawal removal and commitment contraction all change the selected strategy.
However, explicit finite inputs and 346 legal observation policies remain readily
enumerable with code. This run shows the model can compose those mechanisms when
their semantics and output contract are clear; longer runtime alone is not proof
of scientific difficulty or improved discrimination.

Do not silently tighten the verifier after this pass. A future version could
introduce multi-step observation histories, stage-specific information sets and
shared resources across multiple simultaneous cases. Such additions need their
own tractable oracle, single-factor controls and frozen target trials, rather than
more schema fields or artificially shortened execution time.

## Evidence and Release Boundaries

Raw outputs, manifest, event log, verifier result, adapter source snapshots and
replay record are in `quality/trials/partial-risk-gpt56sol-001/`.
`quality/target_trial_evidence.json` records hashes and the RAW_PASS classification.

Execution used local process working-directory isolation, not an enforced
container or network boundary. The independent mathematical audit was automated;
human scientific review, fixed-container replay and held-out target trials remain
NOT_RUN. Task-specific release blockers remain in `quality/sop_card.json`.
Structural preflight PASS is not release approval, and its generic report does
not enumerate all task-specific review requirements.
