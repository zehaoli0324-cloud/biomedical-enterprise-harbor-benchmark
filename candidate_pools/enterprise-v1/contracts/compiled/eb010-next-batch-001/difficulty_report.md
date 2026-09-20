# Difficulty report: eb010-next-batch-001

- Title: Next-batch experimental design under feasibility and budget constraints
- Domain: biomedical_enterprise
- Raw score: 3.417/5
- Adjusted score: 3.617/5
- Band: advanced
- Spec digest: `fb752de5b10a70a576247ed618550bc7bcc6f0b93f2a740e1f5f0fdc138d9eb7`

## Dimensions

| Dimension | Level | Weight | Rationale |
| --- | ---: | ---: | --- |
| `scientific_scenario` | 4 | 1 | The task requires a legal action under uncertainty and budget, not a retrospective leaderboard ranking. |
| `scientific_judgment` | 5 | 1 | The task requires a legal action under uncertainty and budget, not a retrospective leaderboard ranking. |
| `computational_difficulty` | 4 | 1 | The task requires a legal action under uncertainty and budget, not a retrospective leaderboard ranking. |
| `tool_call_complexity` | 2 | 1 | The task requires a legal action under uncertainty and budget, not a retrospective leaderboard ranking. |
| `retrieval_complexity` | 1 | 1 | The task requires a legal action under uncertainty and budget, not a retrospective leaderboard ranking. |
| `information_noise_complexity` | 4 | 1 | The task requires a legal action under uncertainty and budget, not a retrospective leaderboard ranking. |
| `data_type_complexity` | 3 | 1 | The task requires a legal action under uncertainty and budget, not a retrospective leaderboard ranking. |
| `data_complexity` | 4 | 1 | The task requires a legal action under uncertainty and budget, not a retrospective leaderboard ranking. |
| `environment_complexity` | 2 | 1 | The task requires a legal action under uncertainty and budget, not a retrospective leaderboard ranking. |
| `mathematical_complexity` | 4 | 1 | The task requires a legal action under uncertainty and budget, not a retrospective leaderboard ranking. |
| `long_horizon_complexity` | 5 | 1 | The task requires a legal action under uncertainty and budget, not a retrospective leaderboard ranking. |
| `safety_risk` | 3 | 1 | The task requires a legal action under uncertainty and budget, not a retrospective leaderboard ranking. |

## Interactions

- `judgment_x_noisy_evidence`

## Selected modules

### scenario
- `scenario_reproducibility_audit`: `{}`
### judgment
- `judgment_experimental_unit`: `{}`
- `judgment_uncertainty_and_stop_rules`: `{}`
### compute
- `compute_data_schema_discovery`: `{}`
- `compute_multistage_analysis`: `{}`
### noise
- `noise_metadata_conflict`: `{}`
- `noise_missing_and_duplicate_inputs`: `{}`
### data
- `data_text_and_metadata`: `{}`
### data_complexity
- `complexity_replicates_and_batches`: `{}`
- `complexity_sparse_or_missing`: `{}`
### environment
- `environment_offline_setup`: `{}`
- `environment_resource_budget`: `{}`
### math
- `math_model_selection_and_sensitivity`: `{}`
### horizon
- `horizon_branching_experiments`: `{}`
- `horizon_end_to_end_claim`: `{}`
### safety
- `safety_human_approval_gate`: `{}`
