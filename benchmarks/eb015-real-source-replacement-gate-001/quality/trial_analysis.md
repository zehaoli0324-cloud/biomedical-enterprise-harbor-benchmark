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

The contract-repaired trial `eb015-real-source-gpt56sol-004` then passed directly
in 316.29 seconds with agent exit code 0 and no verifier errors. This confirms the
repair but also shows that the current version does not defeat the target model;
additional difficulty must come from substantive source reconciliation rather
than stricter output wording.
