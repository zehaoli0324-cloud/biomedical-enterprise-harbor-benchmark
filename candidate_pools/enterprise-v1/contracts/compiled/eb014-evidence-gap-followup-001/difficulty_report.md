# Difficulty report: eb014-evidence-gap-followup-001

- Title: Evidence gap identification and adaptive follow-up planning
- Domain: biomedical_enterprise
- Raw score: 4.583/5
- Adjusted score: 5.0/5
- Band: frontier
- Spec digest: `db5aba829c6f02c851ade135846c3fd8243f41b8d6618d2ca0c30d92509b098e`

## Dimensions

| Dimension | Level | Weight | Rationale |
| --- | ---: | ---: | --- |
| `scientific_scenario` | 5 | 1 | Registered evidence, scope and future follow-up are separated. |
| `scientific_judgment` | 5 | 1 | Premise support controls a claim-permission ceiling. |
| `computational_difficulty` | 5 | 1 | Enumerate action subsets and feedback-conditioned policies. |
| `tool_call_complexity` | 3 | 1 | Self-contained JSON with a public output contract. |
| `retrieval_complexity` | 5 | 1 | Evidence status, scope, independence and temporal joins are required. |
| `information_noise_complexity` | 5 | 1 | Stale, duplicated, wrong-scope and future records remain visible decoys. |
| `data_type_complexity` | 5 | 1 | Nested evidence-premise-claim-action graph. |
| `data_complexity` | 5 | 1 | Multiple claim levels and conditional result states. |
| `environment_complexity` | 3 | 1 | Offline deterministic calculation. |
| `mathematical_complexity` | 5 | 1 | Worst-case resolved-claim weight, then cost and action count under dependencies. |
| `long_horizon_complexity` | 5 | 1 | First follow-up result gates the second action and stop decision. |
| `safety_risk` | 4 | 1 | Claim inflation is explicitly blocked and human review is required. |

## Interactions

- `judgment_x_noisy_evidence`
- `retrieval_x_scientific_judgment`
- `high_stakes_safety_review`

## Selected modules

### judgment
- `judgment_claim_transportability_boundary`: `{}`
### research_planning
- `research_minimum_additional_evidence`: `{}`
### horizon
- `horizon_adaptive_research_priority`: `{}`
### retrieval
- `retrieval_independence_quorum`: `{}`
