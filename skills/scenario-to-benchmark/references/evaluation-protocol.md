# Evaluation Protocol Reference

This skill delegates execution to the repository's `benchmark_builder` and keeps the LLM provider out of the task contract. The provider adapter must produce the JSON packet described by the compiled `evaluation_protocol.json`.

## Judge separation

- Domain scientist: scores experimental unit, contrasts, mechanism interpretation, causal boundary, and scientific usefulness.
- Methods/reproducibility auditor: scores design matrix, tool applicability, parameters, failure recovery, artifacts, versions, and rerun conditions.
- Evidence/claim auditor: scores source existence, locator accuracy, numeric traceability, uncertainty, and claim strength.

Judges must receive the same agent-visible submission and task evidence. They must not receive hidden reference labels, another judge's output, or the intended score.

## Score interpretation

Use the full configured scale and give evidence for every score:

- `0`: absent, fabricated, or scientifically invalid;
- `1`: mostly incorrect or non-auditable;
- `2`: partial and plausible but material gaps remain;
- `3`: acceptable for the stated task and evidence boundary;
- `4`: strong, complete, independently auditable, and appropriately cautious.

The configured `minimum_score` and `critical` flags control acceptance; do not invent a new threshold in a judge response.

## Iteration diagnosis

Map a weak criterion to one action only:

| Weak criterion | First action |
| --- | --- |
| scientific correctness | inspect task semantics, experimental unit, contrast, and reference oracle |
| evidence grounding | add locators, source checks, or claim-level verifier |
| experimental design | add a confound/replicate control or revise the design contract |
| tool and trace reliability | pin versions, parameter schema, and failure-return checks |
| artifact completeness | repair required-artifact fields or intermediate handoff |
| reproducibility | add checksum, lockfile, resource and rerun checks |
| uncertainty and claim boundary | add negative/insufficient-input case and downgrade rule |
| safety and human review | tighten human-approval gate and remove operational overreach |

Do not change data, prompt, verifier, and rubric in one round. A score change must remain attributable.
