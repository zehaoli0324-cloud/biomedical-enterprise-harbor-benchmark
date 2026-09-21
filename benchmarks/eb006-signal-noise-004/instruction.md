# Perturbation signal versus technical noise

Compare raw and nuisance-adjusted perturbation signal, preserve replicate-level provenance, and stop when the biological effect is not identifiable. A residual phenotype signal supports analytical triage only; it does not establish mechanism, target engagement, or efficacy.

Write exactly these files under outputs/:
- outputs/signal_noise_report.json with this contract: `raw_effect`, `adjusted_effect`, and `control_drift` are numbers; `replicate_count` is an integer; `identifiable` is a JSON boolean; `decision` is exactly `proceed_to_profile_review` or `hold_for_human_review`; `rules_version` is a string; `input_sha256` is keyed by `profiles.csv` and `rules.json`; `claim_boundary` contains `mechanism_established: false` and `human_review_required: true`.
- outputs/replicate_diagnostics.tsv: columns perturbation, plate, replicate, raw_signal, adjusted_signal, and control_status.
- outputs/profile_review_gate.md: signal result, technical noise result, human review decision, and a bounded statement about mechanism, target engagement, and efficacy.
