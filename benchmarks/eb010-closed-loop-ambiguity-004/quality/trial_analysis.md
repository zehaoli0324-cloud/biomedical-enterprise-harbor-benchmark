# Target-model trial analysis

`gpt-5.6-sol` completed `trial-gpt56-sol-001` with exit code 0 and produced all four required artifacts. It recursively discovered the nested inputs, reconstructed the lexicon and rules, selected `P-ALPHA`, sent `P-BETA` and `P-GAMMA` to human review, rejected `P-DELTA` for future-outcome leakage, and excluded `P-ARCHIVE` by scope.

The strict first verifier run failed with 39 messages. They were cascades from representation mismatches: the model used a record list instead of an ID-keyed object, `eligibility` instead of `eligible`, more specific semantic/blocker labels, `data/`-prefixed discovery paths, and the structured claim-boundary token instead of repeating the prose phrase. No scientific decision was wrong.

The verifier now canonicalizes those documented semantic equivalents. The original artifacts, identified by hashes in `target_trial_evidence.json`, pass unchanged replay with zero errors. This trial therefore demonstrates one successful solution of the L5.1 reasoning chain, not that the model was defeated. It also does not establish release readiness: fixed-container replay, repeated sampling and practitioner review remain open.

## Contract v0.6.1 rerun

After the SOP repair, the second run used the explicit equivalence contract. It passed `rules_version`, keyed records, eligibility naming, semantic blocker fields and discovery provenance on the first attempt. The only initial mismatches were two valid encodings of scope/future exclusion (`unresolved` plus an explicit blocker) and a stability explanation using `stable`/replay-range language. The verifier contract now declares and tests those equivalents; the unchanged v0.6.1 artifacts replay with zero errors. The remaining work is fixed-container replay and repeated held-out variants, not another round of hidden schema tightening.

`trial-gpt56-sol-003` then exercised the frozen v0.6.1 contract from a fresh workspace. It passed the runner verifier on the first attempt with agent and verifier exit codes 0 and no timeout. This is the first clean trial result after the SOP-level prevention rules were applied.

## Contract v0.7.0 self-planning rerun

The v0.7.0 run added a mission and operation catalog and required the agent to choose a dependency-valid workflow. `trial-gpt56-sol-004` passed on the first verifier execution. Its plan covered `inventory`, `interpret`, `screen`, `replay` and `decide` exactly once, respected all dependencies, used no network, stayed within the planning budget, and stopped after selecting an eligible record. This is a clean first-pass solvability result for the new planning layer, not a claim of target-model discrimination.

## Contract v0.7.1 capability-subgraph trial

v0.7.1 removed the fixed required operation list and exposed only required capabilities. The operation catalog included label-only, partial-replay, network and blanket-defer shortcuts. `trial-gpt56-sol-005` still passed on the first verifier execution, selecting the complete offline subgraph `inventory -> interpret -> screen -> replay -> decide` and avoiding all four shortcuts. This is evidence that the task is solvable with autonomous workflow planning; held-out variants and repeated trials are still needed before claiming discrimination.

## Contract v0.8.0 data expansion

The fixture now contains 22 policy records. Added records cover inclusive signal,
uncertainty, budget and replay-spread boundaries, plus independent semantic,
scope, future-outcome, uncertainty, signal, budget and stability blockers. The
previous trial artifacts are superseded because the derived selection is now
`P-OMICRON`; recalibration is required before retaining any model-trial claim.
