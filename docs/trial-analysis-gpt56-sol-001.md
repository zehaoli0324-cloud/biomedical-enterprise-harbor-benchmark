# GPT-5.6 Sol Trial Analysis

## Scope

The four tranche-002 enterprise tasks were run through the local Codex CLI adapter using `gpt-5.6-sol`. Trial archives are outside the repository at `/private/tmp/benchmark-runs/enterprise-v1-gpt56-sol-20260921/`.

All four agents exited with code 0 and wrote every required artifact. Therefore these are completed agent trials, not provider or runner failures. The hidden verifier rejected all four submissions.

## Findings

| Task | Verifier outcome | First actionable finding | Interpretation |
| --- | --- | --- | --- |
| EB003 | fail | Missing literal `not causal`; manifest provenance mismatch | Claim boundary was semantically present, but the verifier depended on undocumented wording and an undocumented exact manifest shape. |
| EB005 | fail | Batch report schema mismatch; missing `over-correction`; provenance mismatch | The model computed a richer report, but the instruction did not declare the verifier's exact summary fields or phrase. |
| EB008 | fail | Route compliance mismatch; stock evidence column/name mismatch; missing exact approval phrases | The model selected the correct route and recorded equivalent evidence, but the verifier was schema- and wording-brittle. |
| EB010 | fail | Selected batch differed from hidden `reference_batch` | The model found a feasible lower-uncertainty batch. The instruction did not define a unique objective/tie-break, so this is a single-answer contract defect before it is a model failure. |

## Required workflow changes

Before another target-model run, run the model-independent enterprise contract audit: declare output schemas in `task.yaml`, document all required paths and claim/provenance fields in `instruction.md`, replace exact prose checks with structured fields, and define an objective/tie-break whenever one hidden answer is required. Re-run author-side reference, legal-alternative, abstain, and template controls before comparing models.

The four results remain valid calibration evidence for the current contracts, but must not be reported as four clean measures of GPT-5.6 Sol scientific difficulty.

## Contract revision outcome

The task instructions now declare full output paths and required fields, EB010
declares a unique objective and tie-break, and the verifiers accept documented
equivalent provenance and evidence schemas instead of exact prose. Positive,
negative, invariance, and insufficient-evidence controls pass for all four
tasks.

A fresh `gpt-5.6-sol` Codex CLI run is archived at
`/private/tmp/benchmark-runs/enterprise-v1-gpt56-sol-20260921-revised/`.
All four model processes exited with code 0. EB010 passed immediately. EB003,
EB005, and EB008 initially exposed three remaining verifier compatibility gaps
(`input_hashes` list, `inputs` mapping, and equivalent stock/reaction evidence
language); after those contract fixes, the unchanged trial outputs pass all
four verifiers. The corrected outcome is therefore 4/4 verifier pass after
contract revision, not four model failures.

## Calibrated scientific difficulty

The difficulty compiler was re-matched to the materialized fixtures rather
than the source workflow's full theoretical complexity:

| Task | Primary scientific modules | Compiled band | Interpretation |
| --- | --- | --- | --- |
| EB003 | claim-preserving recovery, failure recovery, version/interface drift | advanced (3.360) | Competing successful fallbacks differ in scientific meaning. |
| EB005 | batch identifiability, hierarchical sensitivity, replicate/batch structure | advanced (3.440) | Competing corrections trade control drift against phenotype retention. |
| EB008 | route feasibility, evidence quality, human approval gate | advanced (3.540) | Reaction validity is derived from step-level chemistry evidence. |
| EB010 | value of information, batch acquisition under uncertainty, branching experiments | advanced (3.440) | Utility combines exploration, gain, failure risk and redundancy. |

These bands describe the current fixtures. Increasing prompt length, artifact
count, or verifier strictness must not be used to raise them.

The scores above refer to task version `0.2.0`. The prior GPT-5.6 Sol trials
used version `0.1.0` and are retained only as historical contract evidence;
they do not calibrate the increased scientific difficulty.

## Task v0.2.0 target-model trial

A new Codex CLI run using `gpt-5.6-sol` is archived at
`/private/tmp/benchmark-runs/enterprise-v1-gpt56-sol-20260921-v02/`. EB003,
EB005 and EB010 passed on the first hidden-verifier execution. EB008 selected
the correct route and documented the correct stock and step-level chemistry
gates, but the first verifier required canonical fields to be duplicated in
`stock_compliance.json` despite the instruction allowing equivalent fields
across the declared artifacts. The verifier was corrected to validate the
same scientific semantics across the JSON and TSV outputs; the unchanged
model artifacts then passed replay.

The current outcome is therefore 4/4 scientific decisions correct in one
trial per task, with one contract replay. These tasks now contain activated
scientific judgment modules and reject the simple, abstention and template
baselines, but a single strong-model pass does not establish target-model
discrimination. Keep the `advanced` structural band provisional until
repeated trials and independent domain review are complete.

## Local runner versus TB-Science

The local run used the repository's process backend. It kept `verifier.py`,
`tests/`, and `verifier_only/` out of the copied workspace, but the verifier
was invoked by the host runner after the model process. This is weaker than
TB-Science separate verifier mode, where the agent container is torn down and a
clean verifier container sees only declared artifacts and baked-in tests.

The tranche also had no completed oracle/nop control calibration before the
target-model run, and no `harbor analyze` trajectory review. Those are process
gaps, not model failures. A release-grade rerun should use the Harbor layout and
separate verifier mode, run oracle and nop first, then analyze the target trial
trajectory before updating difficulty or training claims.
