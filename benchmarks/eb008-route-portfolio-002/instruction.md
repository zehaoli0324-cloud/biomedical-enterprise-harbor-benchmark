# shared-inventory route portfolio with dependent evidence

Use only `data/case.json` and `data/rules.json`. Apply the following deterministic rule exactly; do not substitute a different scoring formula or add an unstated approval gate.

A route is accepted only when every material requirement fits current stock, independent_sources >= min_independent_sources, evidence_status is `current`, and target equals rules.target. Enumerate pairs of accepted routes and retain a pair only if its combined material use fits stock. Select the lexically first retained pair and join its IDs with `+`; otherwise select the lexically first accepted route; if none is accepted, use `reject`. Evidence outcomes are lowercase `true` or `false`. The evidence entity is `route_id`.

Produce exactly these files under `outputs/`:

- `outputs/decision.json`: a JSON object with `decision` set to the exact decision string and `rules_version` copied from the rules.
- `outputs/evidence.tsv`: a tab-separated table with columns `entity`, `outcome`, `decision`, `provenance`, `uncertainty`, `claim_boundary`. Include every input entity exactly once. Repeat the final decision in every row. `provenance` and `claim_boundary` must be nonempty.
- `outputs/review.md`: explain the result and uncertainty. It must explicitly contain the phrases `human review`, `stop`, and `not experimental proof`.
- `outputs/manifest.json`: a JSON object with `input_sha256` mapping the bare names `case.json` and `rules.json` to their SHA-256 hashes, `rules_version` copied from the rules, and `deterministic` set to true.

Request review or stop only when the rule above returns a hold, block, reject, escalation, or information request. Do not replace a valid deterministic selection with a new approval enum. This is a planning/review aid, not experimental proof.

`decision.json` must contain `decision` and `rules_version` (and may include `details`). `evidence.tsv` must contain exactly one row for every route entity in `data/case.json`, with columns `entity`, `outcome`, `decision`, `provenance`, `uncertainty`, and `claim_boundary`; use the route ID as `entity` and record its accepted status as `outcome`. `manifest.json` must contain `input_sha256` with the SHA-256 hashes of `case.json` and `rules.json`, plus `rules_version` and `deterministic: true`. `review.md` must explicitly state human review, stop conditions, and that this is not experimental proof.
