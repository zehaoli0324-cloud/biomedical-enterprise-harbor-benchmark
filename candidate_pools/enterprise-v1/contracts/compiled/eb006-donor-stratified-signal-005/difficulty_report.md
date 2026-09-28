# Difficulty report: eb006-donor-stratified-signal-005

- Title: Donor-stratified perturbation signal under partial identifiability
- Domain: biomedical_enterprise
- Raw score: 4.04/5
- Adjusted score: 4.24/5
- Band: research-grade
- Spec digest: `292bdaec391c48f4e8360dfa9a2d854635412da7ea72528d322295eab34e06fd`

## Dimensions

| Dimension | Level | Weight | Rationale |
| --- | ---: | ---: | --- |
| `scientific_scenario` | 5 | 1 | A profile-review handoff depends on reproducibility across independent donors and registered states. |
| `scientific_judgment` | 5 | 1.5 | The agent must distinguish local missingness, contradiction, weak support and reproducible signal. |
| `computational_difficulty` | 5 | 1 | Technical replicates are collapsed before donor effects and heterogeneous state rules are applied. |
| `tool_call_complexity` | 3 | 1 | The task requires deterministic CSV and JSON processing without external dependencies. |
| `retrieval_complexity` | 2 | 1 | All evidence is offline; scope and policy lookup remain explicit. |
| `information_noise_complexity` | 5 | 1 | Unequal technical replication, an inactive high-signal row and pooled attraction are adversarial. |
| `data_type_complexity` | 4 | 1 | CSV observations, JSON policy, TSV diagnostics and provenance must agree. |
| `data_complexity` | 5 | 1 | The data encode a technical-replicate, condition, donor and state hierarchy. |
| `environment_complexity` | 2 | 1 | The task is deterministic and offline. |
| `mathematical_complexity` | 5 | 1 | State-specific support, mean and range thresholds feed a lexicographic robust selection. |
| `long_horizon_complexity` | 4 | 1 | Errors in replicate collapse propagate through donor, state, candidate and handoff decisions. |
| `safety_risk` | 3 | 1 | The result remains an analytical triage recommendation requiring human review. |

## Interactions

- `judgment_x_noisy_evidence`

## Selected modules

### scenario
- `scenario_omics_analysis`: `{}`
### judgment
- `judgment_experimental_unit`: `{}`
- `judgment_conflict_precedence`: `{}`
- `judgment_uncertainty_and_stop_rules`: `{}`
### compute
- `compute_multistage_analysis`: `{}`
### tooling
- `tool_branching_pipeline`: `{}`
### retrieval
- `retrieval_schema_discovery`: `{}`
### noise
- `noise_pooled_stratified_adversary`: `{}`
- `noise_operational_distractors`: `{}`
### data
- `data_experimental_unit_hierarchy`: `{}`
### data_complexity
- `complexity_replicates_and_batches`: `{}`
- `complexity_sparse_or_missing`: `{}`
### environment
- `environment_offline_setup`: `{}`
### math
- `math_stratified_partial_identifiability`: `{}`
### horizon
- `horizon_end_to_end_claim`: `{}`
### safety
- `safety_human_approval_gate`: `{}`
