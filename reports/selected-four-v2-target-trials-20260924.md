# Selected Four v2 Target Trials

Model: `gpt-5.6-sol`  
Date: 2026-09-24

| Task | Effective result | Valid model defeat | Interpretation |
|---|---|---:|---|
| `eb006-research-completion-011` | Scientific fail | Yes | The model misclassified registered-donor missingness and repeated the error in two input replays. |
| `eb013-cross-context-evidence-portfolio-005` | Raw pass | No | The model solved the expanded static portfolio search. |
| `eb014-sequential-evidence-feedback-002` | Pass after contract replay | No | The complete six-action scientific path was correct; the raw failure was path-prefix normalization. |
| `eb015-real-source-replacement-gate-001` | Pass after contract replay | No | All nine decisions were correct; the raw failure came from undeclared exact-shape and exact-phrase checks. |

The first `v2-001` attempts are excluded because the nested Codex process was blocked before task execution. The `v2-002` artifacts are preserved under `/Users/zehaoli0324/harbor-runs/selected-four-target-v2`.

The verifier repairs were replayed against the original, unchanged model outputs. `eb014` and `eb015` then passed. `eb006` still failed on four scientific status mismatches after its harmless extra provenance metadata was accepted.

## Abstention Surface

The four tasks no longer reward blanket abstention. Observable score fractions are 97.22%, 100%, 100%, and 100%, respectively. Oracle, no-op, key mutation, blanket-abstain, wrong-abstention, and correct mixed-behavior controls pass their declared expectations.

## Next Difficulty Revision

- `eb013`: replace more static enumeration with observation-contingent portfolio routing, compatibility constraints, and an executable perturbation replay.
- `eb014`: add multiple observation-dependent branches and delayed evidence interactions while keeping every required branch data-backed; do not inflate length with unsupported questions.
- `eb015`: add chained source-to-file-to-analysis lineage, inherited rights constraints, and controlled hash/rebinding mutations while keeping all cases decidable from supplied manifests.
- `eb006`: retain the paired-donor and assay perturbation design; add a second independently computed evidence family only after supplying complete data for it.

These are difficulty changes, not additional abstention opportunities. Any deliberately insufficient unit remains capped as a small minority and is tested by the abstention variants.
