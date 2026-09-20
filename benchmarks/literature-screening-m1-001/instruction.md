# Agent Task

You are an evidence-synthesis analyst screening a frozen set of literature records for a human cancer drug-resistance question.

Read `data/constraints.yaml` before screening. For every row in `data/literature_records.tsv`, produce exactly one decision: `include`, `exclude`, `context_only`, or `uncertain`. Use one of the listed reason codes for the corresponding decision and write `confidence` as a numeric value from `0.0` to `1.0` rather than a word such as `high`. Do not use the network and do not infer unavailable methods or full-text details.

## Required outputs

Write all files below under `outputs/`:

- `screening_decisions.tsv`: `record_id`, `decision`, `reason_code`, `confidence`, `evidence_locator`.
- `evidence_table.tsv`: `claim_id`, `source_id`, `evidence_type`, `support_status`, `locator`, `limitation`.
- `uncertainty_queue.tsv`: `record_id`, `uncertainty_reason`, `minimum_next_check`.
- `run_manifest.json`: `input_sha256`, `rules_version`, `tool_version`.
- `final_report.md`: screening summary, evidence boundary, uncertainty, and next step.

The evidence table must include a locator for every included or context-only source. An association-only source may support contextual evidence, but it must not be used to support a causal claim. A duplicate must be resolved using normalized DOI and must not be counted twice. An incomplete record must go to the uncertainty queue instead of being guessed.

The final report must contain the exact headings `Screening summary`, `Evidence boundary`, `Uncertainty`, and `Next step`. State whether the available records are sufficient for a causal mechanism claim. They are not sufficient merely because a record is marked `include`.
