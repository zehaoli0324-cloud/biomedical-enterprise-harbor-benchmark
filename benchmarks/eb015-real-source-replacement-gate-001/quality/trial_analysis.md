# Trial analysis

The first target-model run with `gpt-5.6-sol` wrote all required artifacts and
correctly kept all three sources blocked. The initial verifier rejected only
pre-registered output representations: a shorthand input hash, a per-source
provenance array, and equivalent non-causal wording.

Unchanged artifacts were replayed after the canonical contract registry was
updated. The replay passed with the same blocker set, empty `selected_sources`,
four next actions and bounded claim. This is `RAW_FAIL_CONTRACT_REPLAY_PASS`, not
scientific difficulty evidence and not a model defeat. The task remains blocked
until source rights, file SHA-256 values, verifier rebinding, fixed-container
replay and practitioner review are complete.
