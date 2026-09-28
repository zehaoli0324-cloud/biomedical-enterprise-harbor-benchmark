# Difficulty report: eb012-revocation-portfolio-003

- Title: Revocation-aware cross-stage portfolio replay
- Domain: biomedical_enterprise
- Raw score: 4.5/5
- Adjusted score: 5.0/5
- Band: frontier
- Spec digest: `53e74b9776a39fcb67419e95bafdc5ef98984eef34a29d692d4fcd7b813de8fe`

## Dimensions

| Dimension | Level | Weight | Rationale |
| --- | ---: | ---: | --- |
| `scientific_scenario` | 5 | 1.5 | Evidence retraction and restoration propagate across a multi-stage decision chain. |
| `scientific_judgment` | 5 | 1.5 | Claim, sensitivity and shared-resource gates interact before portfolio selection. |
| `computational_difficulty` | 5 | 1.5 | Eighteen replay states and fifteen portfolios require independent recomputation. |
| `tool_call_complexity` | 4 | 1 | Four mutually consistent artifacts are required. |
| `retrieval_complexity` | 3 | 1 | All evidence is offline across three linked JSON inputs. |
| `information_noise_complexity` | 5 | 1 | High-utility decoys fail transient or shared-resource gates. |
| `data_type_complexity` | 4 | 1 | JSON event streams feed JSON, TSV and prose outputs. |
| `data_complexity` | 5 | 1 | Six chains cross three checkpoints and fifteen portfolios. |
| `environment_complexity` | 3 | 1 | Offline deterministic replay and hashing are required. |
| `mathematical_complexity` | 5 | 1 | Portfolio selection maximizes the minimum checkpoint aggregate. |
| `long_horizon_complexity` | 5 | 1.5 | Transient invalidity disqualifies a chain after later restoration. |
| `safety_risk` | 4 | 1 | Human review and bounded claims remain mandatory. |

## Interactions

- `long_horizon_x_tool_orchestration`
- `judgment_x_noisy_evidence`
- `high_stakes_safety_review`

## Selected modules

### horizon
- `horizon_checkpointed_workflow`: `{}`
### judgment
- `judgment_claim_permission_lattice`: `{}`
### data
- `data_evidence_graph_join`: `{}`
- `data_shared_inventory_allocation`: `{}`
### math
- `math_robust_scenario_optimization`: `{}`
### environment
- `environment_offline_setup`: `{}`
### safety
- `safety_human_approval_gate`: `{}`
