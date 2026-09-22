# Difficulty report: eb015-real-source-replacement-gate-001

- Title: Real-source replacement release gate
- Domain: biomedical_enterprise
- Raw score: 3.906/5
- Adjusted score: 4.356/5
- Band: research-grade
- Spec digest: `65d06acbe15e1439825a08163092c6ffd359424c9d5752a13eabd0f1cd3329c3`

## Dimensions

| Dimension | Level | Weight | Rationale |
| --- | ---: | ---: | --- |
| `scientific_scenario` | 4 | 1 | Three public-source replacement tracks must be kept separate without upgrading metadata to scientific evidence. |
| `scientific_judgment` | 5 | 1.3 | Rights, hash and verifier blockers must remain distinct and claims must be bounded. |
| `computational_difficulty` | 4 | 1 | Per-source required-field and ordered-blocker computation is deterministic but multi-artifact. |
| `tool_call_complexity` | 3 | 1 | Offline JSON/TSV/Markdown delivery with an explicit nested contract. |
| `retrieval_complexity` | 5 | 1.2 | CRISPR, BBBC021 and Zenodo source records expose different publication, metadata and archive boundaries. |
| `information_noise_complexity` | 4 | 1 | A publication license, an archive MD5 and a metadata page are tempting but insufficient substitutes. |
| `data_type_complexity` | 4 | 1 | Nested source records, JSON contracts, TSV rows and bounded prose must agree. |
| `data_complexity` | 4 | 1 | Three task/source mappings carry independent rights, integrity and verifier state. |
| `environment_complexity` | 2 | 1 | The gate is deterministic and network-free. |
| `mathematical_complexity` | 3 | 1 | Ordered blocker classification and exact input-hash coverage are required. |
| `long_horizon_complexity` | 3 | 1 | The release plan must preserve the sequence from rights and hash freeze to verifier rebinding. |
| `safety_risk` | 5 | 1.3 | The main risk is publishing synthetic or incompletely licensed material as real scientific evidence. |

## Interactions

- `judgment_x_noisy_evidence`
- `retrieval_x_scientific_judgment`
- `high_stakes_safety_review`

## Selected modules

### retrieval
- `retrieval_provenance_temporal_boundary`: `{}`
### judgment
- `judgment_claim_transportability_boundary`: `{}`
