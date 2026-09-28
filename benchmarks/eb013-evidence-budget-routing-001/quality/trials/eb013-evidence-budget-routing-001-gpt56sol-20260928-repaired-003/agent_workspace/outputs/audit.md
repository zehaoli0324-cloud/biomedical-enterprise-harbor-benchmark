# Evidence routing audit

The decision boundary is the critical residual threshold: signal starts at 0.70 with threshold 0.25, and selectivity starts at 0.60 with threshold 0.25. The selected route is `R-ASSAY` then `R-ORTHO`. Their combined reductions leave signal at 0.00 and selectivity at 0.00 after lower-bounding residuals at zero, so the maximum critical residual is 0.00.

The route costs 3.0 + 2.0 = 5.0, exactly the discovered maximum budget. Both requests are current, have no future-outcome dependency, and have no prerequisites, so the sequence is dependency-valid. Requests with the same correlation group were not added together: the G1 requests (`R-CHEM` and `R-CORR`) would contribute only the larger signal reduction if both were considered.

`R-ARCHIVE` is excluded for the scope blocker, `R-POST` for future-outcome leakage, and `R-INCOMPLETE` for its missing dependency. The remaining current requests are legal evidence candidates; unselected legal candidates retain their full catalog `covers` in `route.tsv`. `R-REPL` would additionally require `R-CHEM` in the same route, but that dependency route is inferior to the selected route under the objective.

The route is selected because it minimizes the maximum critical residual first, then cost, then lexical request IDs. No network was used, and no future outcome was used. This is a bounded planning decision and **not experimental proof**.
