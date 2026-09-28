# Evidence review and follow-up allocation

A translational review board needs a defensible current claim ledger and a small follow-up program for the registered claims. Reconstruct the evidence from measurements and source metadata, then recommend a contingent research policy under the shared budget. Decide the work order yourself.

Use the synthetic acceptance and planning rules in `data/rules.json`. The claim registry in `evidence.json` defines which premises authorize each scope; primary-cohort evidence alone does not authorize target-population claims. Source counts are not independent evidence counts. Preserve excluded observations and their exclusion reasons.

The objective rewards resolving a registered question, whether supported or refuted, not promising a positive outcome. Optimize across every possible outcome, respecting action dependencies at the moment an action is chosen. Include a hold option. No follow-up has actually been run: `feedback.json` is a catalogue of hypothetical measurements for static conditional replay, not observed evidence or a live service. Current claims must use only initial observations. A refuted acceptance premise does not establish the opposite biological or causal claim.

Write the five artifacts defined in `data/output_contract.json` under `outputs/`. Explain the substantive evidence gaps, rejected shortcuts, conditional stopping and human-review boundary in `audit.md`. This is synthetic planning, not experimental proof. Network access is off; algorithms and local tools are your choice.

Required paths: `outputs/claim_ledger.json`, `outputs/research_plan.json`,
`outputs/adaptive_update.json`, `outputs/provenance.json`, and `outputs/audit.md`.
