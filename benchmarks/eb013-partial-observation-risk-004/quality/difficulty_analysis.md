# Partial-Observation Risk Escalation

## Design Boundary

Predecessor: `eb013-shared-setup-routing-003`, whose valid GPT-5.6-sol trial passed.
This version does not modify that task, its verifier, or its recorded outcomes.
The new task is finite synthetic assay planning, not a real clinical recommendation.
Six hypothetical worlds are visible to the planner, but execution reveals only a
probe-specific label. This distinction is the principal scientific decision.

## Interacting Dimensions

| Dimension | New computation | Observable failure |
| --- | --- | --- |
| Information and long horizon | One action per observation equivalence class | Different actions in indistinguishable worlds |
| Mathematics and uncertainty | Exact CVaR tail mass, worst over three distributions | Nominal-only, mean-as-tail, or omitted boundary mass |
| Retrieval and provenance | Latest full evidence snapshot as of the decision date | Future revision or active fallback after withdrawal |
| Data joins and feasibility | Probe capabilities joined to actions and world reductions | Action used without its probe prerequisite |
| Retained resource timing | Policy-wide setup union paid before observation | Conditional setup payment or double charging |

Three probes induce different partitions, and four actions survive temporal
evidence resolution; the capability gate leaves 346 observation-consistent
candidate policies. Search size is modest by design. The difficulty is preserving
information, evidence, risk and budget semantics across the same decision.

## Measured Controls

The base optimum is P2 with a=B, b=A, c=B, d=C, setup cost 1.5, worst cost 3.5,
robust CVaR 0.215, and worst-model mean loss 0.1565.

| Single-factor change | Selected outcome | Interpretation |
| --- | --- | --- |
| Reveal the world with P0 | P0 with world-specific actions | Genuine information-value decision flip |
| Retain only nominal probabilities | P2 with a=B, b=B, c=D, d=C | Distribution-robust objective changes actions |
| Increase alpha to 0.9 | Same policy, CVaR 0.22 | Numerical sensitivity, not a decision flip |
| Reduce commitment budget to 2.0 | P0, both labels choose A | Setup commitments change the selected probe |
| Remove E's withdrawal | P0, both labels choose E | Temporal exclusion changes the optimum |
| Make total budget infeasible | Request information | Correct bounded abstention |
| Reorder inputs | Unchanged policy and values | Representation invariance |

Twenty pre-trial controls passed. Two independent exact implementations agree
on the base and seven variants: observation-first Decimal enumeration with sorted
tail integration, and world-first Fraction enumeration with convex threshold
minimization. These are automated crosschecks, not human or independent-agent
scientific review. Variants are author-side calibration controls, not completed
held-out target-model trials.

## Transferable Modules

The three new modules are registered individually with observable computations,
negative controls, decision-flip mechanisms and claim boundaries. The information
partition mechanism could transfer to diagnosis from coarse measurements or
dispatch from delayed signals; temporal tombstones could transfer to revoked
inventory or superseded evidence; robust tail risk could transfer to scenario
planning. These domain transfers have NOT been validated in this round.

The SOP now requires separate reporting of numerical sensitivity and decision
flips, and forbids counting the same error as independent failures in multiple
dimensions. The five-file output contract remains explicit and admits declared
representation equivalences. Trial results belong in `trial_analysis.md`, with
raw artifacts and unchanged-artifact frozen-verifier replay kept separately.
