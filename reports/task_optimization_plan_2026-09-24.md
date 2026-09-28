# Task optimization plan (2026-09-24)

## Scope freeze

- **Official repository scope: 32 tasks.** These are the task packages returned by `git ls-files 'benchmarks/*/task.yaml'` at `HEAD`.
- **Working-tree candidate scope: 14 additional tasks.** They exist under `benchmarks/` but are not tracked in Git. They remain staging/candidate tasks and are not counted in the official benchmark until explicitly promoted.
- The previous count of 46 was a working-tree count, not the repository release count.

## Cross-repository lineage gate

The local cross-repository audit compares the 32 tracked packages with 261 task
packages found in three related repositories. It found six normalized-ID lineage
combinations, of which four require direct review:

- `research-workflow-stress-test-001` ↔ `skill-scenario-to-benchmark`
- `literature-screening-m1-001` ↔ `research-benchmark`
- `literature-screening-m1-001` ↔ `skill-scenario-to-benchmark`
- `crispr-resistance-e2e-001` ↔ `skill-scenario-to-benchmark`

These are not counted as additional official tasks. Before promotion or release,
each combination must identify one canonical task/version, record the source and
reference differences, and mark other copies as lineage variants or retired
duplicates. The static audit is maintained by
`scripts/audit_cross_repo_dedup.py`; its current result is in
`reports/cross_repo_dedup_audit_2026-09-24.md`.

## New candidate: `eb014-adaptive-evidence-ladder-003`

The supplied L12 data-heavy bundle was accepted as a candidate-only task and
expanded locally from v0.1.0 to v0.2.0. The expansion adds numeric rows and
vectors across all 11 measurement domains while preserving the 12-action
scientific ladder, 17 information sets, final claims and abstention policy.
Focused tests pass (`8 passed, 1 skipped`), but the historical RAW_PASS trial is
superseded; a fresh target-model trial and complete enterprise quality review are
still required. The updated provisional archive is
`dist/eb014-adaptive-evidence-ladder-003-l12-data-heavy-20260924-v020-final.tar.gz`.

## Per-task optimization contract

Optimize exactly one task at a time. A task is not considered optimized merely because its prompt or metadata changed. The task advances only after these gates pass:

1. Freeze the current task version and record the baseline data unit count.
2. Map every scored judgment unit to positive, negative, insufficient, or control evidence.
3. Add data that creates answerable positive/negative/boundary cases; every added row must be consumed by the verifier/reference calculation.
4. Update the reference oracle, mutation tests, and provenance hashes.
5. Run reference, legal baseline, abstention baseline, shortcut baseline, and target-model calibration.
6. Record the remaining failure attribution and source/reference closure status.
7. Promote only when the task has no unresolved data sufficiency blocker and its trial result matches the current data version.

## Optimization queue

### Wave 0: blocked tasks

1. `crispr-resistance-e2e-001` — either materialize licensed frozen assay/literature inputs plus verifier/reference, or narrow to a contract-review task.
2. `research-workflow-stress-test-001` — resolve placeholder DOI/source classification before scientific expansion.
3. `literature-screening-m1-001` — replace placeholder DOI records or explicitly keep it calibration-only.

### Wave 1: already expanded; recalibrate first

4. `eb010-closed-loop-ambiguity-004` — **data expansion v0.8.0 completed**: 22 records, inclusive threshold boundaries, independent blocker cases, oracle/reference synchronized; fresh model calibration remains required.
5. `eb010-distributional-policy-stress-006`
6. `eb013-evidence-budget-routing-002`

The working tree also contains staging versions of the related expanded tasks `eb010-stop-uncertainty-002`, `eb011-reproduction-manifest-001`, and `eb013-evidence-budget-routing-001`; optimize them only after deciding whether to promote them into the official 32-task scope.

### Wave 2: high-value decision and evidence tasks

7. `eb010-adaptive-policy-regret-005`
8. `eb010-closed-loop-replay-003`
9. `eb010-measurement-value-004`
10. `eb011-measurement-request-005`
11. `eb012-cross-stage-chain-002`
12. `eb012-cross-handoff-audit-001`
13. `eb013-cross-context-evidence-portfolio-005`
14. `eb013-partial-observation-risk-004`
15. `eb013-shared-setup-routing-003`

### Wave 3: reproducibility, feedback, and failure recovery

16. `eb014-sequential-evidence-feedback-002`
17. `eb015-real-source-replacement-gate-001`
18. `eb003-recovery-chain-005`
19. `eb003-failure-recovery-003`
20. `eb003-replay-provenance-004`
21. `eb001-split-leakage-001`

### Wave 4: biomedical analysis tasks

22. `admiral-adsl-derivation-001`
23. `biogen-adme-audit-001`
24. `eb004-adtte-censoring-002`
25. `eb005-batch-normalization-002`
26. `eb005-normalization-hierarchy-003`
27. `eb006-signal-noise-004`
28. `eb008-route-portfolio-002`
29. `eb008-stock-route-001`
30. `eb009-diversity-coverage-004`
31. `eb010-next-batch-001`
32. `eb010-next-batch-002`

## Candidate-only tasks

The following 14 working-tree packages are excluded from the 32-task release queue until promotion is approved: `eb006-donor-stratified-signal-005`, `eb006-research-completion-006`, `eb006-research-completion-007`, `eb006-research-completion-008`, `eb006-research-completion-009`, `eb006-research-completion-010`, `eb006-research-completion-011`, `eb010-stop-uncertainty-002`, `eb011-reproduction-manifest-001`, `eb012-revocation-portfolio-003`, `eb013-evidence-budget-routing-001`, `eb013-observation-boundary-004`, `eb014-adaptive-evidence-ladder-003`, and `eb014-evidence-gap-followup-001`.

## Immediate next task

The next action is a fresh target-model calibration against `eb010-closed-loop-ambiguity-004` version `0.8.0`. Do not modify another task until its data sufficiency, baseline, and model-trial record are closed.
