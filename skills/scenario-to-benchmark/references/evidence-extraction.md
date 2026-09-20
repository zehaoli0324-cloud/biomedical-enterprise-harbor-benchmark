# Workflow Evidence Extraction

Use this reference while mining a workflow. The aim is to recover the research context without overstating what the source proves.

## Evidence tiers

| Tier | Source evidence | What it supports |
| --- | --- | --- |
| E0 | Tool name, landing page, marketing text | Candidate operation only |
| E1 | README usage, CLI help, declared inputs/outputs | Operation and artifact schema |
| E2 | Tutorial, notebook, example data, test fixture | Example analysis path and assumptions |
| E3 | Published methods, benchmark, validated reference workflow | Research intent and domain-specific decision, subject to scope |
| E4 | Executed run with fixed inputs and inspected outputs | Reproducible behavior for that version and input |

Do not promote E0/E1 evidence into a causal or clinical claim. When evidence tiers disagree, preserve the disagreement and explain which source controls the benchmark contract.

## Extraction table

For each workflow, fill one row per claim:

| Field | Question |
| --- | --- |
| `workflow_id` | Which repository/tool/workflow is this? |
| `operation` | What transformation does it perform? |
| `input_schema` | What files, columns, identifiers, and versions are required? |
| `output_schema` | What files and fields are produced? |
| `research_role` | Where does this occur in a real research project? |
| `decision` | What choice does a researcher make using the output? |
| `assumption` | What must be true for that choice to be valid? |
| `failure_consequence` | What scientific or operational harm follows from an error? |
| `evidence_tier` | E0–E4 |
| `locator` | URL/path plus heading, function, cell, or line |
| `verification_status` | inspected, executed, inferred, or unknown |

## Questions that expose hidden context

Ask these before naming a scenario:

1. What is the independent unit: donor, animal, well, sample, perturbation, sequence, image, field, or paper?
2. What is the null or comparison: vehicle, untreated, single agent, batch-matched control, reference sequence, or spatial holdout?
3. What is the decision threshold and who set it?
4. What would count as a negative result or an unidentifiable result?
5. Which metadata change would invalidate the analysis?
6. Does the output support screening, prioritization, mechanism, or validation?
7. What alternate explanation could produce the same output?
8. Which next experiment would distinguish the leading explanations?

If the source does not answer these questions, record them as data requirements or benchmark ambiguity. Do not silently choose defaults.

## Workflow-to-context heuristics

These are prompts for investigation, not conclusions:

- QC/alignment/counting workflows often hide sample identity, batch, library, and reference-version decisions.
- Differential-expression or enrichment workflows hide experimental unit, design matrix, contrast direction, and multiple-testing choices.
- Guide-design workflows hide target transcript, PAM/reference version, off-target policy, and whether ranking is actionable.
- Structure prediction/docking workflows hide chain/ligand identity, confidence interpretation, and the distinction between prediction and experiment.
- Image segmentation/tracking workflows hide field-of-view sampling, scale calibration, denominator choice, and manual validation.
- Literature workflows hide inclusion criteria, duplicate records, source authority, and claim entailment.
- Writing/figure workflows hide provenance mapping, unit/sample-count consistency, and claim strength.

Treat these as hypotheses to verify against the actual source, not as automatic labels.
