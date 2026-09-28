# EB006-011 Trial Analysis

The oracle-repaired cross-assay version was run with `gpt-5.6-sol`. The model
produced all four required artifacts and the public completion gate accepted the
submission after clean and reversed-row replays. It exited with code 124 at
1154.08 seconds because the shared process budget ended after artifact delivery.

The independent scientific verifier passed. The model correctly reconciled
nominal `C43`, pooled `C28`, robust paired `C17`, and applied the independent
assay gate to hold the final selection (`selected: null`, `cross_assay_hold: true`).
The expanded assay table, exact effect-range formula, closed reason-code set and
all input hashes were accepted.

Classification is `TIMEOUT_OUTPUT_COMPLETE_SCIENCE_PASS`: the trial demonstrates
long-horizon delivery pressure and successful science under a bounded budget, but
does not show that the model was scientifically defeated. Human review, isolated
container replay and held-out model transfer remain NOT_RUN.

The later trial `gpt56sol-cross-assay-v1-005` completed normally in 854.00 seconds
and passed the public completion gate on its first submission. The independent
scientific verifier rejected the result because `C43|late` was marked `SUPPORTED`
despite incomplete D4 assay coverage, including on the perturbation replay. The
submission also added an undeclared `runtime` provenance field. This is
`SCIENTIFIC_FAIL_CONTRACT_PASS`: valid difficulty evidence, with no infrastructure
or completion-gate attribution. Because an earlier target trial passed the science
verifier, another replicate is needed before claiming stable target-model defeat.
