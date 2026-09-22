# Target-model trial analysis

`gpt-5.6-sol` completed `trial-gpt56-sol-001` with exit code 0 and produced all four required artifacts. It recursively discovered the nested inputs, reconstructed the lexicon and rules, selected `P-ALPHA`, sent `P-BETA` and `P-GAMMA` to human review, rejected `P-DELTA` for future-outcome leakage, and excluded `P-ARCHIVE` by scope.

The strict first verifier run failed with 39 messages. They were cascades from representation mismatches: the model used a record list instead of an ID-keyed object, `eligibility` instead of `eligible`, more specific semantic/blocker labels, `data/`-prefixed discovery paths, and the structured claim-boundary token instead of repeating the prose phrase. No scientific decision was wrong.

The verifier now canonicalizes those documented semantic equivalents. The original artifacts, identified by hashes in `target_trial_evidence.json`, pass unchanged replay with zero errors. This trial therefore demonstrates one successful solution of the L5.1 reasoning chain, not that the model was defeated. It also does not establish release readiness: fixed-container replay, repeated sampling and practitioner review remain open.

## Contract v0.6.1 rerun

After the SOP repair, the second run used the explicit equivalence contract. It passed `rules_version`, keyed records, eligibility naming, semantic blocker fields and discovery provenance on the first attempt. The only initial mismatches were two valid encodings of scope/future exclusion (`unresolved` plus an explicit blocker) and a stability explanation using `stable`/replay-range language. The verifier contract now declares and tests those equivalents; the unchanged v0.6.1 artifacts replay with zero errors. The remaining work is fixed-container replay and repeated held-out variants, not another round of hidden schema tightening.

`trial-gpt56-sol-003` then exercised the frozen v0.6.1 contract from a fresh workspace. It passed the runner verifier on the first attempt with agent and verifier exit codes 0 and no timeout. This is the first clean trial result after the SOP-level prevention rules were applied.
