# Expected Artifacts

The verifier checks the following interface:

| Artifact | Required fields or checks |
| --- | --- |
| `outputs/screening_decisions.tsv` | one row per input record; valid decision, reason, confidence, locator |
| `outputs/evidence_table.tsv` | claim ID, source ID, evidence type, support status, locator, limitation |
| `outputs/uncertainty_queue.tsv` | every uncertain record and a concrete next check |
| `outputs/run_manifest.json` | checksum of input data, rules version, tool version |
| `outputs/final_report.md` | four required headings and an explicit causal boundary |

The hidden reference checks decisions, reason codes, duplicate handling, association-vs-causality handling, uncertainty routing, and reproducibility metadata. It does not require a particular prose style.
