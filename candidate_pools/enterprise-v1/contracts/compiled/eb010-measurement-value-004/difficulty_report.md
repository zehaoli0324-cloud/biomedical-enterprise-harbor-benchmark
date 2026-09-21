# Difficulty report: eb010-measurement-value-004

- Title: Decision-critical measurement prioritization
- Domain: biomedical_enterprise
- Raw score: 3.083/5
- Adjusted score: 3.283/5
- Band: advanced
- Spec digest: `ef49ff8081c580d48626d4375023821402587857fbf21257eea68623894e4213`

## Dimensions

| Dimension | Level | Weight | Rationale |
| --- | ---: | ---: | --- |
| `scientific_scenario` | 4 | 1 | The task chooses one additional measurement before the next experimental batch. |
| `scientific_judgment` | 5 | 1 | Eligibility, uncertainty reduction, redundancy, cost, and evidence visibility must be reconciled. |
| `computational_difficulty` | 3 | 1 | The agent computes and ranks information value for all options under explicit constraints. |
| `tool_call_complexity` | 2 | 1 | The challenge is disciplined evidence reconciliation rather than tool breadth. |
| `retrieval_complexity` | 1 | 1 | All evidence is contained in the frozen offline bundle. |
| `information_noise_complexity` | 5 | 1 | High apparent gains include correlated, infeasible, observed, and future-leaking distractors. |
| `data_type_complexity` | 3 | 1 | CSV options and JSON rules feed TSV, JSON, and Markdown deliverables. |
| `data_complexity` | 3 | 1 | Several candidate states and measurement constraints must be evaluated jointly. |
| `environment_complexity` | 2 | 1 | The environment is offline and deterministic. |
| `mathematical_complexity` | 3 | 1 | The score combines uncertainty, sensitivity, variance reduction, correlation, and cost. |
| `long_horizon_complexity` | 3 | 1 | The artifact hands an optimization state into a reviewed measurement request before batching. |
| `safety_risk` | 3 | 1 | A planning score must not be represented as evidence of experimental improvement. |

## Interactions

- `judgment_x_noisy_evidence`

## Selected modules

### scenario
- `scenario_reproducibility_audit`: `{}`
### judgment
- `judgment_uncertainty_and_stop_rules`: `{}`
- `judgment_causal_boundary`: `{}`
### compute
- `compute_multistage_analysis`: `{}`
### tooling
- `tool_branching_pipeline`: `{}`
### noise
- `noise_metadata_conflict`: `{}`
### data
- `data_multimodal_join`: `{}`
### data_complexity
- `complexity_sparse_or_missing`: `{}`
### environment
- `environment_pinned_container`: `{}`
### math
- `math_model_selection_and_sensitivity`: `{}`
### horizon
- `horizon_checkpointed_workflow`: `{}`
### safety
- `safety_human_approval_gate`: `{}`
