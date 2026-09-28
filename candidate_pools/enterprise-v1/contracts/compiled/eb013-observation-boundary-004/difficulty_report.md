# Difficulty report: eb013-observation-boundary-004

- Title: Observation-limited robust evidence routing
- Domain: biomedical_enterprise
- Raw score: 4.5/5
- Adjusted score: 5.0/5
- Band: frontier
- Spec digest: `2c29c8ed83008dade1dffcd443aa031368e1413b5c60e32f143cc5a5bfe7021a`

## Dimensions

| Dimension | Level | Weight | Rationale |
| --- | ---: | ---: | --- |
| `scientific_scenario` | 5 | 1 | Observable signal partitions conceal multiple stress worlds. |
| `scientific_judgment` | 5 | 1 | The action must preserve observational equivalence and claim boundaries. |
| `computational_difficulty` | 5 | 1 | Enumerate thousands of complete label policies and replay every world. |
| `tool_call_complexity` | 3 | 1 | Self-contained JSON and explicit output contract. |
| `retrieval_complexity` | 5 | 1 | Source status, scope and temporal availability are joined. |
| `information_noise_complexity` | 5 | 1 | Latent scenario decoys and unusable sources remain visible. |
| `data_type_complexity` | 4 | 1 | Nested world, action and source joins. |
| `data_complexity` | 5 | 1 | Four worlds, non-injective observations and eleven actions. |
| `environment_complexity` | 4 | 1 | Offline deterministic calculation with explicit deadline and capacity. |
| `mathematical_complexity` | 5 | 1 | Ex-ante setup union plus normalized distributional minimax. |
| `long_horizon_complexity` | 5 | 1 | Commit before observation, then replay conditional actions. |
| `safety_risk` | 3 | 1 | Synthetic planning only; human review required. |

## Interactions

- `judgment_x_noisy_evidence`
- `data_x_environment`
- `retrieval_x_scientific_judgment`

## Selected modules

### math
- `math_ex_ante_shared_setup`: `{}`
- `math_distributional_minimax`: `{}`
### horizon
- `horizon_observation_equivalence`: `{}`
### retrieval
- `retrieval_provenance_temporal_boundary`: `{}`
