# EB014: Evidence Gaps and Conditional Follow-up

Author-facing record; this file, tests, controls, quality and verifier-only files are
not solver inputs. The solver receives instruction.md and data/ only.

This synthetic task reconstructs acceptance evidence from measurements, checks
source time/scope/independence, propagates premise blockers to registered claims,
and selects a two-stage research policy. It tests reasoning about evidence gaps,
not biological validity of the deliberately simplified acceptance rules.

Difficulty budget: research_minimum_additional_evidence is primary;
judgment_claim_transportability_boundary and horizon_adaptive_research_priority
are secondary; retrieval_independence_quorum is a supporting constraint.

## Authoring Checks

From the repository root:

```sh
.venv/bin/python -m pytest benchmarks/eb014-evidence-gap-followup-001/tests/test_verifier.py -q
python3 scripts/calibrate_evidence_gap_followup.py
python3 -m benchmark_builder.cli compile candidate_pools/enterprise-v1/contracts/eb014-evidence-gap-followup-001.toml --out candidate_pools/enterprise-v1/contracts/compiled/eb014-evidence-gap-followup-001
```

Calibration writes author-only reference, control results and the pretrial hash
freeze. Do not rerun a freeze over historical model trials; the script guards
known trial evidence paths. Tests call the non-persisting calibration function.

Every newly authored or substantively revised version must proceed directly to a
target-model trial and analysis after the preflight freeze. Controls alone do not
complete authoring. Use a fresh trial ID, the full-turn adapter, and the established
900-second runner / 840-second adapter budget. Archive with
`scripts/record_evidence_gap_trial.py TRIAL_DIRECTORY`, inspect the actual artifacts
and trace, then write `quality/trial_analysis.md`. An infrastructure blocker must
be recorded, not counted as a scientific failure. Never edit a live frozen task.

Verifier: recursive Decimal enumeration with full terminal replay.
Cross-check: independent Fraction evidence reconstruction and two-stage product
enumeration in scripts/audit_evidence_gap_oracle.py. No reference is consumed by
the verifier. Audit prose is not scientifically validated by a keyword search.

## Status

24 artifact checks and 8 input variants pass. Six variants change the policy;
row ordering is invariant and feedback relabeling preserves the decision semantics.
Two independent algorithms agree on the optimal policy and objective for the
base task and all eight variants.

Target-model trial `gpt56sol-v1-001`: gpt-5.6-sol RAW_PASS in 564.69 seconds;
unchanged-artifact frozen replay also PASS. This instance did not defeat the model.
See quality/trial_analysis.md for decision-level findings and difficulty limitations.
Human scientific review, isolated container replay, held-out model trials and
cross-domain transfer remain NOT_RUN. The task is not release-ready.

## Design Repairs

- Removed fixed first-action and claim-ceiling answer fields from the draft.
- Replaced pre-labeled premise support with measurements and metadata joins.
- Replaced guaranteed-positive permission optimization with public worst-case
  question-resolution weights: negative results also resolve a question.
- Separated current claim ledger from hypothetical terminal outcomes.
- Made stop-on-resolution explicit; no hidden no-waste preference.
- Checked exact record/branch coverage, duplicate keys, objective values,
  provenance, finite numbers and registered representation equivalences.

Reusable authoring rules are recorded in the EB014 addendum of
docs/enterprise-harbor-sop-v1.1.md and config/reusable_difficulty_modules.json.
