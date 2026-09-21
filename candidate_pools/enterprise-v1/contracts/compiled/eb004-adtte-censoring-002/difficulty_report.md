# Difficulty report: eb004-adtte-censoring-002

- Title: ADTTE event and censoring derivation under a prespecified cutoff
- Domain: biomedical_enterprise
- Raw score: 2.917/5
- Adjusted score: 3.117/5
- Band: advanced
- Spec digest: `c0e309e06f2ac6f85739a7b50365cbb9cd141054f174c4ab1846a224374e7212`

## Dimensions

| Dimension | Level | Weight | Rationale |
| --- | ---: | ---: | --- |
| `scientific_scenario` | 4 | 1 | The same calendar arithmetic can produce different endpoint meanings; the task tests endpoint rules, partial dates, and bounded handoff. |
| `scientific_judgment` | 5 | 1 | The same calendar arithmetic can produce different endpoint meanings; the task tests endpoint rules, partial dates, and bounded handoff. |
| `computational_difficulty` | 3 | 1 | The same calendar arithmetic can produce different endpoint meanings; the task tests endpoint rules, partial dates, and bounded handoff. |
| `tool_call_complexity` | 1 | 1 | The same calendar arithmetic can produce different endpoint meanings; the task tests endpoint rules, partial dates, and bounded handoff. |
| `retrieval_complexity` | 1 | 1 | The same calendar arithmetic can produce different endpoint meanings; the task tests endpoint rules, partial dates, and bounded handoff. |
| `information_noise_complexity` | 4 | 1 | The same calendar arithmetic can produce different endpoint meanings; the task tests endpoint rules, partial dates, and bounded handoff. |
| `data_type_complexity` | 3 | 1 | The same calendar arithmetic can produce different endpoint meanings; the task tests endpoint rules, partial dates, and bounded handoff. |
| `data_complexity` | 3 | 1 | The same calendar arithmetic can produce different endpoint meanings; the task tests endpoint rules, partial dates, and bounded handoff. |
| `environment_complexity` | 1 | 1 | The same calendar arithmetic can produce different endpoint meanings; the task tests endpoint rules, partial dates, and bounded handoff. |
| `mathematical_complexity` | 3 | 1 | The same calendar arithmetic can produce different endpoint meanings; the task tests endpoint rules, partial dates, and bounded handoff. |
| `long_horizon_complexity` | 4 | 1 | The same calendar arithmetic can produce different endpoint meanings; the task tests endpoint rules, partial dates, and bounded handoff. |
| `safety_risk` | 3 | 1 | The same calendar arithmetic can produce different endpoint meanings; the task tests endpoint rules, partial dates, and bounded handoff. |

## Interactions

- `judgment_x_noisy_evidence`

## Selected modules

### scenario
- `scenario_reproducibility_audit`: `{}`
### judgment
- `judgment_experimental_unit`: `{}`
- `judgment_uncertainty_and_stop_rules`: `{}`
- `judgment_causal_boundary`: `{}`
### compute
- `compute_data_schema_discovery`: `{}`
- `compute_multistage_analysis`: `{}`
### noise
- `noise_metadata_conflict`: `{}`
- `noise_missing_and_duplicate_inputs`: `{}`
### data
- `data_text_and_metadata`: `{}`
### data_complexity
- `complexity_sparse_or_missing`: `{}`
### environment
- `environment_offline_setup`: `{}`
### math
- `math_basic_units_and_rates`: `{}`
- `math_statistics_and_multiple_testing`: `{}`
### horizon
- `horizon_checkpointed_workflow`: `{}`
- `horizon_end_to_end_claim`: `{}`
### safety
- `safety_human_approval_gate`: `{}`
- `safety_genetic_or_clinical_boundary`: `{}`
