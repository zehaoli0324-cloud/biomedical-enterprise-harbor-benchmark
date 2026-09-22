# Difficulty report: eb013-evidence-budget-routing-002

- Title: Two-stage evidence budget routing under observed uncertainty
- Domain: biomedical_enterprise
- Raw score: 4.655/5
- Adjusted score: 5.0/5
- Band: frontier
- Spec digest: `28c40e2198fc73780f9d2d37bf0833aae63d037566d3087901991396a53ebcd2`

## Dimensions

| Dimension | Level | Weight | Rationale |
| --- | ---: | ---: | --- |
| `scientific_scenario` | 5 | 1.5 | The action space changes after an observed stage-one state. |
| `scientific_judgment` | 5 | 1.5 | The agent must preserve the prospective boundary and select a bounded policy. |
| `computational_difficulty` | 5 | 1.5 | Dependency-valid policies are enumerated across observation states. |
| `tool_call_complexity` | 4 | 1 | Five synchronized artifacts encode the adaptive route. |
| `retrieval_complexity` | 4 | 1 | Nested request catalogs must be discovered without network access. |
| `information_noise_complexity` | 5 | 1 | Fixed, future and infeasible stage-two options are plausible distractors. |
| `data_type_complexity` | 4 | 1 | JSON state transitions feed JSON, TSV and prose outputs. |
| `data_complexity` | 5 | 1 | A policy cross-product spans stage-one outcomes and stage-two actions. |
| `environment_complexity` | 4 | 1 | Checksums and deterministic offline replay remain mandatory. |
| `mathematical_complexity` | 5 | 1.5 | Worst-case maximum residual is optimized before cost and lexical tie-breaks. |
| `long_horizon_complexity` | 5 | 1.5 | The stage-one observation gates the legal stage-two action. |
| `safety_risk` | 4 | 1 | Future outcome leakage and unsupported experimental claims are blocked. |

## Interactions

- `long_horizon_x_tool_orchestration`
- `judgment_x_noisy_evidence`
- `data_x_environment`
- `retrieval_x_scientific_judgment`
- `high_stakes_safety_review`

## Selected modules

### horizon
- `horizon_two_stage_acquisition`: `{}`
### judgment
- `judgment_evidence_route_selection`: `{}`
- `judgment_uncertainty_and_stop_rules`: `{}`
### math
- `math_correlation_adjusted_reduction`: `{}`
- `math_minimax_evidence_route_selection`: `{}`
### retrieval
- `retrieval_provenance_temporal_boundary`: `{}`
### environment
- `environment_schema_discovery_under_offline`: `{}`
### safety
- `safety_human_approval_gate`: `{}`
