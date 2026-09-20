# Candidate pools

This directory holds pre-release benchmark candidates. A workflow first expands into several distinct scientific decisions, then independent LLM judges review the linked card bundles before one candidate enters task compilation and model trials.

Each candidate bundle references:

- a workflow evidence card;
- a scientific scenario card;
- a scientific judgment card;
- a difficulty TOML;
- a compute and verification card.

The executable example in `literature-screening-m1/` contains three candidates from the same workflow family: protocol screening, budgeted full-text prioritization, and claim-level evidence audit.

```bash
python3.11 -m benchmark_builder.cli validate-candidates \
  candidate_pools/literature-screening-m1/candidate-set.json

python3.11 -m benchmark_builder.cli candidate-protocol \
  candidate_pools/literature-screening-m1/candidate-set.json \
  --out runs/literature-screening-m1/review-protocol.json
```

The protocol is provider-neutral. Run the three configured judge roles independently, combine their structured output into one review packet, then call `select-candidates`. See `docs/candidate-pipeline.md` for the full state transition.

## Enterprise batch

`enterprise-v1/` contains the differentiated matrix: 12 source benchmarks, 36 candidate decisions, and question briefs. The first implementation tranche is under `enterprise-v1/contracts/`: six cross-workflow task contracts with compiled manifests. EB001 and EB004 now have synthetic calibration fixtures and authored verifiers; the remaining four are still contract-only.

These are not yet released Harbor tasks. The batch status is `MIXED_CALIBRATION_AND_CONTRACT`: calibration-ready entries still need positive/negative/invariance controls and model trials, while contract-only entries additionally need an agent-visible fixture, hidden truth route, and independent verifier.
