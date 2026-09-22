# Assay Policy Under Partial Observation and Distribution Shift

Create an executable, deterministic two-stage policy for this synthetic planning
problem. All world states and their hypothetical consequences are public for
planning, but the realized world state is NOT observed at execution time. Only
the chosen probe's observation label is revealed. States with the same label
MUST receive the same action. Do not choose a different probe after observation.
This is not an empirical efficacy claim or permission to perform an experiment.

## Inputs and Timing

Read all four JSON files in `data/`. `rules.json` gives states, uncertainties,
probability models, thresholds and budgets. `catalog.json` lists probes, their
observation maps and capabilities, and actions with setup families, execution
costs and required capabilities. `evidence.json` contains full, not incremental,
action-evidence snapshots. `output_contract.json` gives the output field registry.

For EACH action, first discard snapshots published after `decision_date`, then
select the largest `(published_at, revision)` pair. A selected withdrawn snapshot
disables the action. Never fall back to an older active snapshot after withdrawal.
If no snapshot is available, the action is unavailable. Every required capability
must be in the chosen probe's capabilities. These checks apply before optimization.

Choose one action for EVERY distinct observation label of the chosen probe.
Commit the union of all setup families used anywhere in that policy before any
observation. Pay each family once. Upfront cost = probe cost + union setup cost;
it must be <= commitment_budget. In each world, total cost = upfront cost + the
execution cost of its observation's action, and must be <= total_budget. Do not
sum execution costs over mutually exclusive worlds.

## Loss, Feasibility and Objective

For world s and axis k, residual(s,k) = max(0, initial_uncertainty[k] -
selected_action_snapshot.reductions[s][k]). Probes only reveal information; they
do not themselves reduce uncertainty. Loss(s) = max of the two axis residuals.
Both per-axis critical thresholds must hold in EVERY world, even low-probability
ones. Budget and capability gates are also hard constraints.

For EACH probability model, mean_loss = sum_s probability(s) * loss(s).
CVaR_alpha is the probability-weighted average of the worst `1-alpha` mass, NOT
the maximum loss, an unweighted average of worlds, or a conditional average of
only worlds strictly above the quantile. Sort losses descending and take exactly
`1-alpha` probability mass, taking a fractional mass from the boundary world.
Equivalently, minimize `t + sum_s p(s)*max(loss(s)-t,0)/(1-alpha)` over real t.
robust_cvar = max CVaR over the listed models; worst_mean_loss = max mean over
those models. Do not average the probability models or use only `nominal`.

Among feasible complete policies, lexicographically minimize:
1. robust_cvar;
2. worst_mean_loss;
3. maximum world total cost (`worst_cost`);
4. setup_cost;
5. probe_id;
6. sorted `(observation_label, action_id)` pairs.

All boundaries are inclusive. Decimal inputs are exact; use sufficient precision.
If no policy is feasible, request information instead of inventing an executable
policy. Report the best feasible policy separately for each probe as well.

## Required Outputs

Write these five files under `outputs/`. Do not wrap JSON files in markdown.
All names and full schemas are declared here; no prior task conventions apply.

The seven SELECTED fields are `probe_id` (string), `observation_policy` (object
mapping every observation label to an action ID), `setup_families` (unique string
array), `setup_cost`, `worst_cost`, `robust_cvar`, and `worst_mean_loss` (numbers).

`outputs/plan.json`: the SELECTED fields for the global winner, plus:
- `policies`: one object per catalog probe, each with `probe_id` and `best_policy`.
  `best_policy` contains all seven SELECTED fields, or is null if that probe has
  no feasible policy. Do not list all candidate policies.
- `risk_by_model`: one object per probability model for the global winner, with
  `model_id`, `mean_loss`, and `cvar`.
- `evidence_resolution`: one object per catalog action, with `action_id`,
  `revision` (selected integer or null), `status` (`active`, `withdrawn`, or
  `unavailable`), and `usable` (boolean; evidence availability only, independent
  of probe-specific capability eligibility).

`outputs/decision.json`: the same seven SELECTED fields plus `decision` (`execute_policy`
or `request_information`), `human_review_required: true`, and
`claim_boundary: "synthetic_planning_only"`.

`outputs/route.tsv`: header columns `state`, `observation`, `action_id`, `signal_residual`,
`selectivity_residual`, `loss`, `cost`. One row per world for the global winner.
Observation labels and actions must agree with the selected probe and policy.

`outputs/provenance.json`: `input_sha256` maps each of the four data filenames to its real
SHA-256; also include `rules_version` from rules.json, `network: "off"`, and
`deterministic: true`.

`outputs/audit.md`: a nonempty account of evidence resolution, the observable policy,
cost timing, tail-risk calculation and why the alternatives lose. Prose is for
review; correctness is determined by structured data, not keyword matches.

If no global winner exists, SELECTED is `probe_id: null`, `observation_policy: {}`,
`setup_families: []` and all four numbers null. `risk_by_model` is empty and the
TSV contains only its header. Still report every probe and evidence resolution.

Allowed equivalences: JSON key order, keyed row order, setup family order, finite
numeric strings, and optional `data/` prefixes on hash keys. Extra explanatory
JSON keys are allowed, but extra policy observation keys are not. Numerical
tolerance is 1e-6. Missing values are never inferred; duplicate keys/rows, nonfinite
numbers, wrong hashes, and hidden-world-conditioned policies are rejected.
