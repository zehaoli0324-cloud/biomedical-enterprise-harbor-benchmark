# Task Pipeline v2

This repository now treats task authoring and task release as separate state machines. The pipeline gate is fail-closed and does not infer scientific validity from a static package pass.

## Commands

Run one package and write a full report plus build manifest:

```bash
python3 scripts/check_task_pipeline.py \
  benchmarks/<task-id> \
  --output reports/<task-id>-pipeline.json \
  --manifest-out benchmarks/<task-id>/quality/build_manifest.json
```

Run the explicit formal release scope (the registry is authoritative; Git tracking alone is not promotion):

```bash
python3 scripts/run_task_pipeline.py \
  --formal-only \
  --output reports/task-pipeline-formal.json
```

Run the complete working-tree candidate scope:

```bash
python3 scripts/run_task_pipeline.py \
  --all \
  --output reports/task-pipeline-working-tree.json
```

## Status axes

The report keeps four axes independent:

- `pipeline_status`: whether the package can be built and its visible/hidden boundaries are coherent;
- `evidence_status`: whether the contract and evidence mapping are present;
- `review_status`: whether a named scientific review has been completed;
- `release_status`: whether all dynamic, source, human, and archive gates are complete.

A package can be `DEVELOPMENT_BUILT` and `STATIC_REVIEW_PASS` while remaining `NOT_RUN` and `BLOCKED`. This is the expected state for calibration tasks.

## Hash binding

Each report contains a `task_build_manifest.v1` object with:

- the task ID and task version;
- the current Git commit when available;
- data and contract fingerprints;
- SHA-256 for every non-cache file in the package.

Trial and release reports must retain these values. A later data, contract, verifier, or instruction change supersedes earlier trial evidence.

## Fail-closed rules

The gate blocks on task identity drift, verifier/instruction/data-copy drift, missing contract files, missing source-freeze evidence, missing named scientific review, or missing explicit dynamic gate records. It never upgrades `NOT_RUN`, synthetic fixtures, or infrastructure failures into release evidence.

`config/task_scope.v1.json` is the authoritative scope registry. A package may be committed for auditability while remaining `candidate_only`.
