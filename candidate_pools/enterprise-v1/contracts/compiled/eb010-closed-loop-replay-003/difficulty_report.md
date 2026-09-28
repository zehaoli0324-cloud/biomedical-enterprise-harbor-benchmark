# Difficulty report: eb010-closed-loop-replay-003

- Title: Closed-loop policy replay with temporal causality and stability gates
- Domain: biomedical_enterprise
- Raw score: 4.259/5
- Adjusted score: 4.759/5
- Band: frontier
- Spec digest: `51b88938ed9e925e9f711740b9cc578b7bac968d57c3aff503e95e0aee4bf7b8`

## Dimensions

| Dimension | Level | Weight | Rationale |
| --- | ---: | ---: | --- |
| `scientific_scenario` | 5 | 1.5 | Policy value is evaluated across ordered replay states rather than a static score. |
| `scientific_judgment` | 5 | 1.5 | A high utility policy is rejected for leakage, instability, or budget drift. |
| `computational_difficulty` | 4 | 1 | The verifier derives policy eligibility from replay and stage constraints. |
| `tool_call_complexity` | 4 | 1 | The policy must produce synchronized replay, audit, and provenance artifacts. |
| `retrieval_complexity` | 2 | 1 | All candidate evidence is supplied offline; the difficulty is temporal reconciliation. |
| `information_noise_complexity` | 5 | 1 | A high-utility leakage policy and an over-budget policy remain visible as adversarial alternatives. |
| `data_type_complexity` | 4 | 1 | JSON case inputs must reconcile with CSV-like policy outputs and a structured audit. |
| `data_complexity` | 4 | 1 | Policy state, stage order, observations, outcomes, and seed replay records form a joined state graph. |
| `environment_complexity` | 3 | 1 | The fixture is offline and deterministic, with explicit budget and replay requirements. |
| `mathematical_complexity` | 5 | 1 | Eligibility depends on utility, budget, leakage, and a cross-seed stability spread. |
| `long_horizon_complexity` | 5 | 1.5 | Each stage constrains the next state and available information. |
| `safety_risk` | 4 | 1 | The policy can trigger a consequential next-batch action and must stop for human review when gates fail. |

## Interactions

- `long_horizon_x_tool_orchestration`
- `judgment_x_noisy_evidence`
- `high_stakes_safety_review`

## Selected modules

### scenario
- `scenario_reproducibility_audit`: `{}`
### horizon
- `horizon_adaptive_policy_replay`: `{}`
### math
- `math_replay_stability`: `{}`
- `math_robust_scenario_optimization`: `{}`
### judgment
- `judgment_value_of_information`: `{}`
- `judgment_blocker_and_abstention`: `{}`
### data
- `data_text_and_metadata`: `{}`
### tooling
- `tool_branching_pipeline`: `{}`
### retrieval
- `retrieval_inclusion_exclusion`: `{}`
### noise
- `noise_red_herring_records`: `{}`
### data_complexity
- `complexity_sparse_or_missing`: `{}`
### environment
- `environment_offline_setup`: `{}`
### safety
- `safety_human_approval_gate`: `{}`
