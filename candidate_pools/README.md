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

`enterprise-v1/` contains the differentiated matrix: 12 source benchmarks, 40 candidate decisions, and question briefs. Four candidates were mined from existing seeds: RxRx signal/noise identifiability, CompBioBench replay provenance, REINVENT4 diversity coverage, and BayBE measurement value. The audit is recorded in `enterprise-v1/seed_mining_report.json`. The first implementation tranche is under `enterprise-v1/contracts/`: six cross-workflow task contracts with compiled manifests and synthetic fixtures. EB001 and EB004 have completed control calibration and author-side baselines; EB003, EB005, EB008, and EB010 are materialized with authored verifiers but their controls and model trials remain pending.

The second mined tranche is recorded in `enterprise-v1/scale_tranche_002.json`. `eb003-replay-provenance-004` and `eb009-diversity-coverage-004` are materialized as synthetic calibration tasks with independent verifiers and four controls; both remain evaluation-only until target-model trials and release review are complete.

These are not yet released Harbor tasks. The batch status remains `MIXED_CALIBRATION_AND_CONTRACT` for release-policy compatibility: all six entries are materialized, but four still need positive/negative/invariance/insufficient-evidence controls and model trials, and all six still require the remaining scientific, reproducibility, license, and claim-boundary reviews.

### Starting a batch

Use `scale_tranche_<n>.json` to select a 4-8 task tranche across workflow families. Validate the source/requirements matrix and candidate diversity, compile the selected TOML contracts, materialize only selected tasks under `benchmarks/<task_id>/`, then run controls, author-side baselines, target-model trials, isolation checks and Harbor replay. The authoritative state is `enterprise-v1/contracts/manifest.json`; `batch_compile_report.json` is a generated snapshot and local uncommitted materialization is not a promotion.

```bash
python3 scripts/validate_knowledge_base.py
python3 scripts/validate_candidate_matrix.py candidate_pools/enterprise-v1
python3 scripts/compile_enterprise_question_briefs.py
python3 scripts/compile_contract_batch.py
python3 scripts/run_calibration_controls.py
python3 scripts/run_enterprise_baselines.py
```

`compiled_contract`, `ready_for_calibration` and `CALIBRATED` are development states. They do not imply target-model success, enterprise adoption evidence, license/privacy approval or `READY_FOR_HARBOR`.
