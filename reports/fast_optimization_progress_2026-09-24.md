# Fast Optimization Progress

Date: 2026-09-24

The four extension tasks are now optimized to a pretrial checkpoint. No target-trial status was rewritten.

| Task | Data surface | Controls | Focused tests | Trial status |
| --- | ---: | ---: | ---: | --- |
| `eb013-evidence-budget-routing-001` | 11 units / 9 observable / 2 insufficient | 6 calibrated | 6 passed | not run |
| `eb013-evidence-budget-routing-002` | 10 units / 9 observable / 1 insufficient | 6 calibrated | 7 passed | not run |
| `eb010-closed-loop-ambiguity-004` | 22 records / 21 units / 4 insufficient | 6 calibrated | 7 passed | recalibration required |
| `eb010-distributional-policy-stress-006` | 32 units / 21 positive / 11 negative | 6 calibrated | 3 passed | not run |

The remaining shared gate is evidence-surface abstention scoring: the current verifier controls prove pass/fail behavior, but the variant cards still lack auditable score weights. The parallel trial window should run against these current fixtures and preserve raw and replay artifacts; it should not mark formal release or overwrite the pretrial status.
