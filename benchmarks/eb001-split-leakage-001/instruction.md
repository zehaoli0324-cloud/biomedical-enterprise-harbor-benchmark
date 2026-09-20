# Contract-only task: Molecular identity and scaffold leakage audit before ADME model comparison

You are acting as a DMPK_or_computational_chemist in the discovery_and_lead_optimization workflow. The enterprise decision is:

> Is the proposed ADME train/test split independent at the molecule and scaffold level, or must model comparison be held?

The task must preserve the independent unit (`molecule and canonical structure`), record the handoff, and stop or request review when the evidence is insufficient. It must not turn a computational result into a clinical, efficacy, safety, synthesizability, or causal claim.

This package is currently `contract_only`. The final agent-visible data bundle, hidden oracle, verifier, and resource-pinned environment are not yet attached. When materialized, the agent must record input checksums, versions, parameters, failures, and deterministic rerun information.

Required artifact contract:

- `outputs/split_audit.json`
- `outputs/structure_identity.tsv`
- `outputs/readiness_report.md`
- `outputs/run_manifest.json`

Release blockers are listed in the linked enterprise quality cards and must remain explicit until independently tested.
