# Observation-conditioned policy audit

The only signal available before stage 2 is the label emitted by the chosen stage-1 request. World IDs and scenarios were not used as signals. Therefore Q1 maps both amber worlds to A6 and both green worlds to A4; the two worlds sharing each label receive exactly the same action.

The selected request is Q1 (cost 1, one hour). The policy uses the common and select families, so their setup is paid once before observation: 1.0 + 1.5 = 2.5 cost and 1 + 2 = 3 slots. Commitment is 3.5, and each branch adds action cost 1 for a worst total of 4.5. Every branch takes 1 + 2 = 3 hours. Stage-1, commitment, capacity, worst-branch total, and deadline budgets all pass.

Using the correlation rule, Q1 and A6 share G1, so coverage is the maximum of their per-axis coverages. Q1 and A4 use different groups, so their coverages add. The replay residuals are W1 (0.15 signal, 0 selectivity), W2 (0.15, 0), W3 (0.15, 0), and W4 (0.13, 0.03). All are within the signal threshold 0.3 and selectivity threshold 0.2. The maximum normalized residual is 0.15 / 0.3 = 0.5.

Enumeration was performed after source, dependency, and observation gates and before resource, time, and threshold gates. Q1 had 49 mappings and 23 eligible policies; its best policy is the selected one. Q2 had 2,401 mappings and 511 eligible policies; its lexically first best policy had risk 0.5 but worst cost 5.5. Q3 had 7 mappings and 1 eligible policy; its best risk was 0.75. The ordered objective therefore selects Q1 first by risk, then by worst branch cost.

Only current, primary-scope sources available by 2026-09-21 and non-future-outcome actions were usable. A8 was excluded as retracted, A9 as future-dated, A10 as pilot scope, and A11 as future-outcome evidence. This is a synthetic planning calculation and supports an executable authorization policy only; it is not experimental proof. The recommendation is marked for human review as required by the output contract.
