# Difficulty report: eb006-signal-noise-004

- Title: Perturbation signal versus technical noise
- Domain: biomedical_enterprise
- Raw score: 2.833/5
- Adjusted score: 3.033/5
- Band: advanced
- Spec digest: `de00e0b9400e931695b493046097ebf6514f503b7fdcdfe37644f5bcd1c00612`

## Dimensions

| Dimension | Level | Weight | Rationale |
| --- | ---: | ---: | --- |
| `scientific_scenario` | 4 | 1 | The decision is whether a perturbation phenotype survives technical-noise checks before profile review. |
| `scientific_judgment` | 5 | 1 | Raw signal must be reconciled with adjusted signal, replicate count and control drift. |
| `computational_difficulty` | 3 | 1 | The task joins replicate, plate and nuisance-adjusted measurements. |
| `tool_call_complexity` | 2 | 1 | The challenge is evidence reconciliation, not tool count. |
| `retrieval_complexity` | 1 | 1 | All evidence is in the frozen offline bundle. |
| `information_noise_complexity` | 4 | 1 | Plate effects and control drift can mimic a biological phenotype. |
| `data_type_complexity` | 3 | 1 | CSV measurements and JSON rules require a joined decision. |
| `data_complexity` | 2 | 1 | The fixture is small but contains replicate-level evidence. |
| `environment_complexity` | 2 | 1 | The offline environment is fixed and deterministic. |
| `mathematical_complexity` | 2 | 1 | Effect and drift summaries are simple but must use the correct subsets. |
| `long_horizon_complexity` | 3 | 1 | The handoff links profile measurements, noise diagnostics and human review. |
| `safety_risk` | 3 | 1 | A residual signal is not evidence of mechanism, target engagement or efficacy. |

## Interactions

- `judgment_x_noisy_evidence`

## Selected modules

### scenario
- `scenario_reproducibility_audit`: `{}`
### judgment
- `judgment_uncertainty_and_stop_rules`: `{}`
- `judgment_causal_boundary`: `{}`
### compute
- `compute_multistage_analysis`: `{}`
### tooling
- `tool_branching_pipeline`: `{}`
### noise
- `noise_metadata_conflict`: `{}`
### data
- `data_multimodal_join`: `{}`
### data_complexity
- `complexity_sparse_or_missing`: `{}`
### environment
- `environment_pinned_container`: `{}`
### math
- `math_model_selection_and_sensitivity`: `{}`
### horizon
- `horizon_checkpointed_workflow`: `{}`
### safety
- `safety_human_approval_gate`: `{}`
