# Near-Completion Queue: 14 Tasks

This directory is a metadata queue for the ten official tasks nearest to formal completion. The task packages remain in `benchmarks/<task_id>/`; this queue does not duplicate or move their data.

Current workflow stage: `FAST_CLOSE_QUEUE_EXTENDED`.

The first three are the shortest preliminary close path and already have a `quality/preliminary_completion_20260924.json` record:

1. `eb013-cross-context-evidence-portfolio-005`
2. `eb014-sequential-evidence-feedback-002`
3. `eb015-real-source-replacement-gate-001`

The remaining seven original tasks are queued behind them. Four additional calibration-ready tasks have now been appended for optimization; they do not yet have a current target trial. Every entry still has formal release blockers. The queue is an execution aid, not a release declaration.

## Extension for parallel trials

The extension is deliberately separated from the ten-task fast-close segment so another window can run target trials without confusing baseline/calibration status with release status:

11. `eb013-evidence-budget-routing-001`
12. `eb013-evidence-budget-routing-002`
13. `eb010-closed-loop-ambiguity-004`
14. `eb010-distributional-policy-stress-006`

For these four, the local optimization work should focus on evidence-surface completeness, data sufficiency, and replay controls before the parallel trial results are merged.

Use `manifest.json` as the authoritative order and gate summary for the next pass.

The v3 calibrated archive `dist/selected-four-v3-calibrated-20260924.tar.gz` is attached as a calibration bundle. It contains four task snapshots already present in this queue, so it adds evidence but does not add a new unique task.
