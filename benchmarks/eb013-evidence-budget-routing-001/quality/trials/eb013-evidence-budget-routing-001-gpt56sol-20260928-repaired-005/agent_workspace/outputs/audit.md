# Evidence routing audit

The decision boundary is the pair of critical uncertainties `signal` and `selectivity`, with thresholds of 0.25. Their initial values are 0.70 and 0.60, so the route must provide at least 0.45 and 0.35 reduction respectively. `reproducibility` is non-critical and remains tracked.

The selected bottleneck route is `R-ASSAY` followed by `R-ORTHO`. Both requests have current provenance, no future outcome, and no dependencies, so the sequence is dependency-valid. Their correlation groups are different (`G2` and `G8`), so their reductions can be combined. The resulting reductions are signal 0.75 and selectivity 0.65, giving residuals signal 0.00 and selectivity 0.00; reproducibility remains 0.45. The maximum critical residual is therefore 0.00.

The route costs 3.0 + 2.0 = 5.0, exactly the discovered maximum budget. Other same-group requests were not added to manufacture reduction: `R-CHEM` and `R-CORR` share `G1`, so at most the larger signal reduction would count. `R-ARCHIVE` is excluded for the scope blocker, `R-POST` for future-outcome leakage, and `R-INCOMPLETE` for its missing dependency. Legal but unselected requests retain their full catalog covers in the route table.

The route is bounded, uses no network, and is planning-only, not experimental proof. The stop condition is `route_selected`; human review is not required because all critical thresholds are crossed within budget.
