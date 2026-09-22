# Target Trial Analysis

Four target trials were run with `gpt-5.6-sol`. All agents exited with code 0 and none timed out. The raw runner verifier returned `fail` in every trial, but the failures were output-contract representations rather than a wrong chain decision.

| trial | raw verifier result | replay result | attribution |
| --- | --- | --- | --- |
| `gpt56sol-001` | fail: chain representation, permission representation, manifest provenance | pass after contract replay | equivalent chain records and declared hash/permission forms |
| `gpt56sol-002` | fail: chain representation, permission representation, manifest provenance | pass after contract replay | same contract representation issue; scientific decision unchanged |
| `gpt56sol-003` | fail: four root `upstream_hash` values and manifest provenance | pass after contract replay | TSV `null` versus empty root hash and `case_sha256/rules_sha256` aliases |
| `gpt56sol-004` | fail: per-artifact permission and audit wording | pass after contract replay | per-artifact permission is compatible with chain-minimum semantics; equivalent audit wording |

Every replay selected `CHAIN-A`, rejected the hash-drift, inventory-conflict, sensitivity-unstable, and claim-overreach distractors, and preserved the human-review boundary. The model was therefore not defeated on the scientific or cross-stage reasoning dimension. The remaining release blockers are fixed-container replay and practitioner review; raw runner failures remain preserved as evidence and are not relabeled as original PASS results.
