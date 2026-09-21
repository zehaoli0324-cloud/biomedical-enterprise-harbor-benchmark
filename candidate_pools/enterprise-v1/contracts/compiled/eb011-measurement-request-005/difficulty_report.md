# Difficulty report: eb011-measurement-request-005

- Title: active measurement request under correlated uncertainty
- Domain: biomedical_enterprise
- Raw score: 3.72/5
- Adjusted score: 3.92/5
- Band: advanced
- Spec digest: `ab07c47b69bc34f1137bb50d8ba8badf0d5aee36e1d58892b7e73c0d1eebacde`

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
- `judgment_value_of_information`: `{}`
### compute
- `compute_multistage_analysis`: `{}`
### noise
- `noise_metadata_conflict`: `{}`
### safety
- `safety_human_approval_gate`: `{}`
- `safety_human_approval_gate`: `{}`
### data
- `data_text_and_metadata`: `{}`
### data_complexity
- `complexity_sparse_or_missing`: `{}`
### environment
- `environment_offline_setup`: `{}`
### math
- `math_model_selection_and_sensitivity`: `{}`
