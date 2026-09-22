# EB013-002 target trial analysis

The v0.2 target trial passed scientific verification after contract replay. Version 0.3 added a third observable state, `signal_mid`, whose legal action is `R-BALANCE`.

In v0.3 trial `gpt56sol-002`, the model selected all three correct branches, but omitted the required `run_manifest.json` hash; canonical replay therefore remains a provenance delivery failure. In `gpt56sol-003`, after the four required hashes were explicitly enumerated, the model again selected the correct three-state policy and supplied complete provenance. Its raw verifier failure was limited to the declared aliases `observation_state` and `critical_residual_max`; unchanged-artifact replay passed.

The increased scientific difficulty did not defeat gpt-5.6-sol. Release remains blocked pending fixed-container replay and practitioner review.
