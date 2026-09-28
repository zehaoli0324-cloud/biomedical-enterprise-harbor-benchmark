# Evidence routing audit

This bounded planning review used the local manifest, uncertainty map, request catalog, rules, and output contract only. Network access was off, and this is **not experimental proof**.

The bottleneck was the pair of critical uncertainties: signal starts at 0.70 with a 0.25 threshold, and selectivity starts at 0.60 with a 0.25 threshold. `R-ASSAY` reduces signal by 0.50 and selectivity by 0.45. `R-ORTHO` is in a different correlation group and adds 0.25 signal and 0.20 selectivity reduction. The resulting residual map is signal 0.00, selectivity 0.00, and non-critical reproducibility 0.45. The maximum critical residual is therefore 0.00.

The selected route is `R-ASSAY` followed by `R-ORTHO`, with total cost 5.0, exactly the discovered budget. It has no prerequisites, so dependency validity is immediate. Correlation handling uses only the largest reduction per uncertainty within each group; the selected requests are in separate groups. Legal but unselected requests retain their full `covers` objects in `route.tsv`. `R-REPL` was not included because its prerequisite was not in this route, while its dependency exists in the catalog and therefore it is not intrinsically blocked.

`R-ARCHIVE` is excluded for the scope/current-provenance blocker, `R-POST` for future-outcome leakage, and `R-INCOMPLETE` for a missing dependency. Their effective reductions are `{}`. No post-decision outcome was used, and nominal value did not override any blocker.

The route crosses both critical thresholds within budget, so the stop condition is `route_selected` and human review is not required. If any prerequisite, provenance status, network state, or threshold interpretation changes, stop and rerun the bounded review. This remains a planning artifact, not experimental proof.
