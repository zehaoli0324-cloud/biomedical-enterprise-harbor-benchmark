# Cross-stage claim and provenance chain audit

Use only the supplied offline JSON files. Evaluate every chain in order: recovery -> normalization -> route -> policy. A chain is eligible only when every artifact is active, schema/status pass, reported hash equals content hash, every upstream hash equals the previous content hash, normalization sensitivity is stable, route reservation is reserved with the required evidence quorum, policy has no future-outcome leakage and requires human review, and robust_cvar meets the threshold. The requested claim level must not exceed the minimum claim permission across all four artifacts.

Select by highest robust_cvar, then ascending chain_id. Ineligible chains cannot be selected. Round computed values to six decimal places.

Write exactly four artifacts:

- `outputs/chain.json`: an object with `selected_chain`, `rules_version`, and `chains`. `chains` is a four-item array, one row per input chain, with `chain_id`, `eligible`, `requested_claim`, `robust_cvar`, and `artifact_ids`. Additional audit fields are allowed.
- `outputs/handoff.tsv`: exactly one row per artifact and the header `artifact_id`, `chain_id`, `stage`, `upstream_hash`, `content_hash`, `claim_permission`, `status`. Use the artifact's highest listed permission in `claim_permission`. Encode a root artifact's missing upstream hash as either an empty field or `null`.
- `outputs/audit.md`: explain the claim-permission boundary, upstream-hash checks, inventory, human review, stop conditions, and why the result does not constitute experimental proof. Equivalent hyphenation and wording are allowed.
- `outputs/manifest.json`: include `rules_version`, `deterministic=true`, and SHA-256 hashes for `case.json` and `rules.json`. The canonical form is `input_sha256: {"case.json": "...", "rules.json": "..."}`; semantically equivalent direct or `hashes` mappings are accepted.
