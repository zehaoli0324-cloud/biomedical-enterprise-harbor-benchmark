# Molecular identity and scaffold leakage audit before ADME model comparison

You are acting as a DMPK_or_computational_chemist in the discovery_and_lead_optimization workflow. The enterprise decision is:

> Is the proposed ADME train/test split independent at the molecule and scaffold level, or must model comparison be held?

The task must preserve the independent unit (`molecule and canonical structure`), record the handoff, and stop or request review when the evidence is insufficient. It must not turn a computational result into a clinical, efficacy, safety, synthesizability, or causal claim.

The agent-visible bundle is a frozen synthetic calibration fixture. It is not sponsor data. Apply `data/split_rules.json` literally, distinguish canonical-structure leakage from scaffold leakage, preserve salt/stereochemistry identity notes and missing measurements, and block model comparison when either leakage class is present. The hidden reference and verifier are not agent-visible.

Required artifact contract:

- `outputs/split_audit.json`
- `outputs/structure_identity.tsv`
- `outputs/readiness_report.md`
- `outputs/run_manifest.json`

The fixture has calibrated positive, negative, row-order invariance, and insufficient-identity-policy controls. The final report must state the synthetic-data boundary and the human review handoff.
