# EB013-002 repaired-contract trial analysis

The `gpt-5.6-sol` process trial passed the hidden verifier on its raw artifacts. It selected `R-ADAPTIVE` and routed `signal_high -> R-SELECT`, `signal_low -> R-CORR`, and `signal_mid -> R-BALANCE`; worst-case critical residual was `0.25` and cost was `5.0`.

The trial produced complete policy replay, a real-tab route table covering all nine states, and exact hashes for all five visible JSON inputs. This is valid local calibration evidence, but not release evidence until Docker/Harbor replay and practitioner review are complete.
