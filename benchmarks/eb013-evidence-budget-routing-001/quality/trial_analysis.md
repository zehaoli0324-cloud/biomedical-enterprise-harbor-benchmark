# EB013 target trial analysis

The `gpt-5.6-sol` agent completed in 574.5 seconds with exit code 0 and produced all five required artifacts. The runner's original verifier rejected the submission with 20 errors. A v0.1.1 contract replay that accepts documented semantic aliases and explanatory exclusion text reduced this to eight errors without changing any model artifact.

The model correctly discovered the nested manifest, stayed offline, preserved current-versus-archived and future-outcome boundaries, identified dependencies, computed the `R-ASSAY` residuals, and recorded all seven requests. The decisive error was route optimization: it stopped at `R-ASSAY` because that request alone crossed both thresholds. It did not compare the maximum critical residual against `R-ASSAY + R-CORR`; the latter uses cost 4 and lowers the maximum residual from 0.20 to 0.15. This is a scientific objective/route-selection failure, not a provenance or artifact-completeness failure.

The first verifier contract was too strict about field aliases (`sha256`, `network_state`, `residual_uncertainty_map`) and exact blocker wording. Those checks were widened in v0.1.1 and covered by an alias regression test. The unchanged artifact still fails on the route decision, so the trial is retained as valid difficulty evidence.
