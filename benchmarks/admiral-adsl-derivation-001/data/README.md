# Synthetic SDTM input fixture

This fixture is a small, frozen calibration input for an SDTM-to-ADSL derivation task.
It is inspired by the public pharmaverse admiral workflow, but it is not sponsor data,
patient data, or evidence of a clinical result.

The input contains six synthetic subjects and deliberately exposes four rule boundaries:

- a screen-failure subject that is not randomized;
- a randomized subject with no exposure record;
- a randomized, treated subject with a missing end-of-study date;
- a treated subject whose exposure extends beyond the analysis cutoff.

The task is offline. The agent must record checksums for both CSV files and the frozen
rule file in `outputs/run_manifest.json`.
