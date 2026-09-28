# Audit

The quality audit passed (`quality_ok`), so the target-context degradation is not treated as a measurement-quality artifact. The context comparison then observed `context_shift`; the orthogonal assay independently confirmed that the shift was not caused by quality. This supports a context-shift interpretation, but it does not authorize transporting the registered-cohort result to the target context, so `context_status` remains `HOLD`.

The independent replicate returned `replicate_ok` with an observed reproduced effect, supporting `replication_status: SUPPORTED` for the registered cohort only. The stop event was accepted after the quality, context, replication, and handoff checks were recorded. No additional experiment outcome is inferred from the stop action.

Uncertainty remains about behavior outside the registered cohort and about transport to the target context. The final claim is therefore bounded to `registered_cohort_only`; it is not a target-context or causal claim. Human review remains required for the unresolved transport question.
