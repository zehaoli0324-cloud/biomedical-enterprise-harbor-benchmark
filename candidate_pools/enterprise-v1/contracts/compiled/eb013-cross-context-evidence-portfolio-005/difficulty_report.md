# Difficulty report: eb013-cross-context-evidence-portfolio-005

- Title: Context-stratified evidence follow-up portfolio
- Domain: biomedical_enterprise
- Raw score: 3.75/5
- Adjusted score: 3.95/5
- Band: advanced
- Spec digest: `6bffdafac666ddf174fbf4958fb95e4b61dc616a0ac66f55e170006106b0d8d7`

## Dimensions

| Dimension | Level | Weight | Rationale |
| --- | ---: | ---: | --- |
| `scientific_scenario` | 5 | 1 | Synthetic multi-context evidence boundary with bounded independent follow-up. |
| `scientific_judgment` | 5 | 1 | Unsupported and conflicted contexts must remain explicit rather than pooled away. |
| `computational_difficulty` | 3 | 1 | Enumerate 32 follow-up portfolios under a deterministic objective. |
| `tool_call_complexity` | 3 | 1 | Offline JSON and keyed TSV contract. |
| `retrieval_complexity` | 3 | 1 | Resolve evidence roles and independence labels before aggregation. |
| `information_noise_complexity` | 4 | 1 | Related repeats and positive-but-insufficient evidence are deliberate distractors. |
| `data_type_complexity` | 3 | 1 | Context/group/effect evidence joined with follow-up options. |
| `data_complexity` | 5 | 1 | Independent groups, contexts, replacements and quality states share one budget. |
| `environment_complexity` | 3 | 1 | Deterministic offline execution and input hashes. |
| `mathematical_complexity` | 4 | 1 | Lexicographic supported/conflicted/insufficient portfolio optimization. |
| `long_horizon_complexity` | 4 | 1 | Evidence selection precedes context claim handoff. |
| `safety_risk` | 3 | 1 | Synthetic evidence planning only with human review boundary. |

## Interactions

- `judgment_x_noisy_evidence`

## Selected modules

### judgment
- `judgment_evidence_sufficiency_abstention`: `{}`
### data
- `data_context_stratified_concordance`: `{}`
### math
- `math_followup_information_gain`: `{}`
- `math_ex_ante_shared_setup`: `{}`
