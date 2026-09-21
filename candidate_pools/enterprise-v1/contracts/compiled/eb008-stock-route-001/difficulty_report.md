# Difficulty report: eb008-stock-route-001

- Title: Retrosynthesis route selection under stock and reaction validity constraints
- Domain: biomedical_enterprise
- Raw score: 3.24/5
- Adjusted score: 3.54/5
- Band: advanced
- Spec digest: `02d0f915a0c32ba3ba4d6631947f43e612f5e528ed9ebeb92e1b85e36811ea91`

## Dimensions

| Dimension | Level | Weight | Rationale |
| --- | ---: | ---: | --- |
| `scientific_scenario` | 4 | 1 | A high route score is insufficient; the decision requires independent structure, stock, and failure checks before human review. |
| `scientific_judgment` | 5 | 1.5 | A high route score is insufficient; the decision requires independent structure, stock, and failure checks before human review. |
| `computational_difficulty` | 4 | 1 | A high route score is insufficient; the decision requires independent structure, stock, and failure checks before human review. |
| `tool_call_complexity` | 2 | 1 | A high route score is insufficient; the decision requires independent structure, stock, and failure checks before human review. |
| `retrieval_complexity` | 1 | 1 | A high route score is insufficient; the decision requires independent structure, stock, and failure checks before human review. |
| `information_noise_complexity` | 4 | 1 | A high route score is insufficient; the decision requires independent structure, stock, and failure checks before human review. |
| `data_type_complexity` | 3 | 1 | A high route score is insufficient; the decision requires independent structure, stock, and failure checks before human review. |
| `data_complexity` | 3 | 1 | A high route score is insufficient; the decision requires independent structure, stock, and failure checks before human review. |
| `environment_complexity` | 2 | 1 | A high route score is insufficient; the decision requires independent structure, stock, and failure checks before human review. |
| `mathematical_complexity` | 2 | 1 | A high route score is insufficient; the decision requires independent structure, stock, and failure checks before human review. |
| `long_horizon_complexity` | 4 | 1 | A high route score is insufficient; the decision requires independent structure, stock, and failure checks before human review. |
| `safety_risk` | 4 | 1 | A high route score is insufficient; the decision requires independent structure, stock, and failure checks before human review. |

## Interactions

- `judgment_x_noisy_evidence`
- `high_stakes_safety_review`

## Selected modules

### scenario
- `scenario_structure_design`: `{}`
### judgment
- `judgment_route_feasibility`: `{}`
- `judgment_evidence_quality`: `{}`
- `judgment_uncertainty_and_stop_rules`: `{}`
- `judgment_causal_boundary`: `{}`
### compute
- `compute_data_schema_discovery`: `{}`
- `compute_multistage_analysis`: `{}`
### tooling
- `tool_branching_pipeline`: `{}`
### noise
- `noise_metadata_conflict`: `{}`
- `noise_red_herring_records`: `{}`
### data
- `data_text_and_metadata`: `{}`
### data_complexity
- `complexity_sparse_or_missing`: `{}`
### environment
- `environment_offline_setup`: `{}`
### math
- `math_model_selection_and_sensitivity`: `{}`
### horizon
- `horizon_checkpointed_workflow`: `{}`
### safety
- `safety_human_approval_gate`: `{}`
