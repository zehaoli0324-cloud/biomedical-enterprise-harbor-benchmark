# Cross-stage claim and provenance chain audit

Use only the supplied offline JSON files. Evaluate every chain in order: recovery -> normalization -> route -> policy. A chain is eligible only when every artifact is active, schema/status pass, reported hash equals content hash, every upstream hash equals the previous content hash, normalization sensitivity is stable, route reservation is reserved with the required evidence quorum, policy has no future-outcome leakage and requires human review, and robust_cvar meets the threshold. The requested claim level must not exceed the minimum claim permission across all four artifacts.

Select by highest robust_cvar, then ascending chain_id. Ineligible chains cannot be selected. Round computed values to six decimal places.

Write exactly four artifacts: `outputs/chain.json` with selected_chain, rules_version and every chain record; `outputs/handoff.tsv` with one row for every artifact and columns artifact_id, chain_id, stage, upstream_hash, content_hash, claim_permission and status; `outputs/audit.md` explaining claim permission, upstream hash, inventory, human review, stop conditions and why this is not experimental proof; and `outputs/manifest.json` with hashes for case.json and rules.json, rules_version and deterministic=true.
