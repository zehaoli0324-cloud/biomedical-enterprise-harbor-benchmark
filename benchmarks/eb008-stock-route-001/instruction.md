# Retrosynthesis route selection

Derive reaction validity from `reaction_evidence.json` and `rules.json`; no route is pre-labelled valid. Select only routes that satisfy target identity, stock availability, step budget, precedent scope, chemoselectivity risk, stereochemistry and protection-strategy gates. A higher score cannot override a failed gate, and a computational route is not proof of experimental synthesizability.

Required outputs: `outputs/route_table.tsv` with route identity, stock evidence, derived reaction validity, failed gates and accepted status; `outputs/stock_compliance.json` with all route rows and `selected_route_ids`; `outputs/route_evidence.tsv` covering every route and reaction step; and `outputs/approval_gate.md` stating the unresolved chemistry evidence, required human review and that computational validity is not experimental proof. Equivalent field names are acceptable when their meaning is explicit.
