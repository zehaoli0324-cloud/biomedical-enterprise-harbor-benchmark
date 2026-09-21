# Perturbation signal versus technical noise

Compare raw and nuisance-adjusted perturbation signal, preserve replicate-level provenance, and stop when the biological effect is not identifiable. A residual phenotype signal supports analytical triage only; it does not establish mechanism, target engagement, or efficacy.

Write exactly these files under outputs/:
- outputs/signal_noise_report.json: raw effect, adjusted effect, control drift, replicate count, identifiability, decision, rules version, and input SHA-256 values.
- outputs/replicate_diagnostics.tsv: columns perturbation, plate, replicate, raw_signal, adjusted_signal, and control_status.
- outputs/profile_review_gate.md: signal result, technical noise result, human review decision, and the claim boundary that this is not mechanism.
