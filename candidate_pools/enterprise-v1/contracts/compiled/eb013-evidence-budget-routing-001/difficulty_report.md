# Difficulty report: eb013-evidence-budget-routing-001

- Title: Evidence budget routing under correlated uncertainty
- Domain: biomedical_enterprise
- Raw score: 4.571/5
- Adjusted score: 5.0/5
- Band: frontier
- Spec digest: `026daa2935bb049f0858266c572803e90a5e63e9edc0d85e67869edea4e263e6`

## Dimensions

| Dimension | Level | Weight | Rationale |
| --- | ---: | ---: | --- |
| `scientific_scenario` | 5 | 1.5 | A bounded evidence route must cross multiple critical decision thresholds. |
| `scientific_judgment` | 5 | 1.5 | The binding uncertainty must be resolved without nominal-value shortcuts. |
| `computational_difficulty` | 5 | 1.5 | The agent must enumerate dependency-valid subsets and recompute residuals. |
| `tool_call_complexity` | 4 | 1 | Five mutually consistent artifacts are required. |
| `retrieval_complexity` | 4 | 1 | Nested offline inputs contain current, archived and post-decision records. |
| `information_noise_complexity` | 5 | 1 | High nominal-value records are deliberately unusable or incomplete. |
| `data_type_complexity` | 4 | 1 | Nested JSON must be reconciled into JSON, TSV and prose outputs. |
| `data_complexity` | 5 | 1 | Seven requests induce a constrained combinatorial route space. |
| `environment_complexity` | 4 | 1 | Offline discovery, checksums and deterministic output are mandatory. |
| `mathematical_complexity` | 5 | 1.5 | Correlation-adjusted reductions and lexicographic multi-objective selection interact. |
| `long_horizon_complexity` | 4 | 1 | Discovery, route planning, eligibility and stop decisions must remain consistent. |
| `safety_risk` | 4 | 1 | No valid route must degrade to human review and claims remain planning-only. |

## Interactions

- `long_horizon_x_tool_orchestration`
- `judgment_x_noisy_evidence`
- `data_x_environment`
- `retrieval_x_scientific_judgment`
- `high_stakes_safety_review`

## Selected modules

### judgment
- `judgment_evidence_route_selection`: `{}`
- `judgment_uncertainty_and_stop_rules`: `{}`
### data
- `data_dependency_graph_routing`: `{}`
### math
- `math_correlation_adjusted_reduction`: `{}`
- `math_minimax_evidence_route_selection`: `{}`
### retrieval
- `retrieval_provenance_temporal_boundary`: `{}`
### environment
- `environment_schema_discovery_under_offline`: `{}`
### safety
- `safety_human_approval_gate`: `{}`
