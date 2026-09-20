# Contract-only task: Retrosynthesis route selection under stock and reaction validity constraints

You are acting as a medicinal_chemist_or_design_scientist in the medicinal_chemistry workflow. The enterprise decision is:

> Which routes satisfy target structure, allowed stock, reaction validity, and search-budget constraints for human chemistry review?

The task must preserve the independent unit (`target molecule and route`), record the handoff, and stop or request review when the evidence is insufficient. It must not turn a computational result into a clinical, efficacy, safety, synthesizability, or causal claim.

This package is currently `contract_only`. The final agent-visible data bundle, hidden oracle, verifier, and resource-pinned environment are not yet attached. When materialized, the agent must record input checksums, versions, parameters, failures, and deterministic rerun information.

Required artifact contract:

- `outputs/route_table.tsv`
- `outputs/stock_compliance.json`
- `outputs/route_evidence.tsv`
- `outputs/approval_gate.md`

Release blockers are listed in the linked enterprise quality cards and must remain explicit until independently tested.
