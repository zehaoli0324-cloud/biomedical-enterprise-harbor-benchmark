# Difficulty report: eb014-sequential-evidence-feedback-002

- Title: Sequential evidence feedback and claim-boundary review
- Domain: biomedical_enterprise
- Raw score: 4.0/5
- Adjusted score: 4.7/5
- Band: frontier
- Spec digest: `9b79f229bd76d8eab0d9353503bdb97ebe5187f9154eb8251ec496c5634c8b0e`

## Dimensions

| Dimension | Level | Weight | Rationale |
| --- | ---: | ---: | --- |
| `scientific_scenario` | 5 | 1 | Stateful synthetic evidence review where new measurements alter legal follow-up actions. |
| `scientific_judgment` | 5 | 1 | The model must hold a target-context claim after a context shift while preserving registered-cohort replication. |
| `computational_difficulty` | 3 | 1 | Maintain a bounded action ledger and cumulative budget across feedback rounds. |
| `tool_call_complexity` | 4 | 1 | One request and one response are exchanged per model interaction. |
| `retrieval_complexity` | 4 | 1 | Independent replication and context evidence have different claim permissions. |
| `information_noise_complexity` | 4 | 1 | The environment returns measurements and costs but no recommendation or score. |
| `data_type_complexity` | 3 | 1 | JSON request, response, event ledger and completion contract. |
| `data_complexity` | 4 | 1 | The same evidence state is updated after each action and feedback event. |
| `environment_complexity` | 5 | 1 | Feedback is host-controlled, deterministic and hidden from the visible workspace. |
| `mathematical_complexity` | 3 | 1 | Cumulative budget and dependency legality are recomputed after each response. |
| `long_horizon_complexity` | 5 | 1 | Each next action depends on a prior observation; early stopping and handoff are legal. |
| `safety_risk` | 3 | 1 | Synthetic planning only with an explicit registered-cohort claim boundary. |

## Interactions

- `long_horizon_x_tool_orchestration`
- `judgment_x_noisy_evidence`
- `data_x_environment`
- `retrieval_x_scientific_judgment`

## Selected modules

### horizon
- `horizon_sequential_evidence_feedback`: `{}`
### judgment
- `judgment_evidence_sufficiency_abstention`: `{}`
### retrieval
- `retrieval_independence_quorum`: `{}`
### math
- `math_ex_ante_shared_setup`: `{}`
