# EB013-002 target trial analysis

The v0.2 target trial passed scientific verification after contract replay. Version 0.3 added a third observable state, `signal_mid`, whose legal action is `R-BALANCE`.

In v0.3 trial `gpt56sol-002`, the model selected all three correct branches, but omitted the required `run_manifest.json` hash; canonical replay therefore remains a provenance delivery failure. In `gpt56sol-003`, after the four required hashes were explicitly enumerated, the model again selected the correct three-state policy and supplied complete provenance. Its raw verifier failure was limited to the declared aliases `observation_state` and `critical_residual_max`; unchanged-artifact replay passed.

The increased scientific difficulty did not defeat gpt-5.6-sol in trial `trial-gpt56-sol-20260922-004`: it selected the correct three-state policy and enumerated `R-FIXED` as an incomplete policy, exposing a verifier contract gap. After verifier repair, unchanged-artifact replay passed. The first clean post-contract-freeze rerun (`trial-gpt56-sol-20260922-005`) timed out after 600 seconds before producing outputs. This is a runtime/model interaction failure, not a scientific decision failure; release remains blocked pending a successful clean target-model rerun and practitioner review.
