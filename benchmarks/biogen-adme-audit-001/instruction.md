# ADME measurement split audit

You are auditing a frozen, synthetic ADME measurement fixture before it is used in a modeling benchmark.

Read `data/adme_measurements.csv` and produce exactly these files under `outputs/`:

1. `audit_report.json`
2. `audit_notes.md`
3. `run_manifest.json`

The report must include:

- total, train and test row counts;
- every canonical structure that appears in both train and test, with the affected compound IDs;
- every row whose unit is not the declared comparison unit `uM`, including the observed unit and a numeric conversion to `uM` when possible;
- every compound with a missing measurement;
- a readiness decision and a short reasoned recommendation.

Record the SHA-256 digest of the input CSV in both JSON artifacts. State the tool/runtime used and whether the run is deterministic.

The fixture is synthetic. Do not claim that it is private Biogen data, and do not infer model performance, clinical efficacy or experimental success from this audit. If a value cannot be established from the input, report the uncertainty instead of inventing it.
