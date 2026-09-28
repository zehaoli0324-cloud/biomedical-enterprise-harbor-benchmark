# Evidence routing audit

The decision boundary is the approval or hold of the next experiment batch. This is a bounded planning review and **not experimental proof**.

## Bottleneck and route

The critical uncertainties are `signal` (0.70, threshold 0.25) and `selectivity` (0.60, threshold 0.25). The selected route is `R-ASSAY` followed by `R-ORTHO`, with total cost 5.0, exactly the discovered maximum budget. Their groups (`G2` and `G8`) are distinct, so the reductions combine across groups: signal reduction is 0.50 + 0.25 = 0.75 and selectivity reduction is 0.45 + 0.20 = 0.65. Residuals are capped at zero, giving critical residuals of 0.00 and a maximum critical residual of 0.00. Reproducibility remains 0.45 because the selected requests do not cover it; it is non-critical.

This route has the smallest attainable maximum critical residual. Among routes at that objective value, its cost is the minimum (5.0), and the selected IDs are recorded lexically. No selected request has a dependency, so the sequence is dependency-valid.

## Eligibility and dependencies

Only current requests with current provenance, satisfied prerequisites, and no post-decision outcome are usable. `R-ARCHIVE` is intrinsically blocked by scope, `R-POST` by future-outcome leakage, and `R-INCOMPLETE` by its missing dependency `R-MISSING`; each therefore has empty effective reductions. `R-REPL` is otherwise legal and retains its full covers object in `route.tsv`, but its prerequisite `R-CHEM` is not in the selected route, so it is excluded for this route.

The other legal, current requests are listed exactly once and retain their complete `covers` objects even when excluded because the selected route is better. No request was added merely for nominal value.

## Correlation and stop condition

Within any one correlation group, only the largest reduction for each uncertainty would count. The selected requests are in separate groups, and no correlation double-counting occurs. `R-CHEM` and `R-CORR` are both in `G1`; neither is selected, so they cannot manufacture additional signal reduction. `R-POST` is not considered evidence because it exposes a future outcome.

The route stays within budget and brings every critical residual to its threshold or below, so the stop condition is `route_selected` and human review is not required. Network access was off and no future outcome was used.
