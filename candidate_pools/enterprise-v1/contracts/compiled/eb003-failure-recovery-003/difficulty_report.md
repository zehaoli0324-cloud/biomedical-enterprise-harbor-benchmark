# Difficulty report: eb003-failure-recovery-003

- Title: Computational biology tool failure recovery with claim-preserving handoff
- Domain: biomedical_enterprise
- Raw score: 3.75/5
- Adjusted score: 4.3/5
- Band: research-grade
- Spec digest: `840ca2c1ebffefeed7cd9119296a2369ce46170e958ba0ec4de88c4fc5e08657`

## Dimensions

| Dimension | Level | Weight | Rationale |
| --- | ---: | ---: | --- |
| `scientific_scenario` | 4 | 1 | Difficulty comes from preserving state and claim permissions across a failed branch, not from adding more tools. |
| `scientific_judgment` | 5 | 1 | Difficulty comes from preserving state and claim permissions across a failed branch, not from adding more tools. |
| `computational_difficulty` | 4 | 1 | Difficulty comes from preserving state and claim permissions across a failed branch, not from adding more tools. |
| `tool_call_complexity` | 4 | 1 | Difficulty comes from preserving state and claim permissions across a failed branch, not from adding more tools. |
| `retrieval_complexity` | 1 | 1 | Difficulty comes from preserving state and claim permissions across a failed branch, not from adding more tools. |
| `information_noise_complexity` | 4 | 1 | Difficulty comes from preserving state and claim permissions across a failed branch, not from adding more tools. |
| `data_type_complexity` | 4 | 1 | Difficulty comes from preserving state and claim permissions across a failed branch, not from adding more tools. |
| `data_complexity` | 4 | 1 | Difficulty comes from preserving state and claim permissions across a failed branch, not from adding more tools. |
| `environment_complexity` | 4 | 1 | Difficulty comes from preserving state and claim permissions across a failed branch, not from adding more tools. |
| `mathematical_complexity` | 3 | 1 | Difficulty comes from preserving state and claim permissions across a failed branch, not from adding more tools. |
| `long_horizon_complexity` | 5 | 1 | Difficulty comes from preserving state and claim permissions across a failed branch, not from adding more tools. |
| `safety_risk` | 3 | 1 | Difficulty comes from preserving state and claim permissions across a failed branch, not from adding more tools. |

## Interactions

- `long_horizon_x_tool_orchestration`
- `judgment_x_noisy_evidence`
- `data_x_environment`

## Selected modules

### scenario
- `scenario_reproducibility_audit`: `{}`
### judgment
- `judgment_uncertainty_and_stop_rules`: `{}`
- `judgment_causal_boundary`: `{}`
### compute
- `compute_multistage_analysis`: `{}`
- `compute_failure_recovery`: `{}`
### tooling
- `tool_branching_pipeline`: `{}`
- `tool_version_and_interface_drift`: `{}`
- `tool_adversarial_failure`: `{}`
### noise
- `noise_metadata_conflict`: `{}`
### data
- `data_multimodal_join`: `{}`
### data_complexity
- `complexity_sparse_or_missing`: `{}`
### environment
- `environment_pinned_container`: `{}`
- `environment_resource_budget`: `{}`
### math
- `math_model_selection_and_sensitivity`: `{}`
### horizon
- `horizon_checkpointed_workflow`: `{}`
- `horizon_end_to_end_claim`: `{}`
### safety
- `safety_human_approval_gate`: `{}`
