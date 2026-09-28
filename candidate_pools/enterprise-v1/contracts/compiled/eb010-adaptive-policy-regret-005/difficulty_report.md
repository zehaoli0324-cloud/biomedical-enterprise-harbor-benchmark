# Difficulty report: eb010-adaptive-policy-regret-005

- Title: Adaptive policy tree selection by minimax regret
- Domain: biomedical_enterprise
- Raw score: 4.517/5
- Adjusted score: 5.0/5
- Band: frontier
- Spec digest: `ca0346d58d30c21e1b301de8db989fcd68962abda36551339d18b68dca4b2c14`

## Dimensions

| Dimension | Level | Weight | Rationale |
| --- | ---: | ---: | --- |
| `scientific_scenario` | 5 | 1.5 | The task evaluates complete adaptive experimental policies across latent scenarios. |
| `scientific_judgment` | 5 | 1.5 | Structural, temporal and budget gates precede robust policy ranking. |
| `computational_difficulty` | 5 | 1.5 | Every policy branch is replayed before constructing a scenario-wise regret oracle. |
| `tool_call_complexity` | 4 | 1 | The agent must reconcile five input artifacts and four output artifacts. |
| `retrieval_complexity` | 3 | 1 | All evidence is offline but distributed across nested files. |
| `information_noise_complexity` | 5 | 1 | High-mean, high-single-state, future-leaking and over-budget policies are plausible distractors. |
| `data_type_complexity` | 4 | 1 | Nested JSON policy graphs feed JSON, TSV and Markdown outputs. |
| `data_complexity` | 5 | 1 | Ten policies, four scenarios, three observations and five actions interact. |
| `environment_complexity` | 3 | 1 | Offline deterministic hashes and stage order are required. |
| `mathematical_complexity` | 5 | 1.5 | The answer requires scenario oracles, regret vectors and multi-level tie-breaking. |
| `long_horizon_complexity` | 5 | 1.5 | Observation-conditioned actions form complete policy trees with temporal visibility constraints. |
| `safety_risk` | 4 | 1 | Future leakage and budget violations cannot be traded for utility. |

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
