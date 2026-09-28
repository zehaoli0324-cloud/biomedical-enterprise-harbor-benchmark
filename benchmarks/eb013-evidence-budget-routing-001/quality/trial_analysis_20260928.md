# EB013-001 gpt-5.6-sol trial analysis (2026-09-28)

Trial ID: `eb013-evidence-budget-routing-001-gpt56sol-20260928-001`  
Runner: local `process_cwd_only`; the existing Docker/Harbor environment was not used.  
Model: `gpt-5.6-sol`; agent exit code `0`; timeout: `false`.

## Observed result

The agent wrote all five required artifacts and selected `R-ASSAY + R-ORTHO`, cost `5.0`, with a claimed maximum critical residual of `0.0`. The hidden verifier returned `verifier_fail` with 11 errors: residual map mismatch, effective-reduction mismatches for all catalog requests, and provenance mismatch.

The route choice agrees with the declared minimax objective, but the submitted derived fields and provenance are not yet accepted by the current verifier. This is recorded as `scientific_or_delivery_fail_pending_triage`; it is not counted as valid difficulty evidence until the raw artifact is independently replayed and the failure is classified.

## Evidence

Raw artifacts and manifest remain at the trial directory recorded in `quality/target_trial_evidence_20260928.json`. Their SHA-256 values are stored there. No task instruction, data, or verifier was changed after the run.

## Next action

Perform unchanged-artifact replay and compare the submitted reduction/provenance fields with the v0.1.1 oracle. If the route is scientifically correct and only an announced representation is incompatible, record a contract replay result; otherwise preserve the scientific failure. Fixed-container replay and practitioner review remain open.
