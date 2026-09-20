# Difficulty report: eb001-split-leakage-001

- Title: Molecular identity and scaffold leakage audit before ADME model comparison
- Domain: biomedical_enterprise
- Raw score: 2.583/5
- Adjusted score: 2.783/5
- Band: intermediate
- Spec digest: `87f51f755a536ccdd48f46cd5bea0dd9c6ea5ccf64c665eea3179f0a0a02131a`

## Dimensions

| Dimension | Level | Weight | Rationale |
| --- | ---: | ---: | --- |
| `scientific_scenario` | 4 | 1 | The model can compute overlap easily but must first choose the independent unit and stop when identity rules are unresolved. |
| `scientific_judgment` | 4 | 1 | The model can compute overlap easily but must first choose the independent unit and stop when identity rules are unresolved. |
| `computational_difficulty` | 3 | 1 | The model can compute overlap easily but must first choose the independent unit and stop when identity rules are unresolved. |
| `tool_call_complexity` | 1 | 1 | The model can compute overlap easily but must first choose the independent unit and stop when identity rules are unresolved. |
| `retrieval_complexity` | 1 | 1 | The model can compute overlap easily but must first choose the independent unit and stop when identity rules are unresolved. |
| `information_noise_complexity` | 4 | 1 | The model can compute overlap easily but must first choose the independent unit and stop when identity rules are unresolved. |
| `data_type_complexity` | 3 | 1 | The model can compute overlap easily but must first choose the independent unit and stop when identity rules are unresolved. |
| `data_complexity` | 3 | 1 | The model can compute overlap easily but must first choose the independent unit and stop when identity rules are unresolved. |
| `environment_complexity` | 1 | 1 | The model can compute overlap easily but must first choose the independent unit and stop when identity rules are unresolved. |
| `mathematical_complexity` | 2 | 1 | The model can compute overlap easily but must first choose the independent unit and stop when identity rules are unresolved. |
| `long_horizon_complexity` | 3 | 1 | The model can compute overlap easily but must first choose the independent unit and stop when identity rules are unresolved. |
| `safety_risk` | 2 | 1 | The model can compute overlap easily but must first choose the independent unit and stop when identity rules are unresolved. |

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
### noise
- `noise_metadata_conflict`: `{}`
- `noise_missing_and_duplicate_inputs`: `{}`
### data
- `data_text_and_metadata`: `{}`
### data_complexity
- `complexity_replicates_and_batches`: `{}`
### environment
- `environment_offline_setup`: `{}`
### math
- `math_model_selection_and_sensitivity`: `{}`
### horizon
- `horizon_checkpointed_workflow`: `{}`
### safety
- `safety_human_approval_gate`: `{}`
