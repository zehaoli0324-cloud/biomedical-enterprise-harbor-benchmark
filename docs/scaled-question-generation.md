# Scaled question generation

## Capacity and batching

The authoring pipeline can generate 3-5 distinct candidate decisions per source workflow. With the current registry of 12 enterprise benchmarks, the first matrix contains 36 candidates. This is a candidate-generation capacity, not a promise that 36 runnable tasks are ready for release.

For review and implementation, use tranches of 4-8 candidates. A tranche should cover different workflow families and should not contain multiple surface variants of one decision. The first tranche is recorded in [`candidate_pools/enterprise-v1/scale_tranche_001.json`](../candidate_pools/enterprise-v1/scale_tranche_001.json).

## Difference contract

Every candidate must specify the independent unit, business decision, handoff, error consequence, failure injections, required artifacts, claim boundary, and GPT difficulty mechanism. The generator and validator reject candidates that:

- have fewer than three semantic axes;
- are duplicates on decision, unit, and handoff;
- differ on fewer than two semantic axes within a source workflow;
- lack an observable failure injection or artifact contract.

Changing only the prompt, file name, company label, output format, data volume, or random seed does not create a new question.

## Enterprise realism and GPT difficulty

The candidate cards are grounded in the repository's source and workflow registries, enterprise attribution class, named role, downstream handoff, and failure consequence. They also encode stateful dependencies, competing decisions, abstention/hold behavior, evidence boundaries, and shortcut probes. This keeps difficulty attached to scientific reasoning and auditable artifacts rather than token count or tool count.

## Commands

```bash
python3 scripts/generate_enterprise_candidate_cards.py
python3 scripts/validate_candidate_matrix.py candidate_pools/enterprise-v1
python3 scripts/compile_enterprise_question_briefs.py
```

The question briefs are `CONTRACT_ONLY`. Before a brief becomes a runnable Harbor task, add its data card, hidden truth/oracle, verifier, controls, reproducibility manifest, and model-trial record.
