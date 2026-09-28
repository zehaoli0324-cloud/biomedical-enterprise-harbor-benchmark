# EB014-001 Trial Analysis

> Historical scope: this analysis applies to frozen contract v1.0.0. The
> clarified v1.0.1 contract explicitly lists all five output paths and requires
> a new target-model trial before any current-version difficulty claim.

## Result

- Trial: `gpt56sol-v1-001`, model `gpt-5.6-sol`.
- Raw result: `RAW_PASS`; unchanged-artifact frozen replay: PASS, no errors.
- Normal turn completion, exit code 0, no timeout; elapsed 564.69 seconds.
- Runner limit 900 seconds; full-turn adapter limit 840 seconds.
- Five required artifacts delivered. No artifact repair, contract relaxation or
  scientific-rule changes occurred during or after this trial.

This instance did not defeat the target model. It is evidence of successful task
completion in one local run, not an estimate of the model's general success rate.

## Decision Checks

| Check | Observed artifact result |
| --- | --- |
| Current claim ceiling | descriptive; no future result counted as initial evidence |
| Initial reproduction evidence | one independent group; duplicate report not counted twice |
| Exclusions | archived, wrong-population and future evidence rejected with reasons |
| First action | A-REPLICATE |
| Consistent replication | A-BRIDGE, with both bridge outcomes replayed |
| Inconsistent replication | hold immediately; no unnecessary additional cost |
| Full terminal coverage | three leaves, costs 4, 4 and 2 |
| Objective | worst resolved weight 5, worst cost 4, maximum two actions |
| Positive bridge outcome | transportable association permitted; causal claim still unknown |
| Negative outcome | dependent registered acceptance claims refuted, not opposite biological proof |
| Provenance | all six data-file hashes correct |

The trace shows input reads, direct construction of the result artifacts, and
JSON, ID, policy-key and hash checks. It does not show an exhaustive solver being
run by the model. The correct result therefore cannot be attributed to an observed
search implementation; it may have been derived directly from this small instance.
An initial git-status command failed because the workspace is not a repository;
the model recovered and completed. This was not a delivery or infrastructure failure.

## Difficulty Assessment

The independent authoring oracle enumerates only 12 legal policies in the base
instance. Most distracting actions are eliminated by a single explicit status,
group or dependency condition. There is one short evidence chain, binary outcomes,
and just two decision stages. Action/source names also hint at duplicate or future
roles. These features make the instance useful as a correctness anchor but do not
support calling it a strong difficulty discriminator.

The model handled the intended scientific boundaries, not merely output syntax.
Its audit text explains independence, target-scope limits, the distinction between
hypothetical and observed evidence, and why refutation is not opposite causal proof.
This is an agent review of observable prose; independent human review remains NOT_RUN.
No task contradiction or verifier defect was observed in this run; that is not proof
that all possible contract or input edge cases are covered.

Recommended next-version experiments, not implemented in this frozen trial:
multiple competing claim chains sharing one budget; measurement outcomes that leave
partial support rather than immediately resolving a premise; shared or conflicting
independence groups across chains; and neutral IDs with a label-invariance control.
Each experiment needs a new version, independent oracle, decision-flip controls and
its own target trial. Do not increase difficulty by hiding objective or output rules.

## Evidence and Limits

Raw manifest, verdict, event log, final response, frozen hashes and unchanged outputs
are archived under `trials/gpt56sol-v1-001/`; structured evidence is also in
`target_trial_evidence.json`. Adapter hashes observed during the run match post-run
hashes. A launch-time adapter hash was not separately saved; do not claim otherwise.

This was process-cwd local calibration, not container isolation. The recorded commands
show no deliberate parent-directory or network reads, but network-off was requested,
not externally enforced. Held-out model trials, cross-domain transfer, isolated
container replay and independent human scientific review remain NOT_RUN. Release
readiness remains false.
