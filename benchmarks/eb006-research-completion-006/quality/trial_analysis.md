# EB006 Research Completion Trial Analysis

## Result

- Target: `gpt-5.6-sol`.
- Primary evidence trial: `eb006-research-completion-gpt56sol-002`.
- Runner result: adapter exit 124; classification `TIMEOUT_INFRASTRUCTURE_OUTPUT_VERIFIED`.
- Difficulty evidence: invalid. An adapter/SSE lifecycle timeout is not a scientific failure.
- Release: blocked pending adapter lifecycle repair, fixed-container replay, and human review.

The model wrote all four required artifacts during its first submission attempt. Its executable analysis covered 24 donor-state unit effects, 30 base/LODO scenario checks, six pooled diagnostics, three candidate summaries, and the final reconciliation. It independently replayed the program and checked contract coverage before the model stream disconnected.

## Scientific Replay

The unchanged frozen workspace passed the public completion checker after timeout, including two clean replays and one reversed-row replay. It also passed the independent scientific verifier and the verifier's altered-measurement replay.

| Decision | Observed | Oracle |
| --- | --- | --- |
| Nominal donor-balanced | `C43` | `C43` |
| Observation-row pooled diagnostic | `C28` | `C28` |
| LODO-robust final selection | `C17` | `C17` |

The audit preserved the analytical-triage claim ceiling and human-review requirement. The output therefore shows that this instance did not defeat the model scientifically. Because the turn did not terminate normally, it is not a valid raw pass either.

## Infrastructure Findings

The first run was invalidated by a concurrent source-contract update while the trial workspace remained frozen. The second run used stable agent-visible inputs, but the model stream emitted reconnect errors and the adapter consumed its 840-second budget before normal turn completion. At that time the research gate skipped completion checking whenever the child exit code was nonzero.

The gate now checks and archives already-written artifacts even after exit 124, producing `timeout_output_complete` when public completion replay passes. It still returns 124, so artifact recovery cannot convert infrastructure timeout into a formal pass. A regression test fixes this behavior.

## Difficulty Conclusion

The L8 contract is materially harder than EB006-005: it requires a reusable executable estimator, a competing estimand, every registered influence scenario, and explicit resolution of three different winners. Controls reject nominal-only, pooled-only, missing-sensitivity, duplicate-record, constant-output, and always-hold shortcuts. Contract compilation scores the task 4.52 raw and 5.0 adjusted (`frontier`).

Those design properties establish task complexity, not target-model failure. A fixed-container trial with stable frozen sources and repaired stream lifecycle is still required before using target success or failure as difficulty evidence.
