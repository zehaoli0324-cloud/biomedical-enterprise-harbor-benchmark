# L4 tranche 005 difficulty and trial analysis

## Scope and interpretation

This tranche contains six L4 tasks. The first target-model run used `l4-v1` and
completed normally, but all six verifier failures were caused by an exact output
contract that did not expose the required decision enum or evidence labels. The
model reasoning was frequently conservative and semantically plausible; those
results are retained as contract-defect evidence, not counted as six scientific
mistakes. After the instruction/verifier contract was clarified and the task
version was advanced to `l4-v1-explicit-contract-revision`, all six revised local
trials passed their independent verifier. Both generations are packaged.

The revised runs were author-side `process_cwd_only` trials. They demonstrate
solvability and contract repair, but do not establish fixed-container or Harbor
release readiness. Every task remains `release_status=BLOCKED` until the required
source, practitioner, replay, and infrastructure gates are independently met.

## What makes each task hard

| Task | Scientific/operational difficulty | Observable trap or state transition |
| --- | --- | --- |
| `eb003-recovery-chain-005` | Recover from partial failure without changing question, estimand, reference, cohort, or provenance. | A successful-looking retry can still be scientifically drifted; the selected branch must preserve the claim and leave an auditable recovery ledger. |
| `eb005-normalization-hierarchy-003` | Join plate metadata to experiment hierarchy, exclude pilot/archived/QC-failing units, and compare normalization profiles without erasing phenotype direction. | A profile can improve a batch metric while reversing or over-correcting the biological effect; eligibility and direction are separate gates. |
| `eb008-route-portfolio-002` | Verify route, stock, target, reaction, and source independence, then select a portfolio under shared inventory. | A route may be locally feasible but globally incompatible; retracted, wrong-target, and duplicate evidence must not inflate quorum. |
| `eb010-next-batch-002` | Choose the next batch across scope, budget, group, incompatibility, coverage, and scenario utility constraints. | Current utility and future information value conflict; pilot or out-of-scope candidates must not enter a provisional production batch. |
| `eb011-measurement-request-005` | Rank measurements by expected value of information while accounting for correlation, feasibility, uncertainty, cost, and gating. | The best single measurement is not always the best feasible request; a deterministic tie-break is needed when scores are close. |
| `eb012-cross-handoff-audit-001` | Reconcile upstream normalization and route outputs before a cross-stage handoff. | One missing digest, stale status, or boundary-violating claim blocks the whole handoff even when local artifacts look reasonable. |

## Transferable difficulty dimensions

1. **Hidden multi-artifact state.** The answer is distributed across data joins,
   evidence ledgers, manifests, and review notes. A final winner alone is not
   sufficient; the verifier must inspect the intermediate gates.
2. **Eligibility versus selection.** Candidate-level validity, portfolio-level
   feasibility, and final deterministic selection are different predicates.
   Collapsing them is a reliable way to create plausible but wrong answers.
3. **Blocker precedence and calibrated abstention.** The model must hand off for a
   binding blocker, but must still decide when uncertainty is explicitly allowed
   and no hard constraint failed. “Human review” is not a universal answer.
4. **Claim-permission propagation.** A computational result can support an
   operational recommendation without supporting a causal, mechanistic, or
   laboratory claim. This boundary must propagate into the ledger and approval
   gate.
5. **Risk-aware constrained optimization.** Budget, shared resources, correlation,
   scenario robustness, effect retention, and tie-breaks turn a local score into
   a reproducible policy rather than a keyword match.
6. **Provenance and replay.** Version, digest, scope, source independence, and
   replay status are part of the decision state. A stale or inconsistent artifact
   is a blocker, not merely missing documentation.
7. **Contract precision without hidden rules.** Required enums and output paths
   must be explicit. The first six failures showed that a reasonable semantic
   answer can be rejected by an undocumented serialization detail; the fix is a
   contract revision plus unchanged-artifact replay, not a harder verifier.

## Trial evidence

| Evidence | Result | Meaning |
| --- | --- | --- |
| Initial target trials | 6/6 completed, 0/6 verifier pass | The model reached the task, but the contract under-specified exact decision/evidence labels. |
| Contract-revised target trials | 6/6 completed, 6/6 verifier pass | The revised contract is solvable and the local verifier accepts the model's artifacts. |
| Independent verification-agent audits | 6/6 pass | The task packages, controls, and verifier audits are internally consistent at author side. |
| Fixed-container/Harbor release | Not run / blocked | The current evidence is not a release claim. |

The correct conclusion is therefore **contract repaired and locally calibrated**,
not “the model was defeated six times” and not “the model is fully reliable.”
The next useful evidence is repeated held-out variants that preserve the same
contract while changing winners, blockers, and evidence order.

## SOP migration rule

The accompanying `l4-transferable-modules.json` registers five reusable modules:
minimal sufficient disclosure, contract equivalence and replay, local eligibility
versus global selection, cross-artifact consistency audit, and deterministic
tie-break. A future task may claim one of these modules only if it exposes the
relevant evidence, includes positive/negative/invariance/insufficient-evidence
controls, and records a single-factor mutation that flips the intended decision.
These modules should be combined with domain content, not used as formatting
obstacles or undocumented label traps.
