# Offline Input Dataset

`literature_records.tsv` is a small synthetic, frozen dataset used to calibrate the first downstream benchmark slice. It is deliberately not a live literature search and does not assert that the DOI-like identifiers refer to real papers.

The records include four controlled difficulty features:

- a duplicate DOI with conflicting metadata (`LIT-001` / `LIT-005`);
- a primary association-only study (`LIT-003`);
- an animal-only study (`LIT-004`);
- a sensitivity study that does not satisfy the resistance outcome (`LIT-006`);
- an incomplete metadata-only record (`LIT-007`).

The benchmark is offline after setup. The agent must use only these files and must record the input checksum in `outputs/run_manifest.json`.
