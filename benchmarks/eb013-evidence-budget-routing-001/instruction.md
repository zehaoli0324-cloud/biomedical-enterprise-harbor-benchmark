# Evidence routing review

This is a bounded planning and review task, not experimental validation. The input bundle is intentionally nested and does not restate the field meanings in this instruction. Inspect the bundle recursively, read its manifest, reconstruct the uncertainty map and request catalog, and determine which evidence route can cross the decision boundary without using network access or future outcomes.

Decide whether to execute a bounded evidence route or stop for human review. A request is usable only when its provenance is current, its prerequisites are satisfied by the same route, and it does not use a post-decision outcome. Requests in the same correlation group cannot be added together to manufacture reduction: for each uncertainty, only the largest reduction from that group counts. The route must stay within the discovered budget and reduce every critical uncertainty to its declared threshold. Select the valid route with the smallest maximum critical residual, then the lowest cost, then lexical request IDs. If no route crosses all critical thresholds, stop for human review. A high nominal value does not override a blocker.

Write these artifacts under `outputs/`:

- `outputs/plan.json`: your selected request sequence, dependency-valid route strategy, total cost, `network_used=false`, and a stop condition of `route_selected` or `human_review_required`.
- `outputs/route.tsv`: one row for every catalog request with request ID, status, included flag, blockers, effective reductions, and route position.
- `outputs/decision.json`: selected request IDs, decision, route cost, residual uncertainty map, objective values, and human-review requirement.
- `outputs/provenance.json`: discovered input paths and SHA-256 hashes, rules version, network state and deterministic flag.
- `outputs/audit.md`: explain bottleneck selection, dependency and correlation handling, future-outcome exclusion, budget, stop condition and the phrase `not experimental proof`.

Equivalent representations are accepted when they preserve meaning: `selected_request_ids` may be a list or `route`; booleans may be JSON booleans or lowercase strings; blocker lists may be semicolon-joined in TSV; and discovery paths may consistently include or omit the `data/` prefix. Do not assume a hidden canonical request order.
