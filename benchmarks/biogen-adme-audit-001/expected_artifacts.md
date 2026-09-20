# Expected artifacts

## `outputs/audit_report.json`

```json
{
  "schema_version": "1.0",
  "input_sha256": "...",
  "summary": {"row_count": 8, "train_rows": 4, "test_rows": 4},
  "leakage": {"structure_overlap": [{"structure_key": "c1ccccc1", "train_ids": ["CMP-003"], "test_ids": ["CMP-008"]}]},
  "unit_audit": {"expected_unit": "uM", "issues": [{"compound_id": "CMP-007", "observed_unit": "mM", "converted_to_uM": 500.0}]},
  "missingness": {"compound_ids": ["CMP-006"]},
  "readiness": {"decision": "blocked", "reason": "..."}
}
```

The verifier checks the scientific facts above, not byte-for-byte formatting or the exact prose of the recommendation.

## `outputs/audit_notes.md`

The notes must mention the three observed issue classes and explicitly state that the fixture is synthetic and does not establish enterprise validation.

## `outputs/run_manifest.json`

The manifest must contain `input_sha256`, a non-empty `tool_version`, and `deterministic: true`.
