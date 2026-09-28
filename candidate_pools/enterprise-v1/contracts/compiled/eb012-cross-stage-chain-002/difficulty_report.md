# Difficulty report: eb012-cross-stage-chain-002

- Title: Cross-stage claim and provenance chain audit
- Domain: biomedical_enterprise
- Raw score: 4.429/5
- Adjusted score: 4.929/5
- Band: frontier
- Spec digest: `a933df42992013bb9280f0a733b82da8090836d323afc2b90d2d6bd2cd8166f8`

## Dimensions

| Dimension | Level | Weight | Rationale |
| --- | ---: | ---: | --- |
| `scientific_scenario` | 5 | 1.5 | Four stage artifacts form a provenance-constrained handoff graph. |
| `scientific_judgment` | 5 | 1.5 | Claim permission, resource reservation and robust policy thresholds interact. |
| `computational_difficulty` | 5 | 1.5 | Sixteen artifacts and four candidate chains require joined gate evaluation. |
| `tool_call_complexity` | 4 | 1 | The agent produces a JSON decision, TSV handoff ledger, audit and manifest. |
| `retrieval_complexity` | 3 | 1 | All evidence is offline but must be followed across stage links. |
| `information_noise_complexity` | 5 | 1 | High-CVaR chains are deliberately invalidated by hash or inventory defects. |
| `data_type_complexity` | 4 | 1 | Nested JSON graph feeds JSON and TSV evidence. |
| `data_complexity` | 5 | 1 | Four chains, four stages, claim permissions and upstream links interact. |
| `environment_complexity` | 3 | 1 | Offline deterministic hashes and explicit stage order are required. |
| `mathematical_complexity` | 4 | 1 | A weakest-link claim lattice is combined with robust policy threshold ranking. |
| `long_horizon_complexity` | 5 | 1.5 | Downstream permissions cannot exceed any upstream stage. |
| `safety_risk` | 4 | 1 | Human review and stop conditions remain mandatory before operational handoff. |

## Interactions

- `long_horizon_x_tool_orchestration`
- `judgment_x_noisy_evidence`
- `high_stakes_safety_review`

## Selected modules

### horizon
- `horizon_end_to_end_claim`: `{}`
### judgment
- `judgment_claim_permission_lattice`: `{}`
- `judgment_causal_boundary`: `{}`
### data
- `data_evidence_graph_join`: `{}`
### tooling
- `tool_version_and_interface_drift`: `{}`
### math
- `math_model_selection_and_sensitivity`: `{}`
- `math_robust_scenario_optimization`: `{}`
### environment
- `environment_offline_setup`: `{}`
### safety
- `safety_human_approval_gate`: `{}`
