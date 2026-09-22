# Evidence and Claim-Boundary Audit

The initial baseline and target-context measurements had unresolved quality, so the first action was a quality audit. The observed `quality_ok` result (M-QC PASS) reduces the quality-artifact explanation for the measured degradation, but it does not by itself establish transfer to the target context.

After quality passed, the context comparison was run. It observed `context_shift` with M-CONTEXT effect 0.08 and status `SHIFT_DETECTED`. This supports a difference between the registered cohort and target context under this protocol. It is not a causal estimate of target-context performance and does not identify the mechanism of the shift.

An independent registered-cohort unit was then tested. The observed `replicate_ok` result (M-REPL effect 0.39, status `REPRODUCED`) supports reproducibility of the registered-cohort effect. It does not replicate the target-context measurement, and no orthogonal assay was run because the accepted stop action completed the public checks.

The round-4 `stop` response was observed as `stopped` with zero cost and three budget units remaining. The log records that response before completion. There is no unresolved blocker requiring handoff, but human review remains required because the context shift and its cause remain uncertain.

The final claim is therefore limited to the registered cohort: quality passed and the registered-cohort effect reproduced, while a context shift was observed. This does not justify claiming that the effect, its magnitude, or its cause transfers to the target context. This is synthetic planning evidence, not laboratory evidence or a causal claim.
