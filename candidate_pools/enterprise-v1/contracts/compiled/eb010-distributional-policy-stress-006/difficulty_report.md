# Difficulty report: eb010-distributional-policy-stress-006

- Title: Distributionally robust adaptive-policy stress test
- Domain: biomedical_enterprise
- Raw score: 4.586/5
- Adjusted score: 5.0/5
- Band: frontier
- Spec digest: `cfbf93e90cb773d1b5ea1c9e9ab6398243c892d1ef53c2e0ba16198b7f390d61`

## Dimensions

| Dimension | Level | Weight | Rationale |
| --- | ---: | ---: | --- |
| `scientific_scenario` | 5 | 1.5 | The task evaluates adaptive experimental policies under multiple plausible cohort distributions. |
| `scientific_judgment` | 5 | 1.5 | Temporal, structural and budget gates precede tail-risk optimization. |
| `computational_difficulty` | 5 | 1.5 | Seventy-two branches feed five weighted distributions, tail integrals, regrets and sensitivity replays. |
| `tool_call_complexity` | 5 | 1 | The agent must reconcile nested inputs with five mutually constrained output artifacts. |
| `retrieval_complexity` | 3 | 1 | All evidence is offline but distributed across a manifest-governed JSON bundle. |
| `information_noise_complexity` | 5 | 1 | The nominal winner and several high-utility invalid policies are explicit distractors. |
| `data_type_complexity` | 4 | 1 | Nested JSON policy graphs feed two relational TSV audits plus JSON and Markdown. |
| `data_complexity` | 5 | 1 | Twelve policies, six scenarios, five distributions and six actions interact. |
| `environment_complexity` | 3 | 1 | Offline deterministic hashes and fixed stage order are required. |
| `mathematical_complexity` | 5 | 1.5 | Weighted fractional lower-tail CVaR, profile regret and lexicographic robust selection are all required. |
| `long_horizon_complexity` | 5 | 1.5 | Complete adaptive trees are replayed under every distribution and every leave-one-profile-out stress test. |
| `safety_risk` | 4 | 1 | Future leakage, missing branches and budget violations cannot be traded for tail utility. |

## Interactions

- `long_horizon_x_tool_orchestration`
- `judgment_x_noisy_evidence`
- `high_stakes_safety_review`

## Selected modules

### horizon
- `horizon_adaptive_policy_replay`: `{}`
- `horizon_two_stage_acquisition`: `{}`
### math
- `math_robust_scenario_optimization`: `{}`
- `math_sensitivity_frontier`: `{}`
- `math_replay_stability`: `{}`
### judgment
- `judgment_blocker_and_abstention`: `{}`
- `judgment_value_of_information`: `{}`
### data
- `data_nested_manifest_join`: `{}`
### tooling
- `tool_branching_pipeline`: `{}`
### noise
- `noise_operational_distractors`: `{}`
### environment
- `environment_offline_setup`: `{}`
### safety
- `safety_human_approval_gate`: `{}`
