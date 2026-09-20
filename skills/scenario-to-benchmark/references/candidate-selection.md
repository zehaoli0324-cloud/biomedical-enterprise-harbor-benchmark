# Candidate Cards And Selection

Use this reference when one workflow should produce several benchmark candidates before one is materialized. The purpose of the pool is to compare different **research decisions**, not several phrasings of one prompt.

## Card graph

Each candidate is a bundle of five linked cards:

```text
workflow evidence card
  -> scientific scenario card
  -> scientific judgment card
  -> difficulty card
  -> compute card
```

- `workflow-evidence-card.v1` records operations, source locators, evidence tiers, verification status, and unsupported inferences. Several candidates from one workflow may share it.
- The scientific scenario card uses the YAML contract in [scenario-card-schema.md](scenario-card-schema.md). It defines role, object, question, decision, consequence, handoffs, and release gates.
- `scientific-judgment-card.v1` gives each judgment a decision, failure consequence, observable, verifier, and claim boundary. It must cover every judgment named by the scenario card.
- The difficulty card is the existing benchmark TOML. Its `[scenario].card` must reference this candidate's scenario card.
- `compute-card.v1` defines the environment, resource budget, executable stages, failure behavior, and programmatic checks. Network, CPU, and memory must agree with the TOML constraints.

The `benchmark-candidate-set.v1` manifest references these files. Content digests are computed during validation; do not manually copy card content into the manifest.

## Generate a useful pool

Generate three to five candidates for each sufficiently rich workflow. Vary at least two of these axes:

- the consequential scientific decision;
- the unit of analysis or independent replicate;
- evidence ambiguity or identifiability;
- the failure consequence;
- the downstream handoff or stopping rule.

Do not treat tool count, prompt length, record count, or cosmetic output format as a variation axis. Reject semantic duplicates before paying for judge reviews. A candidate that cannot name an independent verifier route remains a scenario hypothesis, not a selectable benchmark candidate.

Keep hidden truth out of every card a candidate judge sees. The card may describe the reference **route**, but not labels, injected-record identities, expected rankings, or secret thresholds.

## Review protocol

Run three reviews independently:

1. domain scientist;
2. benchmark and measurement methodologist;
3. compute, verifier, and reproducibility auditor.

Each judge scores every candidate from 0 to 4 on scientific reality, research value, scientific judgment, observability, verifiability, naive resistance, compute feasibility, reproducibility, and calibrated difficulty. Every score must cite a card field or source locator. Judges must not see another judge's output or the generator's hidden reasoning.

All hard gates must pass. Criterion floors are applied before overall score, so high scores cannot compensate for an unreal scenario, hidden-truth leakage, or an unexecutable task.

## Selection

Selection follows this fixed sequence:

1. remove candidates with failed hard gates;
2. remove candidates below any criterion floor;
3. compute the Pareto front over scientific reality, scientific judgment, verifiability, naive resistance, compute feasibility, and calibrated difficulty;
4. require judge agreement on every criterion for a recommendation;
5. use declared criterion weights only to choose one recommendation within the agreed Pareto front.

Always retain the full Pareto front in the report. A resource-heavy but scientifically distinctive candidate and a cheaper, more verifiable candidate may both be valuable; the recommendation is an operational next choice, not proof of universal superiority.

## Commands

```bash
python3.11 -m benchmark_builder.cli validate-candidates <candidate-set.json>
python3.11 -m benchmark_builder.cli candidate-protocol <candidate-set.json> --out <review-protocol.json>
python3.11 -m benchmark_builder.cli select-candidates <candidate-set.json> --judgments <reviews.json> --out <selection.json>
python3.11 -m benchmark_builder.cli iterate-candidates <candidate-set.json> --selection <selection.json> --out <iteration.json>
```

`iterate-candidates` changes one named card for one causal defect. After revision, rerun validation and all independent reviews because the candidate-set digest changes.

When a candidate is selected, compile the selected difficulty-card path from the selection report through the normal `validate`, `score`, and `compile` commands. Then run model trials and submission evaluation. Candidate review evaluates the **task design**; trial evaluation evaluates a **model submission**. Do not reuse one as the other.
