# Computational artifact replay

Reconcile the recorded artifact, input/output checksums, environment and rerun result. Hold unexplained differences for human review.

Write exactly these files under `outputs/`:
- `outputs/replay_manifest.json`: artifact ID, rules version, input/output hashes, environment and replay status.
- `outputs/provenance_diff.tsv`: columns `field`, `status`, and `match`.
- `outputs/handoff_replay_report.md`: replay result, checksum evidence, human review decision, and the statement that this is not biological validation.
