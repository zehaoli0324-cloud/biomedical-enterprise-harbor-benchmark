# Expected artifacts

## `outputs/adtte.csv`

CSV with exactly one row per `USUBJID` in `data/dm.csv` and columns `USUBJID,PARAMCD,TRTSDT,ADT,CNSR,EVNTDESC,ADT_DTYPE,DERIVATION_STATUS`. `CNSR=0` denotes a qualifying event, `CNSR=1` a valid censor, and `CNSR=` for a review row. `ADT_DTYPE` is `NONE`, `CUTOFF`, or `REVIEW`.

## `outputs/event_trace.csv`

CSV with columns `USUBJID,source_record,event_type,raw_date,date_precision,rule_id,selected_value`. Include all event and follow-up evidence used or rejected for each subject.

## `outputs/censoring_audit.json`

JSON with `schema_version`, `input_sha256`, `rules_version`, `summary`, `edge_cases`, `handoff`, and `claim_boundary`. The handoff decision must be `hold_for_review` because the fixture contains unresolved endpoint cases.

## `outputs/run_manifest.json`

JSON containing checksums for `dm.csv`, `events.csv`, `followup.csv`, and `rules.json`, plus the rules version, tool version, and deterministic flag.
