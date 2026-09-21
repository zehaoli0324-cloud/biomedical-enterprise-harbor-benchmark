# Difficulty report: eb008-route-portfolio-002

- Title: shared-inventory route portfolio with dependent evidence
- Domain: biomedical_enterprise
- Raw score: 3.72/5
- Adjusted score: 3.92/5
- Band: advanced
- Spec digest: `b30ff6b589854bb8795f2338cb22ae67e2582a5a376fde4940e21c3833e7c559`

## Dimensions

| Dimension | Level | Weight | Rationale |
| --- | ---: | ---: | --- |
| `scientific_scenario` | 4 | 1 | L4 requires cross-artifact constraints, partial observability and a single-factor decision flip. |
| `scientific_judgment` | 5 | 1.5 | The correct action may be selection, hold, escalation or block; local proxy optimization is insufficient. |
| `computational_difficulty` | 4 | 1 | The verifier derives a deterministic decision from multiple joined inputs. |
| `tool_call_complexity` | 3 | 1 | The task requires several structured artifacts and a provenance manifest. |
| `retrieval_complexity` | 1 | 1 | All evidence is supplied offline; the challenge is reconciliation rather than retrieval. |
| `information_noise_complexity` | 5 | 1 | Decoy rows and locally attractive but globally invalid branches are visible. |
| `data_type_complexity` | 4 | 1 | CSV/JSON/TSV/Markdown artifacts must agree. |
| `data_complexity` | 4 | 1 | The decision depends on joined records, not a single table. |
| `environment_complexity` | 2 | 1 | The fixture is offline and deterministic with explicit resource limits. |
| `mathematical_complexity` | 4 | 1 | At least one metric, threshold or robust comparison is decision-binding. |
| `long_horizon_complexity` | 5 | 1 | Intermediate state and handoff claims constrain the final action. |
| `safety_risk` | 3 | 1 | The output is bounded by human review and explicit non-experimental claims. |

## Interactions

- `judgment_x_noisy_evidence`

## Selected modules

### judgment
- `judgment_experimental_unit`: `{}`
### compute
- `compute_data_schema_discovery`: `{}`
### math
- `math_model_selection_and_sensitivity`: `{}`
- `math_model_selection_and_sensitivity`: `{}`
### safety
- `safety_human_approval_gate`: `{}`
- `safety_human_approval_gate`: `{}`
### data
- `data_text_and_metadata`: `{}`
### data_complexity
- `complexity_sparse_or_missing`: `{}`
### environment
- `environment_offline_setup`: `{}`
