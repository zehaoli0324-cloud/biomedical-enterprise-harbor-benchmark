# Difficulty report: eb013-shared-setup-routing-003

- Title: Prospective evidence routing with shared setup commitments
- Domain: biomedical_enterprise
- Raw score: 3.917/5
- Adjusted score: 4.117/5
- Band: research-grade
- Spec digest: `07cfb1806735982bfde08e19fa01120d146f1271c5dbf99e1c79f6fe29b98ada`

## Dimensions

| Dimension | Level | Weight | Rationale |
| --- | ---: | ---: | --- |
| `scientific_scenario` | 5 | 1 | Synthetic assay planning with ex-ante commitments and contingent execution. |
| `scientific_judgment` | 5 | 1 | Preparation timing couples the branches before observations. |
| `computational_difficulty` | 4 | 1 | Enumerate 108 complete legal policy mappings. |
| `tool_call_complexity` | 3 | 1 | Small JSON inputs with self-contained output contract. |
| `retrieval_complexity` | 3 | 1 | Check complete source availability and prerequisites. |
| `information_noise_complexity` | 4 | 1 | Future, retracted and partially satisfied dependency decoys. |
| `data_type_complexity` | 3 | 1 | Structured JSON and synchronized TSV. |
| `data_complexity` | 4 | 1 | Three stage-one alternatives and shared branch preparations. |
| `environment_complexity` | 3 | 1 | Deterministic offline calculation and input checksums. |
| `mathematical_complexity` | 5 | 1 | Setup union couples discrete policies; lexicographic minimax objective. |
| `long_horizon_complexity` | 5 | 1 | Preparation must be committed before observation-specific actions. |
| `safety_risk` | 3 | 1 | Synthetic planning only, with explicit human review. |

## Interactions

- `judgment_x_noisy_evidence`

## Selected modules

### math
- `math_ex_ante_shared_setup`: `{}`
- `math_minimax_evidence_route_selection`: `{}`
### horizon
- `horizon_adaptive_policy_replay`: `{}`
### retrieval
- `retrieval_provenance_temporal_boundary`: `{}`
