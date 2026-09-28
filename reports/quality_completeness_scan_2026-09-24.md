# Quality Completeness Scan

Assessment date: 2026-09-24

## Archive assessment

`dist/selected-four-v3-calibrated-20260924.tar.gz` is internally consistent:

- SHA-256 matches the supplied sidecar: `42ce1999e906c0fd665db66db8cc84f0914d31cdb628cfcca5c77ed0eddf93ad`.
- It contains four existing task IDs, not one new task: `eb006-research-completion-011`, `eb013-cross-context-evidence-portfolio-005`, `eb014-sequential-evidence-feedback-002`, and `eb015-real-source-replacement-gate-001`.
- The package reports 208 payload files, enterprise SOP preflight PASS, `51 passed, 3 skipped`, and dynamic checks PASS.
- It remains an internal calibrated batch. Formal release is blocked.

The four snapshots are high-quality author-side packages: they have executable verifiers, reference solutions, controls, quality cards, trial evidence, and deterministic manifests. They are not release-ready because the manifest still requires fixed-container replay and human/reality gates; EB015 additionally requires source-rights, file-hash, and verifier-rebind work.

## Extension added to the optimization queue

The four calibration-ready tasks below are now appended to the queue as priorities 11-14. They are included for optimization, but remain explicitly pre-trial:

- `eb013-evidence-budget-routing-001`
- `eb013-evidence-budget-routing-002`
- `eb010-closed-loop-ambiguity-004`
- `eb010-distributional-policy-stress-006`

Their target trials can be run in a separate window. This repository-side workflow should update evidence-surface cards, data sufficiency, mutation coverage, and replay contracts without changing their `NOT_RUN`/recalibration status prematurely.

## Are there more complete tasks outside the extended queue?

No remaining task is more complete end-to-end than the ten-task queue: the strongest outside candidates either have not run a current target trial or have thinner release evidence.

The following four have especially complete authoring and preflight paperwork, but are **not** ready to replace the queue because their target trial is absent or stale:

| Task | Why it looks complete | Missing before it can join the fast-close queue |
| --- | --- | --- |
| `eb013-evidence-budget-routing-001` | contract audit PASS, independent verifier PASS, SOP preflight PASS | current target trial and evidence-surface trial |
| `eb013-evidence-budget-routing-002` | contract audit PASS, independent verifier PASS, SOP preflight PASS | current target trial and evidence-surface trial |
| `eb010-closed-loop-ambiguity-004` | contract audit PASS, independent verifier PASS, SOP preflight PASS | recalibration after data expansion and target trial |
| `eb010-distributional-policy-stress-006` | contract audit PASS, independent verifier PASS, SOP preflight PASS | evidence-surface trial and target trial |

The next group with a completed target pass but thinner quality-card coverage is `eb003-recovery-chain-005`, `eb005-normalization-hierarchy-003`, `eb008-route-portfolio-002`, `eb009-diversity-coverage-004`, `eb010-next-batch-002`, `eb011-measurement-request-005`, and `eb012-cross-handoff-audit-001`. They are good candidates for a later quality-card consolidation pass, but are not more complete than the current ten.
