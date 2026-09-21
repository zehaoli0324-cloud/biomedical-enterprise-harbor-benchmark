# Difficulty report: eb005-batch-normalization-002

- Title: Cell Painting normalization choice under controlled batch confounding
- Domain: biomedical_enterprise
- Raw score: 3.24/5
- Adjusted score: 3.44/5
- Band: advanced
- Spec digest: `7340b5a39e7a05591f68279a32b5c090ae9611a51c8851fa8c36b7b6326f2c18`

## Dimensions

| Dimension | Level | Weight | Rationale |
| --- | ---: | ---: | --- |
| `scientific_scenario` | 4 | 1 | The agent must compare competing preprocessing branches and distinguish a stable phenotype from a batch artifact. |
| `scientific_judgment` | 5 | 1.5 | The agent must compare competing preprocessing branches and distinguish a stable phenotype from a batch artifact. |
| `computational_difficulty` | 4 | 1 | The agent must compare competing preprocessing branches and distinguish a stable phenotype from a batch artifact. |
| `tool_call_complexity` | 1 | 1 | The agent must compare competing preprocessing branches and distinguish a stable phenotype from a batch artifact. |
| `retrieval_complexity` | 1 | 1 | The agent must compare competing preprocessing branches and distinguish a stable phenotype from a batch artifact. |
| `information_noise_complexity` | 5 | 1 | The agent must compare competing preprocessing branches and distinguish a stable phenotype from a batch artifact. |
| `data_type_complexity` | 3 | 1 | The agent must compare competing preprocessing branches and distinguish a stable phenotype from a batch artifact. |
| `data_complexity` | 4 | 1 | The agent must compare competing preprocessing branches and distinguish a stable phenotype from a batch artifact. |
| `environment_complexity` | 1 | 1 | The agent must compare competing preprocessing branches and distinguish a stable phenotype from a batch artifact. |
| `mathematical_complexity` | 4 | 1 | The agent must compare competing preprocessing branches and distinguish a stable phenotype from a batch artifact. |
| `long_horizon_complexity` | 4 | 1 | The agent must compare competing preprocessing branches and distinguish a stable phenotype from a batch artifact. |
| `safety_risk` | 2 | 1 | The agent must compare competing preprocessing branches and distinguish a stable phenotype from a batch artifact. |

## Interactions

- `judgment_x_noisy_evidence`

## Selected modules

### scenario
- `scenario_omics_analysis`: `{}`
### judgment
- `judgment_batch_identifiability`: `{}`
- `judgment_experimental_unit`: `{}`
- `judgment_uncertainty_and_stop_rules`: `{}`
- `judgment_causal_boundary`: `{}`
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
### environment
- `environment_offline_setup`: `{}`
### math
- `math_hierarchical_batch_sensitivity`: `{}`
- `math_model_selection_and_sensitivity`: `{}`
### horizon
- `horizon_checkpointed_workflow`: `{}`
### safety
- `safety_human_approval_gate`: `{}`
