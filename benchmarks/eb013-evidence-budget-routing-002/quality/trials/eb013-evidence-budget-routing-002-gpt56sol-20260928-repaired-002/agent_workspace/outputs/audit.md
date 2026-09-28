# Audit

This is a deterministic planning replay, not experimental proof. All declared observation states were enumerated before routing: `R-ADAPTIVE` has `signal_high`, `signal_low`, and `signal_mid`; `R-FIXED` has `chem_clean` and `chem_risk`; `R-CHEAP` has `screen_positive` and `screen_negative`; and `R-CONTEXT` has `context_clear` and `context_conflict`.

Stage 1 is selected before observing its declared outcome. Stage 2 is then gated by the observed state, its `allowed_observations`, current status, `future_outcome=false`, and dependency IDs. The future-outcome request `R-POST` is excluded. No archived or missing-prerequisite request is used. `R-FIXED` is incomplete because its only potentially applicable replication request requires the missing stage-1 prerequisite `R-CHEAP`.

The stage-1 budget is 3.0 and the total budget is 5.0. `R-ADAPTIVE` uses costs 3.0 plus a worst-case stage-2 cost of 2.0, exactly 5.0. Other complete mappings stay within budget. For each state, residuals subtract the stage-1 reduction, the observation-specific stage-2 reduction, and the declared observation adjustment. Reductions in one correlation group are combined by taking only the largest reduction per uncertainty; this makes the `R-CONTEXT` stage-2 check share group `G8` with its stage-1 request rather than add reductions.

Eligibility is evaluated independently for every state against signal and selectivity thresholds of 0.25, then conjoined at policy level. `R-ADAPTIVE` is the only complete policy eligible in every state, with worst-case maximum critical residual 0.25 and worst-case cost 5.0. It is selected by the stated residual, cost, and lexical tie-break order. Incomplete policies have null policy-level worst-case residual and cost, as required.

Human review remains required before execution. The route expresses an adaptive plan under the supplied assumptions; it does not establish efficacy, causal effect, or any experimental result.
