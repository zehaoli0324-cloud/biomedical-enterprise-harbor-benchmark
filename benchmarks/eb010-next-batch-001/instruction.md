# Contract-only task: Next-batch experimental design under feasibility and budget constraints

You are acting as a experimental_design_scientist in the closed_loop_experimental_optimization workflow. The enterprise decision is:

> Which next batch is legal under the search space, material budget, and feasibility constraints, and what evidence supports selecting it?

The task must preserve the independent unit (`candidate experiment and batch`), record the handoff, and stop or request review when the evidence is insufficient. It must not turn a computational result into a clinical, efficacy, safety, synthesizability, or causal claim.

This package is currently `contract_only`. The final agent-visible data bundle, hidden oracle, verifier, and resource-pinned environment are not yet attached. When materialized, the agent must record input checksums, versions, parameters, failures, and deterministic rerun information.

Required artifact contract:

- `outputs/next_batch.csv`
- `outputs/constraint_check.json`
- `outputs/uncertainty_table.tsv`
- `outputs/selection_rationale.md`

Release blockers are listed in the linked enterprise quality cards and must remain explicit until independently tested.
