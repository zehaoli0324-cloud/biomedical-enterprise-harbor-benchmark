# Difficulty report: eb006-research-completion-006

- Title: Completion-gated donor evidence research
- Domain: biomedical_enterprise
- Raw score: 4.52/5
- Adjusted score: 5.0/5
- Band: frontier
- Spec digest: `90aabdc7ade3300d7f61404f6de2f64a3dbfdee5b102d73b5e84d3f2bbd019ab`

## Dimensions

| Dimension | Level | Weight | Rationale |
| --- | ---: | ---: | --- |
| `scientific_scenario` | 5 | 1 | A profile-review handoff must reconcile donor-balanced, pooled, and influence-robust evidence. |
| `scientific_judgment` | 5 | 1.5 | The nominal, pooled, and LODO-robust winners differ and require a bounded resolution. |
| `computational_difficulty` | 5 | 1 | A standalone program computes 24 unit effects, 30 scenario checks, pooled diagnostics, summaries, and decisions. |
| `tool_call_complexity` | 5 | 1 | The submission is executed repeatedly in clean directories and on reordered input. |
| `retrieval_complexity` | 2 | 1 | All evidence and the public completion contract are offline. |
| `information_noise_complexity` | 5 | 1 | Unequal technical replication makes the pooled winner scientifically misleading. |
| `data_type_complexity` | 5 | 1 | CSV inputs, JSON policy/contract, executable Python, JSON outputs, provenance, and audit text must agree. |
| `data_complexity` | 5 | 1 | The design crosses candidate, donor, state, condition, replicate, and omission scenario. |
| `environment_complexity` | 4 | 1 | The analysis must replay deterministically under a shared budget without network access. |
| `mathematical_complexity` | 5 | 1 | Exact aggregation, precedence, thresholds, omission stability, and three ranking objectives interact. |
| `long_horizon_complexity` | 5 | 1 | Submission is accepted only after executable primary, alternative, sensitivity, and resolution evidence passes the public gate. |
| `safety_risk` | 3 | 1 | The recommendation remains analytical triage requiring human review. |

## Interactions

- `long_horizon_x_tool_orchestration`
- `judgment_x_noisy_evidence`
- `data_x_environment`

## Selected modules

### scenario
- `scenario_omics_analysis`: `{}`
### judgment
- `judgment_influence_reconciliation`: `{}`
- `judgment_experimental_unit`: `{}`
### compute
- `compute_multistage_analysis`: `{}`
### tooling
- `tool_branching_pipeline`: `{}`
### retrieval
- `retrieval_schema_discovery`: `{}`
### noise
- `noise_pooled_stratified_adversary`: `{}`
### data
- `data_experimental_unit_hierarchy`: `{}`
### data_complexity
- `complexity_replicates_and_batches`: `{}`
- `complexity_sparse_or_missing`: `{}`
### environment
- `environment_offline_setup`: `{}`
- `environment_resource_budget`: `{}`
### math
- `math_stratified_partial_identifiability`: `{}`
- `math_model_selection_and_sensitivity`: `{}`
### horizon
- `horizon_verified_research_completion`: `{}`
### safety
- `safety_human_approval_gate`: `{}`
