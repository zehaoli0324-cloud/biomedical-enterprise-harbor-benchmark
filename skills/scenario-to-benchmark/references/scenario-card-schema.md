# Scenario Card Schema

Use this compact YAML-like structure for a mined or compiled scenario. It is a design artifact, not a replacement for the benchmark task contract.

```yaml
scenario_id: C20-resistance-mechanism
status: candidate # candidate | needs-data | contract_only | ready
source_scenarios: [C20, M4, C18, C19, D3, R2, R6]
domain: life_sciences
stage: master_phd
research_role: functional_genomics_analyst
scientific_context:
  object: drug-treated human tumour cells
  question: which target merits single-gene resistance validation?
  decision: go/no-go for the next validation experiment
  consequence_of_error: false hit, wasted validation, or causal overclaim
workflow_handoffs:
  - from: pooled_screen
    to: transcriptome
    artifact: candidate_gene_table
    invariant: gene identifiers and comparison direction agree
scientific_judgments:
  - experimental_unit
  - batch_identifiability
  - association_vs_causality
  - evidence_quality
agent_visible_inputs:
  - path: data/screen/
    schema: counts + sample metadata + library manifest
  - path: data/rnaseq/
    schema: reads/counts + reference manifest
  - path: data/literature/
    schema: records/full-text locators + claim list
hidden_truth:
  reference_route: independent analysis or expert adjudication
  withheld: labels, target ranking, injection tags
required_artifacts:
  - study_plan.yaml
  - evidence_table.tsv
  - result_table.tsv
  - claim_ledger.tsv
  - final_report.md
failure_injections:
  - id: metadata-conflict
    trigger: one swapped condition label
    expected_behavior: detect, log, and limit the claim
    verifier_signal: conflict_reported
failure_taxonomy: [F1, F4, F6, F9, F11, F12]
difficulty_modules:
  scenario: [scenario_omics_analysis]
  judgment: [judgment_experimental_unit, judgment_causal_boundary]
  noise: [noise_metadata_conflict]
release_gates:
  scientific_reality: pass
  observability: pending
  verifiability: pending
  naive_resistance: pending
open_questions:
  - What is the frozen reference version?
  - Which outputs are executable versus rubric-scored?
```

## Field rules

- `source_scenarios` must use IDs present in `data/scenario_inventory.csv`.
- Every `workflow_handoffs` entry needs an artifact and an invariant; otherwise the chain is only a list of tools.
- Every `scientific_judgment` must map to at least one observable output or verifier check.
- `hidden_truth.withheld` must not name information that is visible in filenames, constant columns, or prompt text.
- `failure_injections` must state the expected behavior, not only the corrupted input.
- Keep unresolved fields explicit with `pending`, `unknown`, or `needs-data`.
