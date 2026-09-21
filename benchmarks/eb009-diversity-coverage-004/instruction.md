# Candidate diversity audit

Check validity, unique IDs, scaffold coverage and cluster coverage before human synthesis review. Computed diversity is not biological activity.

Write exactly these files under `outputs/`:
- `outputs/candidate_set.tsv`: columns `candidate_id`, `scaffold`, `cluster`, and `valid`.
- `outputs/diversity_report.json`: counts, scaffold/cluster lists, coverage, rules version, and input hashes.
- `outputs/coverage_review_gate.md`: coverage result, scaffold evidence, human review decision, and the statement that this is not biological activity.
- `outputs/run_manifest.json`: input hashes, rules version, and `deterministic: true`.
