# Difficulty report: eb010-closed-loop-ambiguity-004

- Title: Ambiguous policy replay with discovery and semantic abstention
- Domain: biomedical_enterprise
- Raw score: 4.704/5
- Adjusted score: 5.0/5
- Band: frontier
- Spec digest: `4fc361aa9baf24945ec2b81f75097d0e39776aaae41414191378fc79053fbe9f`

## Dimensions

| Dimension | Level | Weight | Rationale |
| --- | ---: | ---: | --- |
| `scientific_scenario` | 5 | 1.5 | The decision combines policy replay, semantic interpretation and conservative escalation. |
| `scientific_judgment` | 5 | 1.5 | Ambiguous language must block a high-utility record instead of being resolved opportunistically. |
| `computational_difficulty` | 4 | 1 | The verifier derives joins, hashes, semantic statuses and eligibility from nested inputs. |
| `tool_call_complexity` | 5 | 1 | The agent must discover nested inputs, inspect a manifest, compute hashes and emit four coordinated artifacts. |
| `retrieval_complexity` | 5 | 1 | The input schema and semantic mapping are discoverable but not restated in the instruction. |
| `information_noise_complexity` | 5 | 1 | Archived, leaking, ambiguous and low-signal records are all plausible distractors. |
| `data_type_complexity` | 4 | 1 | Nested JSON inputs must be reconciled with TSV evidence and structured provenance output. |
| `data_complexity` | 5 | 1 | Eligibility is a join across manifest, lexicon, records, replay arrays and numeric rules. |
| `environment_complexity` | 5 | 1 | Offline deterministic discovery and input hashing are decision-binding, not incidental metadata. |
| `mathematical_complexity` | 4 | 1 | Utility, spread, threshold and budget gates interact after semantic classification. |
| `long_horizon_complexity` | 5 | 1.5 | Discovery precedes interpretation, interpretation precedes eligibility, and ambiguity can terminate selection. |
| `safety_risk` | 4 | 1 | A forced interpretation can authorize an invalid resource-allocation plan. |

## Interactions

- `long_horizon_x_tool_orchestration`
- `judgment_x_noisy_evidence`
- `data_x_environment`
- `retrieval_x_scientific_judgment`
- `high_stakes_safety_review`

## Selected modules

### scenario
- `scenario_reproducibility_audit`: `{}`
### judgment
- `judgment_semantic_ambiguity_resolution`: `{}`
- `judgment_blocker_and_abstention`: `{}`
- `judgment_agent_planned_workflow`: `{}`
### horizon
- `horizon_adaptive_policy_replay`: `{}`
- `horizon_planning_stop_condition`: `{}`
### math
- `math_replay_stability`: `{}`
### tooling
- `tool_branching_pipeline`: `{}`
### retrieval
- `retrieval_schema_discovery`: `{}`
- `retrieval_inclusion_exclusion`: `{}`
### noise
- `noise_red_herring_records`: `{}`
### data
- `data_nested_manifest_join`: `{}`
- `data_text_and_metadata`: `{}`
### data_complexity
- `complexity_sparse_or_missing`: `{}`
### environment
- `environment_schema_discovery_under_offline`: `{}`
- `environment_offline_setup`: `{}`
### safety
- `safety_human_approval_gate`: `{}`
