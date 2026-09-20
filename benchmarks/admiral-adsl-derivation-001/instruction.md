# Agent task

You are a statistical programmer preparing a subject-level analysis dataset for a downstream time-to-event analysis. The public pharmaverse admiral project is the workflow reference, but the files in this task are a synthetic calibration fixture and must not be described as sponsor or patient data.

## Scientific question

Using only `data/dm.csv`, `data/ex.csv`, and `data/rules.json`, derive one ADSL-like row per subject. Decide whether the resulting dataset can be handed off for downstream analysis or must be held for review. Apply the rules literally and preserve the distinction between randomized, treated, and per-protocol populations.

## Required process

1. Inspect the input schemas, duplicate identifiers, date formats, and the rule version before deriving values.
2. Apply the frozen cutoff and population rules. Do not silently invent dates or drop subjects.
3. Create a source-to-target trace for derived flags and treatment dates. Each trace row must identify the subject, target variable, source domain/row, rule ID, and derived value.
4. Report edge cases, counts, and the handoff decision. A derivation result is not a clinical conclusion and does not establish a sponsor analysis.
5. Record SHA-256 checksums for all three input files, a tool version, and deterministic execution in the run manifest.

## Prohibited shortcuts

- Do not treat the number of DM rows as the number of treated subjects.
- Do not set SAFFL=Y for a randomized subject with no qualifying EX record.
- Do not set PPROTFL=Y when RFENDTC is missing or after the cutoff.
- Do not leave a post-cutoff TRTEDT unmarked or silently delete the subject.
- Do not claim that this synthetic fixture supports efficacy, safety, or a clinical decision.

## Deliverables

Write the following files under `outputs/`:

- `adsl.csv`
- `derivation_trace.csv`
- `audit_report.json`
- `derivation_notes.md`
- `run_manifest.json`

The exact required fields are listed in `expected_artifacts.md`.
