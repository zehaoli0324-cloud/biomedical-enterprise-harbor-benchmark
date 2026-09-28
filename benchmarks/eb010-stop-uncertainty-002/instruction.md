# Adaptive stop-rule evidence routing under uncertainty

Use only the supplied nested JSON bundle. Choose a stage-1 request before observing its declared outcome. After that observation, choose exactly one dependency-valid stage-2 request allowed for that observation. The stage-1 cost plus the largest stage-2 cost must remain within the total budget. Ignore archived requests, future outcomes, and requests with missing prerequisites.

The trial workspace is not a git repository. Do not run git commands, inspect parent directories, or search outside `data/`; use shell commands only to read the supplied files and write the five required artifacts.

For every observation state, subtract the stage-1 and selected stage-2 reductions plus the declared observation adjustment. Within one correlation group, only the largest reduction per uncertainty counts. A policy is eligible only if every observation state reaches every critical threshold. Select the eligible policy by lowest worst-case maximum critical residual, then lowest worst-case cost, then lexical stage-1 request ID and stage-2 mapping. A simulated stop policy is a planning aid, not proof of real-world improvement.

Write exactly `outputs/plan.json`, `outputs/route.tsv`, `outputs/decision.json`, `outputs/provenance.json`, and `outputs/audit.md`. Include `stage1_request_id`, `stage2_policy`, `worst_case_max_critical_residual`, `worst_case_cost`, and complete `policies`. `route.tsv` must contain one row per policy state. Record all input SHA-256 values, the rules version, `network="off"`, and `deterministic=true`. The audit must explain observation gating, stages, dependencies, budget, future-outcome exclusion, human review, and why the result is not experimental proof.
