# EB013-002 target trial analysis

The gpt-5.6-sol agent selected the correct adaptive stage-one request and conditionally routed `signal_high` to `R-SELECT` and `signal_low` to `R-CORR`. The raw runner verifier rejected only omitted derived policy-state fields (`max_critical_residual` and `eligible`). The unchanged artifacts passed canonical replay after those fields were derived from the declared residuals and thresholds. This is a contract replay pass, not evidence that the model was defeated; fixed-container replay and practitioner review remain release blockers.
