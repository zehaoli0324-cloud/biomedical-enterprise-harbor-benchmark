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

The first tranche now has six materialized synthetic development/calibration slices. Re-run the deterministic control matrix for the two already-calibrated slices with:

```bash
python3 scripts/run_calibration_controls.py
```

The command records positive, negative, row-order invariance, and insufficient-evidence results under each task's `controls/` directory. A `CALIBRATED` control result does not imply model readiness; the reference/simple/abstain/template/target-model trial remains a separate release gate.

## Second materialization tranche

The remaining four candidates in `TRANCHE-001` are now materialized as synthetic
development fixtures and marked `READY_FOR_CALIBRATION`:

- `eb003-failure-recovery-003`: preserve failed computational branches and claim permissions across an equivalent fallback;
- `eb005-batch-normalization-002`: compare raw and control-adjusted Cell Painting profiles under batch confounding;
- `eb008-stock-route-001`: gate retrosynthesis routes on target identity, stock, reaction validity, and step budget;
- `eb010-next-batch-001`: select a legal next experiment batch under material, diversity, and budget constraints.

Each package now contains agent-visible data, verifier-only reference metadata,
an independent verifier, four declared control slots, and the six quality
cards. Their control and model-trial records remain `NOT_RUN` until the
calibration matrix and baseline/target-model trials are executed. The batch
report therefore records six materialized tasks while keeping publication
disabled.

## Batch startup protocol

Starting a benchmark batch is a staged authoring operation, not a single generation command. The tranche manifest is the selection control plane; the compiled batch report is an execution snapshot. A local materialized directory must not be counted as an official batch promotion until it is reflected in the tranche/contract manifest and the required gates have been rerun.

### 1. Select and freeze the tranche

Choose 4-8 candidates from `candidate_pools/enterprise-v1/`, preferably from distinct workflow families. Before selection, require the source ledger, REQ01-REQ14 coverage, enterprise-value decision, semantic-difference evidence, and an independent truth route. Record the batch in `candidate_pools/enterprise-v1/scale_tranche_<n>.json` and keep `candidate_pools/enterprise-v1/contracts/manifest.json` as the authoritative task status.

### 2. Validate the candidate batch

```bash
python3 scripts/validate_knowledge_base.py
python3 scripts/validate_candidate_matrix.py candidate_pools/enterprise-v1
python3 scripts/compile_enterprise_question_briefs.py
```

Candidates with unresolved critical requirements, fewer than 3 alternatives per source, fewer than two semantic differences, or no observable failure/artifact contract remain `DRAFT`, `REVIEW_REQUIRED`, or `CONTRACT_ONLY`.

### 3. Compile the contracts

```bash
python3 scripts/compile_contract_batch.py
```

This writes compiled manifests, difficulty reports, evaluation protocols and spec digests under `candidate_pools/enterprise-v1/contracts/compiled/`, plus `batch_compile_report.json`. `compiled_contract` is not a runnable Harbor task.

### 4. Materialize only selected tasks

For each selected contract, add `benchmarks/<task_id>/` with agent-visible data, `instruction.md`, task/scenario metadata, verifier-only reference data, an independent verifier, tests, controls and quality cards. Synthetic fixtures must remain labeled synthetic/calibration and must not be described as enterprise-internal data. The materialization helper currently used for the remaining TRANCHE-001 contracts is `scripts/materialize_enterprise_tranche_002.py`; it is a tranche-specific helper, not a general release command.

### 5. Calibrate and run baselines

```bash
python3 scripts/run_calibration_controls.py
python3 scripts/run_enterprise_baselines.py
```

Every materialized task needs positive, negative, invariance and insufficient-evidence controls. The baseline matrix must distinguish reference solution, simple legal baseline, always-abstain and template/keyword strategies; target-model trials are a separate step. A control or baseline pass does not grant `READY_FOR_HARBOR`.

### 6. Recompile and promote by evidence

Re-run `compile_contract_batch.py`, package-level tests and the isolation checks after materialization. Promote only when the manifest, controls, model trial, error attribution, holdout/contamination audit, license/privacy review and fixed-container Harbor replay all agree. Otherwise keep the task in `CONTRACT_ONLY`, `CALIBRATION_READY`, `EVAL_ONLY_UNTIL_CALIBRATED`, `NOT_RUN` or `BLOCKED`.

The current repository may contain uncommitted parallel materialization artifacts. Until those artifacts are reviewed and recorded in the official manifest, the committed tranche status remains the source of truth.
