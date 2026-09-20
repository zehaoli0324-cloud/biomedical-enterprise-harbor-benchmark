---
name: scenario-to-benchmark
description: Mine open scientific workflows into evidence-backed research scenarios, hard scientific tasks, failure modes, and benchmark contracts. Use when a workflow list, repository, protocol, paper, or toolchain must become a benchmark-ready task.
---

# Scenario To Benchmark

Use this skill when the input is a workflow or toolchain and the desired output is a scientific benchmark task. The central transformation is:

```text
workflow/tool -> researcher role -> scientific decision -> task -> observable artifact -> verifier
```

Do not equate a runnable pipeline with a research scenario. A pipeline is evidence about operations; the scenario must explain what a researcher is trying to learn or decide, what could make that decision invalid, and what artifact proves the work was done.

This skill owns authoring through a selected or compiled contract. Benchmark data materialization, isolated model execution, and submission scoring are downstream repository stages; do not claim a task is runnable merely because this skill produced valid cards.

## Modes

Choose the smallest mode that satisfies the request:

- **Mine**: identify candidate scenarios from workflow documentation, example data, notebooks, papers, and repository code. Produce a scenario brief and evidence ledger.
- **Select**: expand one workflow into three to five distinct research-decision candidates, materialize linked evidence/scenario/judgment/difficulty/compute cards, and select from independent reviews.
- **Compile**: turn one or more selected scenarios into a benchmark contract and a difficulty-config TOML that the repository's `benchmark_builder` can validate, score, and compile.
- **Audit**: review an existing scenario or task for scientific reality, observability, verifiability, leakage, naive shortcuts, and conclusion-boundary failures.

Read [references/evidence-extraction.md](references/evidence-extraction.md) when mining a new workflow. Read [references/scenario-card-schema.md](references/scenario-card-schema.md) when producing or reviewing a structured card. Read [references/candidate-selection.md](references/candidate-selection.md) when generating or selecting multiple candidates from one workflow.

## Stage contract

Move forward only through evidence-backed states:

```text
mined -> candidate_set -> selected -> compiled_contract
```

- `mined` proves what the workflow and sources support.
- `candidate_set` contains distinct scientific decisions, not prompt variants.
- `selected` means task-quality gates and independent review passed.
- `compiled_contract` freezes the chosen scenario and difficulty contract but is not yet a runnable benchmark.

Return the earliest honest state. Missing data, hidden truth, environment, or verifier work stays explicit; never promote status based on fluent prose.

## Non-negotiable distinctions

Keep these layers separate in every output:

1. **Operation**: what the tool does, such as align reads, rank guides, fit a model, or render a figure.
2. **Measurement**: what is observed or computed, such as an effect size, FDR, edit rate, or confidence score.
3. **Scientific decision**: what the researcher decides, such as whether a target is worth validating or whether a mechanism is identifiable.
4. **Claim boundary**: what the evidence does not establish, such as causality, clinical efficacy, or experimental confirmation.

If the source only supports an operation, mark the decision and claim boundary as unresolved. Never invent a scientific purpose from a tool name.

## Workflow

### 1. Establish provenance before interpretation

Create a source ledger before summarizing:

- source path or URL, repository/author, access date, commit or version;
- source type: README, tutorial, code, example data, paper, issue, or release;
- exact evidence locator: heading, file, function, notebook cell, table, or command;
- whether the evidence was inspected, executed, or only described;
- license and whether redistribution of the data is allowed.

Treat a README claim as weaker than an executed example. Treat a tool's output schema as evidence of an artifact, not evidence that the artifact is scientifically valid.

### 2. Reconstruct the research context

Answer these questions with citations to the source ledger:

- Who performs the work: undergraduate, master's student, PhD researcher, analyst, or PI?
- What object is being studied: sample, perturbation, gene, protein, image, spectrum, population, or paper?
- What upstream data and metadata are required?
- What decision is made at the end of this workflow?
- What downstream action changes if the decision is wrong?
- Which assumptions are scientific rather than merely technical?
- What would make the input **not analyzable**?
- Which result is a screening signal, which is a statistical result, and which would require experimental validation?

If two workflows are combined, require a shared object, shared decision, or explicit handoff artifact. Do not combine tools just because they belong to the same discipline.

### 3. Convert workflow steps into benchmark tasks

For each candidate task, write:

- a concrete research question;
- the agent-visible inputs and their schema;
- the scientific unit of analysis and independent replicate;
- the expected analysis branches and checkpoints;
- the required artifacts and their fields;
- the hidden truth or independent reference route;
- the error consequence if a decision is wrong;
- the minimum behavior on missing, conflicting, or insufficient input.

Prefer tasks where a locally plausible shortcut changes the scientific conclusion. Examples include cell-level pseudoreplication, a batch-confounded comparison, a correlation-only paper used as causal evidence, a high-scoring but unsafe guide, or a figure whose sample count disagrees with the code.

Do not make difficulty equal to the number of tools or prompt tokens. A hard task needs competing scientific choices, stateful dependencies, evidence ambiguity, or an auditable failure boundary.

### 3a. Diversify before selecting

For a workflow with more than one defensible research decision, produce three to five candidates before compilation. Vary the decision, unit of analysis, evidence ambiguity, error consequence, downstream handoff, or stopping rule. Reject candidates that vary only wording, tool count, data volume, or output format.

Materialize and select the five-card bundles using [references/candidate-selection.md](references/candidate-selection.md). Keep the full Pareto front even when one candidate is recommended. If no candidate is eligible, change only the card and defect named by `iterate-candidates`, then rerun validation and every independent review.

### 4. Map the task to failure and difficulty modules

Use the IDs in `docs/failure-taxonomy.md`, `config/module_catalog.json`, and the scenario inventory. Every selected module must have:

- a visible trigger in the input or environment;
- an expected correct behavior;
- a scoring signal or verifier check;
- a reason the failure matters scientifically.

Select dimensions in this order:

1. scientific scenario and scientific judgment;
2. data type and data complexity;
3. computation and mathematical/statistical choices;
4. tools, retrieval, and environment;
5. horizon, safety, and claim consistency.

Keep the scientific judgment high even when the execution is simplified. A small dataset with an ambiguous experimental unit is usually more valuable than a large dataset with a cookbook answer.

### 5. Compile through the existing pipeline

For a compiled candidate, use its selected TOML in the candidate pool. Promote it to `config/examples/` only when it becomes a maintained repository example. The spec must contain:

- `task.id`, title, domain, and `source_scenarios`;
- all twelve difficulty dimensions;
- module IDs that exist in `config/module_catalog.json`;
- data types and resource/network constraints.
- `[scenario].card` pointing to the mined scenario card; the card's source IDs must cover `task.source_scenarios`.

Run from the repository root:

```bash
python -m benchmark_builder.cli validate <task.toml>
python -m benchmark_builder.cli score <task.toml>
python -m benchmark_builder.cli compile <task.toml> --out <compiled-dir>
```

Include the resulting `spec_digest` in the scenario record or task review. The compiler report is a difficulty estimate, not evidence that the task is scientifically valid.

### 6. Apply release gates

Do not mark a candidate ready until it passes all applicable gates:

- **Scientific reality**: a real researcher would make this decision and a wrong answer would matter.
- **Observability**: the agent-visible materials contain enough evidence to reason, without revealing hidden labels.
- **Verifiability**: an independent oracle, invariant, or expert rubric can score the decision and key artifacts.
- **Identifiability**: the task does not demand a unique answer when the evidence supports several defensible answers; score equivalence classes or calibrated uncertainty.
- **Naive resistance**: lookup, constant-column, tool-name matching, and output-volume strategies do not solve it.
- **Reproducibility**: inputs, versions, parameters, resources, and failure behavior are fixed or recorded.
- **Claim safety**: the task does not silently turn computational evidence into an unapproved wet-lab or clinical instruction.

If a gate fails, return `candidate`, `blocked`, or `needs-data` with the missing evidence. Do not fill the gap with plausible prose.

### 7. Evaluate model submissions and iterate the task

Keep task difficulty dimensions separate from model-performance criteria. For model submissions, use the configured rubric in `[evaluation.criteria]`: scientific correctness, evidence grounding, experimental design, tool/trace reliability, artifact completeness, reproducibility, uncertainty/claim boundary, and safety/human review.

Use at least three independent judge roles (domain scientist, methods/reproducibility auditor, evidence/claim auditor). Each judge must return criterion-level 0–4 scores, confidence, artifact locators, rationale, and hard-gate booleans. Aggregate with criterion medians and weighted scores; do not average away failed critical criteria or hard gates. Numerical and schema checks remain programmatic; an LLM judge cannot replace an oracle.

After evaluation, run the controlled iteration loop:

1. `accepted`: freeze the task and its digest.
2. `adjudication_required`: resolve judge disagreement with an independent expert review.
3. `revise_required`: select the weakest criterion or failed gate and make one causal change.
4. Compare against the previous report; any forbidden criterion regression produces `rollback_required`.

Use the repository commands `protocol`, `evaluate`, and `iterate`. Read [references/evaluation-protocol.md](references/evaluation-protocol.md) when constructing judge packets or iteration records.

## Required deliverables

For **Mine**, deliver:

- scenario card;
- source/evidence ledger;
- candidate task graph;
- failure taxonomy mapping;
- open questions and data gaps.

For **Select**, deliver:

- candidate-set manifest with three to five non-duplicate research decisions;
- five linked card types for every candidate;
- provider-neutral review protocol and independent judge packet;
- selection report with exclusions, Pareto front, agreement, and recommendation;
- one-card iteration plan when no candidate is eligible.

For **Compile**, additionally deliver:

- selected benchmark TOML;
- compiled manifest and difficulty report;
- agent-visible versus hidden-truth separation;
- required artifact schema;
- verifier plan and at least one failure injection.

For **Audit**, report findings first, ordered by severity, with file/line or evidence locators, then assumptions and residual gaps.

## Example composition

For a gene-editing resistance study, a coherent chain can be:

```text
pooled screen -> transcriptome mechanism check -> guide risk review
-> amplicon editing quantification -> claim/figure/reproducibility audit
```

The benchmark question is not “run five tools.” It is “which target is sufficiently supported for the next validation step, and what remains unproven?”

Preserve `contract_only` or equivalent status until data, environment, hidden oracle, and verifier have been independently materialized and rerun.

The difficulty generator is intentionally downstream of this skill. Do not create a high difficulty TOML before the scenario card has a real research decision, scientific judgments, workflow handoffs, and release-gate evidence. A large tool chain without those fields is volume, not scientific difficulty.
