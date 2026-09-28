# Scientific Evidence Compliance SOP V1.0

This is the evidence-quality overlay for every biomedical Harbor task.

1. Classify every visible input as `REAL_PUBLIC_RAW`, `REAL_PUBLIC_DERIVED`, `SYNTHETIC_CALIBRATION`, or `RECIPE_ONLY` in a source manifest.
2. For real data, freeze accession, project URL, download URL, version/access date, license, file inventory, SHA-256, and derivation steps.
3. A DOI proves that a paper exists; it does not prove that the paper supports the task claim. Every material claim needs an exact locator and an entailment decision.
4. Never replace missing evidence with title keywords, a placeholder DOI, a model-generated observation, or a citation count.
5. Synthetic fixtures may test contracts, controls, failures, and abstention. They must not support clinical, causal, mechanistic, or biological-validity claims.
6. Separate association, prediction, functional evidence, mechanistic evidence, and clinical evidence. A higher tier requires an explicit design that supports it.
7. Every task must declare `supported_claims`, `unsupported_claims`, and the required `hold/uncertain/abstain` route.
8. The verifier must reject simulation-to-biology promotion, association-to-causality promotion, future-information leakage, and claims outside the validated data domain.
9. Real-source promotion requires source freeze, claim-evidence matrix, license/privacy review, independent scientific review, reference/negative/invariance controls, and replay.
10. Missing raw data, structural gold, accession, license, or independent review keeps the task `BLOCKED` or `REVIEW_REQUIRED`.

The machine-readable audit is produced by `scripts/audit_scientific_evidence.py` in the factory repository. A passing structural check never overrides a missing scientific gate.

## Real-data replacement plan

The controlled replacement registry is `config/real_data_replacement_registry.json`; its source of record is `Downloads/ten-task-real-data-replacement-plan.md`. It covers ten staged tasks and intentionally keeps source replacement separate from difficulty calibration.

For every task, freeze the accession or DOI, project and download URL, version or access date, license/rights, file inventory, per-file SHA-256, deterministic derivation steps, and the exact row/image/frame selection rule. Put a `data/numeric_provenance.tsv` row behind every scientific field; mark calibration files `CALIBRATION_EXCLUDED`. Put only the release allowlist in `data/release_input_manifest.json`. The runner must copy that allowlist when present, rather than copying a broad data directory.

Replacement order is fixed: (1) freeze source and rights, (2) derive the smallest deterministic snapshot, (3) record numeric provenance, (4) rebuild hidden labels and reference from the snapshot, (5) rebuild verifier and independent claim-boundary review, (6) run positive/negative/invariance/insufficient controls, (7) replay in the final environment, and only then package. Never hand-edit expected scientific values after importing a source.

The named sources are leads, not automatic permission to redistribute. The CRISPR paper/supplement, BBBC021 metadata/images/MoA files, and Zenodo MD archive each require a file-level rights decision. BBBC021 is versioned and includes copyrighted imagery; the official page identifies a 39,600-file image collection and ground-truth files, so a bounded image subset needs its own license and hash record. The Zenodo record identifies DOI `10.5281/zenodo.10362368`, version v1 and a 5.3 GB archive with a published checksum; use the exact downloaded file and rights metadata, not a locally reconstructed trajectory. These facts are source metadata, not benchmark evidence claims.

No raw data, structural gold, accession, license/rights decision, independent scientific review, or verifier rebind means `BLOCKED`/`REVIEW_REQUIRED`. A staging task cannot be described as real-data validated merely because a download exists. Legacy synthetic/calibration inputs remain allowed for engineering regression only and must be explicitly labeled `SYNTHETIC_CALIBRATION`.
