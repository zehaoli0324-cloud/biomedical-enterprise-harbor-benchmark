# Difficulty report: eb003-replay-provenance-004

- Title: Computational artifact replay from provenance
- Domain: biomedical_enterprise
- Raw score: 2.917/5
- Adjusted score: 3.117/5
- Band: advanced
- Spec digest: `e2166717b3f7fd7a5e9252bb7802321deac98cc84fd0c049e940ffae0c110d09`

## Dimensions

| Dimension | Level | Weight | Rationale |
| --- | ---: | ---: | --- |
| `scientific_scenario` | 4 | 1 | The decision is whether a delivered artifact can be reproduced after handoff. |
| `scientific_judgment` | 5 | 1 | Checksum, environment and rerun evidence must be reconciled before approval. |
| `computational_difficulty` | 3 | 1 | The task compares linked artifact and environment records. |
| `tool_call_complexity` | 2 | 1 | The challenge is evidence reconciliation, not tool count. |
| `retrieval_complexity` | 1 | 1 | All evidence is in the frozen offline bundle. |
| `information_noise_complexity` | 4 | 1 | Conflicting provenance edges, stale versions and duplicate replay evidence can change the permission decision. |
| `data_type_complexity` | 3 | 1 | Structured JSON records require cross-file joins. |
| `data_complexity` | 2 | 1 | The fixture is small but linked. |
| `environment_complexity` | 4 | 1 | Environment pinning is itself part of the decision. |
| `mathematical_complexity` | 1 | 1 | No complex numerical method is required. |
| `long_horizon_complexity` | 3 | 1 | The handoff links artifact, environment and replay records. |
| `safety_risk` | 3 | 1 | Unreproducible evidence must not be presented as biological validation. |

## Interactions

- `judgment_x_noisy_evidence`

## Selected modules

### scenario
- `scenario_reproducibility_audit`: `{}`
### judgment
- `judgment_uncertainty_and_stop_rules`: `{}`
- `judgment_causal_boundary`: `{}`
- `judgment_claim_permission_lattice`: `{}`
### compute
- `compute_multistage_analysis`: `{}`
### tooling
- `tool_version_and_interface_drift`: `{}`
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
### horizon
- `horizon_checkpointed_workflow`: `{}`
- `horizon_end_to_end_claim`: `{}`
### safety
- `safety_human_approval_gate`: `{}`
