# EB013-002 gpt-5.6-sol trial analysis (2026-09-28)

Trial ID: `eb013-evidence-budget-routing-002-gpt56sol-20260928-001`  
Runner: local `process_cwd_only`; Docker/Harbor fixed-container execution was unavailable.  
Model: `gpt-5.6-sol`; agent exit code `0`; timeout: `false`.

## Observed result

The agent selected `R-ADAPTIVE` with `R-SELECT` for `signal_high`, `R-CORR` for `signal_low`, and `R-BALANCE` for `signal_mid`; worst-case critical residual was `0.25` at cost `5.0`. This agrees with the expected adaptive route objective.

The hidden verifier returned `verifier_fail` with four errors: `plan policies mismatch`, `route schema mismatch`, `route coverage mismatch`, and `provenance mismatch`. All five required artifacts were produced, but their serialized contract was not accepted.

## Evidence

Raw artifacts and their SHA-256 values are recorded in `quality/target_trial_evidence_20260928.json`. No task instruction, data, or verifier was changed after the run.

## Next action

Replay the unchanged artifacts against the v0.3.0 oracle and determine whether the mismatch is limited to policy/TSV/provenance representation or reflects a substantive route error. Fixed-container replay and practitioner review remain open.
