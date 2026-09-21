# Difficulty report: eb003-failure-recovery-003

- Title: Computational biology tool failure recovery with claim-preserving handoff
- Domain: biomedical_enterprise
- Raw score: 3.16/5
- Adjusted score: 3.36/5
- Band: advanced
- Spec digest: `6a266b175debba24ee42ccf970706cfc13b59dca8fc73af0131af1752ffed422`

## Dimensions

| Dimension | Level | Weight | Rationale |
| --- | ---: | ---: | --- |
| `scientific_scenario` | 3 | 1 | Difficulty comes from preserving state and claim permissions across a failed branch, not from adding more tools. |
| `scientific_judgment` | 5 | 1.5 | Difficulty comes from preserving state and claim permissions across a failed branch, not from adding more tools. |
| `computational_difficulty` | 4 | 1 | Difficulty comes from preserving state and claim permissions across a failed branch, not from adding more tools. |
| `tool_call_complexity` | 3 | 1 | Difficulty comes from preserving state and claim permissions across a failed branch, not from adding more tools. |
| `retrieval_complexity` | 1 | 1 | Difficulty comes from preserving state and claim permissions across a failed branch, not from adding more tools. |
| `information_noise_complexity` | 4 | 1 | Difficulty comes from preserving state and claim permissions across a failed branch, not from adding more tools. |
| `data_type_complexity` | 3 | 1 | Difficulty comes from preserving state and claim permissions across a failed branch, not from adding more tools. |
| `data_complexity` | 2 | 1 | Difficulty comes from preserving state and claim permissions across a failed branch, not from adding more tools. |
| `environment_complexity` | 2 | 1 | Difficulty comes from preserving state and claim permissions across a failed branch, not from adding more tools. |
| `mathematical_complexity` | 3 | 1 | Difficulty comes from preserving state and claim permissions across a failed branch, not from adding more tools. |
| `long_horizon_complexity` | 4 | 1 | Difficulty comes from preserving state and claim permissions across a failed branch, not from adding more tools. |
| `safety_risk` | 3 | 1 | Difficulty comes from preserving state and claim permissions across a failed branch, not from adding more tools. |

## Interactions

- `judgment_x_noisy_evidence`

## Selected modules

### scenario
- `scenario_reproducibility_audit`: `{}`
### judgment
- `judgment_claim_preserving_recovery`: `{}`
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
- `data_text_and_metadata`: `{}`
### data_complexity
- `complexity_sparse_or_missing`: `{}`
### environment
- `environment_offline_setup`: `{}`
### math
- `math_model_selection_and_sensitivity`: `{}`
### horizon
- `horizon_checkpointed_workflow`: `{}`
- `horizon_end_to_end_claim`: `{}`
### safety
- `safety_human_approval_gate`: `{}`
