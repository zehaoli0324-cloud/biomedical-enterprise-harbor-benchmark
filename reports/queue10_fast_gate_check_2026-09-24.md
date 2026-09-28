# Queue-10 Fast Gate Check

Date: 2026-09-24

This is the rapid B-line check. It does not change release status or claim formal completion.

## Immediate replay candidates

These eight tasks have runnable local tests passing and can move directly to fixed-container/replay work:

| Task | Focused test result | Next action |
| --- | --- | --- |
| `eb013-cross-context-evidence-portfolio-005` | 17 passed | fixed-container replay |
| `eb014-sequential-evidence-feedback-002` | 3 passed, 1 skipped | fixed-container replay; retain skip note |
| `eb010-adaptive-policy-regret-005` | 5 passed | fixed-container replay |
| `eb010-closed-loop-replay-003` | 2 passed | fixed-container replay |
| `eb013-partial-observation-risk-004` | 24 passed | fixed-container replay |
| `eb013-shared-setup-routing-003` | 18 passed | fixed-container replay |
| `eb006-donor-stratified-signal-005` | 3 passed | fixed-container replay |
| `eb006-research-completion-008` | 3 passed | fixed-container replay |

All eight also passed the independent enterprise SOP structural recheck on 2026-09-24. The recheck confirms package structure and release blockers; it is not a substitute for the fixed-container run.

## Test-entry blockers

- `eb015-real-source-replacement-gate-001`: pytest collected only one skipped test; exit code 5. It needs a runnable local verifier test or an explicit container-only test record before replay is considered covered.
- `eb006-research-completion-011`: pytest collected only one skipped test; exit code 5. It needs the same test-entry repair, plus a clean target rerun because the current evidence is timeout/output-complete.

## Ten-minute decision

Do not spend this window on new data expansion for the eight passing tasks. The highest-value next action is fixed-container replay and durable hash capture. Handle the two skipped-only tasks separately so they do not weaken the queue's evidence quality.
