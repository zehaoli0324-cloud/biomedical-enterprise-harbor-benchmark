# Contract-only task: Computational biology tool failure recovery with claim-preserving handoff

You are acting as a bioinformatics_or_research_analyst in the computational_biology_support workflow. The enterprise decision is:

> After a version-pinned tool branch fails or returns partial output, can the analyst recover without changing the scientific question or overclaiming?

The task must preserve the independent unit (`analysis branch and artifact state`), record the handoff, and stop or request review when the evidence is insufficient. It must not turn a computational result into a clinical, efficacy, safety, synthesizability, or causal claim.

This package is currently `contract_only`. The final agent-visible data bundle, hidden oracle, verifier, and resource-pinned environment are not yet attached. When materialized, the agent must record input checksums, versions, parameters, failures, and deterministic rerun information.

Required artifact contract:

- `outputs/execution_log.jsonl`
- `outputs/failure_recovery.md`
- `outputs/claim_ledger.tsv`
- `outputs/run_manifest.json`

Release blockers are listed in the linked enterprise quality cards and must remain explicit until independently tested.
