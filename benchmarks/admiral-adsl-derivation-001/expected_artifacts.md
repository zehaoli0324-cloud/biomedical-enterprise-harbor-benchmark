# Expected artifacts

## `outputs/adsl.csv`

CSV with exactly one row per `USUBJID` in `data/dm.csv`, sorted by `USUBJID`, and these columns:

`USUBJID,ARMCD,TRT01P,ITTFL,SAFFL,PPROTFL,TRTSDT,TRTEDT,TRTEDT_DTYPE`

Dates use ISO `YYYY-MM-DD`. Empty dates remain empty. `TRTEDT_DTYPE` is `NONE` unless the cutoff was applied, in which case it is `CUTOFF`.

## `outputs/derivation_trace.csv`

CSV with columns `USUBJID,target_variable,source_domain,source_rows,rule_id,derived_value`. Include a trace for every subject's `ITTFL`, `SAFFL`, `PPROTFL`, `TRTSDT`, and `TRTEDT`. `source_rows` is a semicolon-separated list of source row identifiers such as `DM:SUBJ-001` or `EX:EX-001-01`. For a missing date, write `NA` in `derived_value` and explain the absence through the cited rule/source rows.

## `outputs/audit_report.json`

JSON with `schema_version`, `input_sha256`, `rules_version`, `summary`, `edge_cases`, `handoff`, and `claim_boundary`. The summary must include `subject_count`, `randomized_count`, `treated_count`, `itt_count`, `saffl_count`, and `pprot_count`. The handoff decision must be `hold_for_review` because the fixture contains unresolved boundary cases.

## `outputs/derivation_notes.md`

Markdown notes that mention screen failure, no exposure, missing RFENDTC, cutoff capping, and that the fixture is synthetic and not a clinical or sponsor conclusion.

## `outputs/run_manifest.json`

JSON containing `input_sha256` for `dm.csv`, `ex.csv`, and `rules.json`, `rules_version`, a non-empty `tool_version`, and `deterministic: true`.
