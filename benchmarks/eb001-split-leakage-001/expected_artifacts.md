# Expected artifacts

Write the following artifacts under `outputs/`:

- `outputs/split_audit.json`
- `outputs/structure_identity.tsv`
- `outputs/readiness_report.md`
- `outputs/run_manifest.json`

`split_audit.json` must contain `schema_version`, `summary`, `canonical_overlap`, `scaffold_overlap`, `identity_notes`, `missing_measurements`, `input_sha256`, `rules_version`, and a `readiness.decision` of `blocked` for this fixture. `structure_identity.tsv` must contain one row per compound with identity evidence. `readiness_report.md` must explain canonical, scaffold, salt, missingness, synthetic boundary, and enterprise validation. `run_manifest.json` must record input hashes, rules version, tool version, and deterministic execution.
