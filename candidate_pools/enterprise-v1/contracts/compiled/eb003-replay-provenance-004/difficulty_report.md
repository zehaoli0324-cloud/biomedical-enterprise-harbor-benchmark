# Difficulty report: eb003-replay-provenance-004

- Title: Computational artifact replay from provenance
- Domain: biomedical_enterprise
- Raw score: 2.833/5
- Adjusted score: 2.833/5
- Band: intermediate
- Spec digest: `0c9c1bc4076a053312bf6caa02ecf69e25ba18ec83034f5cfdf80b23aaec910a`

## Dimensions

| Dimension | Level | Weight | Rationale |
| --- | ---: | ---: | --- |
| `scientific_scenario` | 4 | 1 | The decision is whether a delivered artifact can be reproduced after handoff. |
| `scientific_judgment` | 5 | 1 | Checksum, environment and rerun evidence must be reconciled before approval. |
| `computational_difficulty` | 3 | 1 | The task compares linked artifact and environment records. |
| `tool_call_complexity` | 2 | 1 | The challenge is evidence reconciliation, not tool count. |
| `retrieval_complexity` | 1 | 1 | All evidence is in the frozen offline bundle. |
| `information_noise_complexity` | 3 | 1 | Version and checksum differences are plausible but bounded. |
| `data_type_complexity` | 3 | 1 | Structured JSON records require cross-file joins. |
| `data_complexity` | 2 | 1 | The fixture is small but linked. |
| `environment_complexity` | 4 | 1 | Environment pinning is itself part of the decision. |
| `mathematical_complexity` | 1 | 1 | No complex numerical method is required. |
| `long_horizon_complexity` | 3 | 1 | The handoff links artifact, environment and replay records. |
| `safety_risk` | 3 | 1 | Unreproducible evidence must not be presented as biological validation. |

## Interactions

- None

## Selected modules

### scenario
- `scenario_reproducibility_audit`: `{}`
### judgment
- `judgment_uncertainty_and_stop_rules`: `{}`
- `judgment_causal_boundary`: `{}`
### compute
- `compute_multistage_analysis`: `{}`
### tooling
- `tool_version_and_interface_drift`: `{}`
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
