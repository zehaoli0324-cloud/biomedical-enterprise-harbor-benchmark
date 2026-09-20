# Project brief

## Question

Prioritize candidate targets for an expert-reviewed follow-up on human cancer drug resistance. The output is a computational prioritization, not a causal conclusion.

## Pre-registered baseline score

Use this transparent score only after input and provenance checks:

`0.35 * screen_strength + 0.25 * transcript_support + 0.20 * evidence_support + 0.20 * reproducibility`

Risk and uncertainty are decision gates, not hidden bonus terms. A batch-confounded signal cannot be `go`; a missing critical measurement cannot be treated as zero.

## Decision labels

- `go`: suitable for expert review as the leading computational candidate.
- `hold`: potentially useful but a documented issue must be resolved first.
- `no_go`: fails a hard scientific or safety constraint in this slice.
- `uncertain`: insufficient evidence to make a defensible ranking decision.

## Scope boundary

Do not provide clinical treatment advice, wet-lab parameters, guide sequences, or an executable validation protocol. State what an expert must review next.
