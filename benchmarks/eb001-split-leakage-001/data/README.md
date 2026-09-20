# Synthetic ADME split fixture

This fixture is a small, frozen calibration dataset for a molecular identity and
scaffold split audit. It is inspired by the public Biogen ADME benchmark entry,
but it is not Biogen internal data and does not support an efficacy or clinical
claim.

The fixture deliberately contains:

- one canonical structure appearing in both train and test;
- one scaffold appearing in both train and test with different structures;
- a salt-stripped identity that must be handled according to the declared policy;
- one missing endpoint value that must not be silently imputed.
