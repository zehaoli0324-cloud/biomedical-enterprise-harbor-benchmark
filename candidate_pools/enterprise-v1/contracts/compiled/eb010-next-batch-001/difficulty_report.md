# Difficulty report: eb010-next-batch-001

- Title: Next-batch experimental design under feasibility and budget constraints
- Domain: biomedical_enterprise
- Raw score: 3.24/5
- Adjusted score: 3.44/5
- Band: advanced
- Spec digest: `5e41c6cb14a2658160248653a5114164d84060e99af79169d9577283e5c59085`

## Dimensions

| Dimension | Level | Weight | Rationale |
| --- | ---: | ---: | --- |
| `scientific_scenario` | 4 | 1 | The task requires a legal action under uncertainty and budget, not a retrospective leaderboard ranking. |
| `scientific_judgment` | 5 | 1.5 | The task requires a legal action under uncertainty and budget, not a retrospective leaderboard ranking. |
| `computational_difficulty` | 4 | 1 | The task requires a legal action under uncertainty and budget, not a retrospective leaderboard ranking. |
| `tool_call_complexity` | 2 | 1 | The task requires a legal action under uncertainty and budget, not a retrospective leaderboard ranking. |
| `retrieval_complexity` | 1 | 1 | The task requires a legal action under uncertainty and budget, not a retrospective leaderboard ranking. |
| `information_noise_complexity` | 4 | 1 | The task requires a legal action under uncertainty and budget, not a retrospective leaderboard ranking. |
| `data_type_complexity` | 3 | 1 | The task requires a legal action under uncertainty and budget, not a retrospective leaderboard ranking. |
| `data_complexity` | 3 | 1 | The task requires a legal action under uncertainty and budget, not a retrospective leaderboard ranking. |
| `environment_complexity` | 1 | 1 | The task requires a legal action under uncertainty and budget, not a retrospective leaderboard ranking. |
| `mathematical_complexity` | 5 | 1 | The task requires a legal action under uncertainty and budget, not a retrospective leaderboard ranking. |
| `long_horizon_complexity` | 4 | 1 | The task requires a legal action under uncertainty and budget, not a retrospective leaderboard ranking. |
| `safety_risk` | 2 | 1 | The task requires a legal action under uncertainty and budget, not a retrospective leaderboard ranking. |

## Interactions

- `judgment_x_noisy_evidence`

## Selected modules

### scenario
- `scenario_reproducibility_audit`: `{}`
### judgment
- `judgment_value_of_information`: `{}`
- `judgment_experimental_unit`: `{}`
- `judgment_uncertainty_and_stop_rules`: `{}`
### compute
- `compute_data_schema_discovery`: `{}`
- `compute_multistage_analysis`: `{}`
### noise
- `noise_metadata_conflict`: `{}`
### data
- `data_text_and_metadata`: `{}`
### data_complexity
- `complexity_sparse_or_missing`: `{}`
### environment
- `environment_offline_setup`: `{}`
### math
- `math_batch_acquisition_under_uncertainty`: `{}`
- `math_model_selection_and_sensitivity`: `{}`
- `math_robust_scenario_optimization`: `{}`
- `math_sensitivity_frontier`: `{}`
### horizon
- `horizon_branching_experiments`: `{}`
- `horizon_two_stage_acquisition`: `{}`
### safety
- `safety_human_approval_gate`: `{}`
