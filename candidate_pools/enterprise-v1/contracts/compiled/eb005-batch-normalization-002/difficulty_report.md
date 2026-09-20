# Difficulty report: eb005-batch-normalization-002

- Title: Cell Painting normalization choice under controlled batch confounding
- Domain: biomedical_enterprise
- Raw score: 3.5/5
- Adjusted score: 3.7/5
- Band: advanced
- Spec digest: `e4dec3ae40a32c40c63f089717ebdd36bfa078a65df4911193b7889cc16f81a7`

## Dimensions

| Dimension | Level | Weight | Rationale |
| --- | ---: | ---: | --- |
| `scientific_scenario` | 5 | 1 | The agent must compare competing preprocessing branches and distinguish a stable phenotype from a batch artifact. |
| `scientific_judgment` | 5 | 1 | The agent must compare competing preprocessing branches and distinguish a stable phenotype from a batch artifact. |
| `computational_difficulty` | 4 | 1 | The agent must compare competing preprocessing branches and distinguish a stable phenotype from a batch artifact. |
| `tool_call_complexity` | 2 | 1 | The agent must compare competing preprocessing branches and distinguish a stable phenotype from a batch artifact. |
| `retrieval_complexity` | 1 | 1 | The agent must compare competing preprocessing branches and distinguish a stable phenotype from a batch artifact. |
| `information_noise_complexity` | 5 | 1 | The agent must compare competing preprocessing branches and distinguish a stable phenotype from a batch artifact. |
| `data_type_complexity` | 4 | 1 | The agent must compare competing preprocessing branches and distinguish a stable phenotype from a batch artifact. |
| `data_complexity` | 4 | 1 | The agent must compare competing preprocessing branches and distinguish a stable phenotype from a batch artifact. |
| `environment_complexity` | 1 | 1 | The agent must compare competing preprocessing branches and distinguish a stable phenotype from a batch artifact. |
| `mathematical_complexity` | 4 | 1 | The agent must compare competing preprocessing branches and distinguish a stable phenotype from a batch artifact. |
| `long_horizon_complexity` | 4 | 1 | The agent must compare competing preprocessing branches and distinguish a stable phenotype from a batch artifact. |
| `safety_risk` | 3 | 1 | The agent must compare competing preprocessing branches and distinguish a stable phenotype from a batch artifact. |

## Interactions

- `judgment_x_noisy_evidence`

## Selected modules

### scenario
- `scenario_omics_analysis`: `{}`
### judgment
- `judgment_experimental_unit`: `{}`
- `judgment_uncertainty_and_stop_rules`: `{}`
- `judgment_causal_boundary`: `{}`
### compute
- `compute_multistage_analysis`: `{}`
### noise
- `noise_metadata_conflict`: `{}`
- `noise_missing_and_duplicate_inputs`: `{}`
### data
- `data_images_and_structures`: `{}`
- `data_text_and_metadata`: `{}`
### data_complexity
- `complexity_replicates_and_batches`: `{}`
- `complexity_sparse_or_missing`: `{}`
### environment
- `environment_offline_setup`: `{}`
### math
- `math_model_selection_and_sensitivity`: `{}`
- `math_statistics_and_multiple_testing`: `{}`
### horizon
- `horizon_checkpointed_workflow`: `{}`
- `horizon_end_to_end_claim`: `{}`
### safety
- `safety_human_approval_gate`: `{}`
