# Contract-only task: Cell Painting normalization choice under controlled batch confounding

You are acting as a image_analysis_or_phenomics_scientist in the high_content_screening workflow. The enterprise decision is:

> Which normalization and replicate aggregation choice removes batch effects without erasing a reproducible phenotype?

The task must preserve the independent unit (`plate-level replicate aggregate`), record the handoff, and stop or request review when the evidence is insufficient. It must not turn a computational result into a clinical, efficacy, safety, synthesizability, or causal claim.

This package is currently `contract_only`. The final agent-visible data bundle, hidden oracle, verifier, and resource-pinned environment are not yet attached. When materialized, the agent must record input checksums, versions, parameters, failures, and deterministic rerun information.

Required artifact contract:

- `outputs/normalization_comparison.tsv`
- `outputs/batch_report.json`
- `outputs/sensitivity_summary.md`
- `outputs/run_manifest.json`

Release blockers are listed in the linked enterprise quality cards and must remain explicit until independently tested.
