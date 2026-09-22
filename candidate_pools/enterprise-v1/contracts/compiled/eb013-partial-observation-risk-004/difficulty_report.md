# Difficulty report: eb013-partial-observation-risk-004

- Title: Partial-observation assay policy with robust tail risk
- Domain: biomedical_enterprise
- Raw score: 4.167/5
- Adjusted score: 4.517/5
- Band: research-grade
- Spec digest: `5485928afd963e53fd8438c4ad0a68d1650aa74f088fc6e7a21e49ecfc8a1ba3`

## Dimensions

| Dimension | Level | Weight | Rationale |
| --- | ---: | ---: | --- |
| `scientific_scenario` | 5 | 1 | Synthetic assay planning under hidden execution states and distribution shift. |
| `scientific_judgment` | 5 | 1 | Distinguish observable decisions from planner-visible counterfactual worlds. |
| `computational_difficulty` | 4 | 1 | 346 complete policies with world replay and model-specific tail integration. |
| `tool_call_complexity` | 3 | 1 | Offline structured calculation and artifact validation. |
| `retrieval_complexity` | 5 | 1 | As-of full snapshots, future revisions and withdrawal tombstones. |
| `information_noise_complexity` | 4 | 1 | Optimistic old estimates and unavailable apparent winners. |
| `data_type_complexity` | 3 | 1 | Explicit JSON contracts and keyed TSV replay. |
| `data_complexity` | 5 | 1 | Join world, observation, action, capability, snapshot and probability model. |
| `environment_complexity` | 3 | 1 | Deterministic offline arithmetic and SHA-256 provenance. |
| `mathematical_complexity` | 5 | 1 | Exact fractional CVaR boundary mass and distributionally robust lexicographic optimization. |
| `long_horizon_complexity` | 5 | 1 | Probe and shared setup committed before partial observation; nonanticipative execution. |
| `safety_risk` | 3 | 1 | Synthetic planning only with mandatory human review. |

## Interactions

- `judgment_x_noisy_evidence`
- `retrieval_x_scientific_judgment`

## Selected modules

### horizon
- `horizon_observation_nonanticipativity`: `{}`
### math
- `math_distributionally_robust_cvar`: `{}`
- `math_ex_ante_shared_setup`: `{}`
### retrieval
- `retrieval_asof_tombstone_resolution`: `{}`
