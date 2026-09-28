# Difficulty report: eb009-diversity-coverage-004

- Title: Generated candidate diversity and scaffold coverage
- Domain: biomedical_enterprise
- Raw score: 2.833/5
- Adjusted score: 3.033/5
- Band: advanced
- Spec digest: `90c091329aa7df41d418948f543972b9bb41919053192be65d85964a05742742`

## Dimensions

| Dimension | Level | Weight | Rationale |
| --- | ---: | ---: | --- |
| `scientific_scenario` | 4 | 1 | The decision is whether a generated set covers the intended chemical space before synthesis review. |
| `scientific_judgment` | 5 | 1 | Objective score must be separated from scaffold and cluster coverage. |
| `computational_difficulty` | 3 | 1 | The task joins validity, scaffold and cluster records. |
| `tool_call_complexity` | 2 | 1 | The challenge is audit reasoning, not tool count. |
| `retrieval_complexity` | 1 | 1 | All evidence is in the frozen offline bundle. |
| `information_noise_complexity` | 4 | 1 | Invalid identifiers, collapsed clusters and threshold-sensitive coverage create competing evidence paths. |
| `data_type_complexity` | 3 | 1 | CSV candidate rows and JSON rules require reconciliation. |
| `data_complexity` | 2 | 1 | The fixture is small but contains a collapsed cluster and invalid row. |
| `environment_complexity` | 2 | 1 | The offline environment is fixed and deterministic. |
| `mathematical_complexity` | 2 | 1 | Coverage thresholds are simple but must be applied to valid candidates only. |
| `long_horizon_complexity` | 3 | 1 | The handoff links generation, diversity audit and human review. |
| `safety_risk` | 3 | 1 | Computed diversity is not biological activity or developability. |

## Interactions

- `judgment_x_noisy_evidence`

## Selected modules

### scenario
- `scenario_reproducibility_audit`: `{}`
### judgment
- `judgment_uncertainty_and_stop_rules`: `{}`
- `judgment_causal_boundary`: `{}`
- `judgment_blocker_and_abstention`: `{}`
### compute
- `compute_multistage_analysis`: `{}`
### tooling
- `tool_branching_pipeline`: `{}`
### noise
- `noise_metadata_conflict`: `{}`
### data
- `data_multimodal_join`: `{}`
- `data_evidence_graph_join`: `{}`
### data_complexity
- `complexity_sparse_or_missing`: `{}`
### environment
- `environment_pinned_container`: `{}`
### math
- `math_model_selection_and_sensitivity`: `{}`
- `math_sensitivity_frontier`: `{}`
### horizon
- `horizon_checkpointed_workflow`: `{}`
### safety
- `safety_human_approval_gate`: `{}`
