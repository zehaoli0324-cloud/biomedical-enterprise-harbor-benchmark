#!/usr/bin/env python3
"""Materialize the donor-stratified signal difficulty task."""

from __future__ import annotations

import json
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TASK = ROOT / "benchmarks/eb006-donor-stratified-signal-005"


OBSERVATIONS = """candidate_id,donor,state,condition,technical_replicate,adjusted_signal,qc_status
method_alpha,D1,early,control,1,1.00,PASS
method_alpha,D1,early,control,2,1.10,PASS
method_alpha,D1,early,treatment,1,1.70,PASS
method_alpha,D1,early,treatment,2,1.80,PASS
method_alpha,D2,early,control,1,1.10,PASS
method_alpha,D2,early,treatment,1,1.60,PASS
method_alpha,D3,early,control,1,1.00,PASS
method_alpha,D3,early,treatment,1,1.40,PASS
method_alpha,D4,early,control,1,1.20,PASS
method_alpha,D4,early,treatment,1,1.50,PASS
method_alpha,D1,late,control,1,1.10,PASS
method_alpha,D1,late,treatment,1,1.65,PASS
method_alpha,D2,late,control,1,1.00,PASS
method_alpha,D2,late,treatment,1,1.45,PASS
method_alpha,D3,late,control,1,1.20,PASS
method_alpha,D3,late,treatment,1,1.50,PASS
method_alpha,D4,late,control,1,1.10,PASS
method_alpha,D4,late,treatment,1,1.35,PASS
method_beta,D1,early,control,1,1.00,PASS
method_beta,D1,early,control,2,1.00,PASS
method_beta,D1,early,control,3,1.00,PASS
method_beta,D1,early,control,4,1.00,PASS
method_beta,D1,early,control,5,1.00,PASS
method_beta,D1,early,control,6,1.00,PASS
method_beta,D1,early,control,7,1.00,PASS
method_beta,D1,early,control,8,1.00,PASS
method_beta,D1,early,control,9,1.00,PASS
method_beta,D1,early,control,10,1.00,PASS
method_beta,D1,early,treatment,1,1.70,PASS
method_beta,D1,early,treatment,2,1.80,PASS
method_beta,D1,early,treatment,3,1.75,PASS
method_beta,D1,early,treatment,4,1.75,PASS
method_beta,D1,early,treatment,5,1.75,PASS
method_beta,D1,early,treatment,6,1.75,PASS
method_beta,D1,early,treatment,7,1.75,PASS
method_beta,D1,early,treatment,8,1.75,PASS
method_beta,D1,early,treatment,9,1.75,PASS
method_beta,D1,early,treatment,10,1.75,PASS
method_beta,D2,early,control,1,1.10,PASS
method_beta,D2,early,control,2,1.10,PASS
method_beta,D2,early,treatment,1,1.55,PASS
method_beta,D2,early,treatment,2,1.55,PASS
method_beta,D3,early,control,1,1.00,PASS
method_beta,D3,early,treatment,1,1.35,PASS
method_beta,D4,early,control,1,1.20,PASS
method_beta,D4,early,treatment,1,0.95,PASS
method_beta,D1,late,control,1,1.10,PASS
method_beta,D1,late,control,2,1.10,PASS
method_beta,D1,late,control,3,1.10,PASS
method_beta,D1,late,control,4,1.10,PASS
method_beta,D1,late,control,5,1.10,PASS
method_beta,D1,late,control,6,1.10,PASS
method_beta,D1,late,control,7,1.10,PASS
method_beta,D1,late,control,8,1.10,PASS
method_beta,D1,late,control,9,1.10,PASS
method_beta,D1,late,control,10,1.10,PASS
method_beta,D1,late,treatment,1,1.70,PASS
method_beta,D1,late,treatment,2,1.70,PASS
method_beta,D1,late,treatment,3,1.70,PASS
method_beta,D1,late,treatment,4,1.70,PASS
method_beta,D1,late,treatment,5,1.70,PASS
method_beta,D1,late,treatment,6,1.70,PASS
method_beta,D1,late,treatment,7,1.70,PASS
method_beta,D1,late,treatment,8,1.70,PASS
method_beta,D1,late,treatment,9,1.70,PASS
method_beta,D1,late,treatment,10,1.70,PASS
method_beta,D2,late,control,1,1.00,PASS
method_beta,D2,late,treatment,1,1.40,PASS
method_beta,D3,late,control,1,1.20,PASS
method_beta,D3,late,treatment,1,1.45,PASS
method_beta,D4,late,control,1,1.10,PASS
method_beta,D4,late,treatment,1,0.90,PASS
method_gamma,D1,early,control,1,1.00,PASS
method_gamma,D1,early,treatment,1,1.62,PASS
method_gamma,D2,early,control,1,1.10,PASS
method_gamma,D2,early,treatment,1,1.57,PASS
method_gamma,D3,early,control,1,1.00,PASS
method_gamma,D3,early,treatment,1,1.42,PASS
method_gamma,D4,early,control,1,1.20,PASS
method_gamma,D4,early,treatment,1,1.54,PASS
method_gamma,D1,late,control,1,1.10,PASS
method_gamma,D1,late,treatment,1,1.60,PASS
method_gamma,D2,late,control,1,1.00,PASS
method_gamma,D2,late,treatment,1,1.43,PASS
method_gamma,D3,late,control,1,1.20,PASS
method_gamma,D3,late,treatment,1,1.51,PASS
method_gamma,D4,late,control,1,1.10,PASS
method_gamma,D4,late,treatment,1,,MISSING
method_shadow,D1,early,control,1,1.00,PASS
method_shadow,D1,early,treatment,1,2.00,PASS
"""


POLICY = {
    "rules_version": "donor-stratified-signal-v1",
    "active_candidates": ["method_alpha", "method_beta", "method_gamma"],
    "registered_donors": ["D1", "D2", "D3", "D4"],
    "registered_states": ["early", "late"],
    "conditions": ["control", "treatment"],
    "qc_pass_status": "PASS",
    "minimum_identifiable_donors": {"early": 4, "late": 3},
    "minimum_state_mean_effect": {"early": 0.35, "late": 0.30},
    "maximum_state_effect_range": {"early": 0.40, "late": 0.35},
    "decision_precedence": ["INSUFFICIENT", "CONTRADICTORY", "WEAK", "SUPPORTED"],
    "selection_rule": [
        "eligible SUPPORTED candidates only",
        "largest worst_state_mean_effect",
        "smallest maximum_state_effect_range",
        "lexical candidate_id",
    ],
    "rounding": "decimal round-half-up to six places",
    "claim_boundary": "analytical_triage_only_not_mechanism_or_efficacy",
}


INSTRUCTION = """# Donor-stratified perturbation signal under partial identifiability

Use only the supplied offline CSV and JSON. Evaluate every active candidate at the biological donor-by-state level. `method_shadow` is not active and must be excluded.

For each candidate, donor and state, first average all QC-passing technical replicates within each condition. The donor effect is treatment mean minus control mean. A donor is identifiable only when both condition means exist. Never count technical replicates as independent donors and never replace donor-level effects with an observation-row pooled difference.

For each state, report the identifiable donor count, mean donor effect and donor-effect range (`maximum - minimum`). Apply state-specific thresholds from `policy.json`. State status is:

1. `INSUFFICIENT` when the identifiable donor count is below that state's minimum;
2. otherwise `CONTRADICTORY` when any identifiable donor effect is less than or equal to zero;
3. otherwise `WEAK` when the mean effect is below the state's minimum or the range exceeds the state's maximum;
4. otherwise `SUPPORTED`.

Candidate decision precedence is `INSUFFICIENT`, then `CONTRADICTORY`, then `WEAK`, then `SUPPORTED`: use the earliest status present across states. A locally insufficient donor/state cell does not force the state or candidate to `INSUFFICIENT` when the state's donor-count requirement is still met.

Only `SUPPORTED` candidates are eligible for selection. Rank them by descending worst-state mean effect, then ascending maximum state range, then ascending candidate ID. Select rank 1; use `hold_for_human_review` if none is eligible. This is analytical triage, not mechanism, target-engagement or efficacy evidence.

Round reported computed numbers to six decimal places using decimal round-half-up. JSON numeric values and TSV numeric cells are compared numerically, so trailing zeroes are optional. Sets use sorted JSON arrays; row order is not significant.

Write exactly four files under `outputs/`:

- `outputs/candidate_summary.tsv`: columns `candidate_id`, `decision`, `eligible`, `worst_state_mean_effect`, `maximum_state_effect_range`, `rank`. Include every active candidate once. Ineligible summary metrics and rank are blank.
- `outputs/state_diagnostics.tsv`: columns `candidate_id`, `state`, `identifiable_donor_count`, `missing_donors`, `nonpositive_donors`, `mean_effect`, `effect_range`, `status`. Include every active candidate/state pair. `missing_donors` and `nonpositive_donors` are sorted JSON arrays. When no donor is identifiable, numeric cells are blank.
- `outputs/decision.json`: fields `decision`, `selected_candidate`, `rules_version`, `claim_boundary`, and `human_review_required`. `decision` is `proceed_to_profile_review` when a candidate is selected, otherwise `hold_for_human_review`. `human_review_required` is true.
- `outputs/provenance.json`: `input_sha256` maps `observations.csv` and `policy.json` to their SHA-256 values; also include `rules_version`, `network`=`off`, and `deterministic`=true.
"""


TASK_YAML = """id: eb006-donor-stratified-signal-005
version: "1.0.0"
status: ready_for_calibration
title: "Donor-stratified perturbation signal under partial identifiability"
domain: biomedical_enterprise
agent_visible_inputs:
  - path: data/
    format: CSV and JSON
constraints:
  network: off
  provenance:
    record_input_checksum: true
    deterministic_output: true
required_outputs:
  - {id: candidate_summary, path: outputs/candidate_summary.tsv, required_fields: [candidate_id, decision, eligible, worst_state_mean_effect, maximum_state_effect_range, rank]}
  - {id: state_diagnostics, path: outputs/state_diagnostics.tsv, required_fields: [candidate_id, state, identifiable_donor_count, missing_donors, nonpositive_donors, mean_effect, effect_range, status]}
  - {id: decision, path: outputs/decision.json, required_fields: [decision, selected_candidate, rules_version, claim_boundary, human_review_required]}
  - {id: provenance, path: outputs/provenance.json, required_fields: [input_sha256, rules_version, network, deterministic]}
hidden_truth:
  path: verifier_only/reference.json
  status: verifier_only
"""


SCENARIO = """scenario_id: eb006-donor-stratified-signal-005
status: ready
source_scenarios: [EB006]
domain: biomedical_enterprise
scientific_decision: select a perturbation signal only when it is reproducible across independent donors and registered states
scientific_judgments:
  - collapse technical replicates before donor-level inference
  - apply state-specific support and heterogeneity thresholds
  - distinguish a missing donor cell from a globally insufficient state
  - reject pooled evidence that conceals a donor direction reversal
workflow_handoffs:
  - from: adjusted_signal_review
    to: profile_review
    artifact: outputs/decision.json
    invariant: only donor-stratified supported candidates may proceed
difficulty_modules:
  - id: judgment_experimental_unit
    observable: condition means and effects are computed once per biological donor and state
    decision_flip: observation-row pooling favors method_beta while donor-level direction identifies contradiction
  - id: math_stratified_partial_identifiability
    observable: support thresholds and effect tolerances are resolved separately for each state
    decision_flip: one missing donor remains locally insufficient but the late state is still identifiable
  - id: judgment_conflict_precedence
    observable: insufficient contradictory weak and supported states follow a public precedence
    decision_flip: a high pooled mean cannot override one registered nonpositive donor
  - id: noise_pooled_stratified_adversary
    observable: pooled and replicate-weighted summaries are reported only as rejected shortcut controls
    decision_flip: pooled aggregation selects a different candidate from the stratified oracle
release_gates:
  scientific_reality: synthetic_analytical_triage_only
  observability: pass
  verifiability: pass
  naive_resistance: pass
  reproducibility: automated_controls
  enterprise_value: pending
  training_value: evaluation_only
"""


def write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="utf-8")


def write_json(path: Path, value: object) -> None:
    write_text(path, json.dumps(value, indent=2, sort_keys=False) + "\n")


def main() -> int:
    if TASK.exists():
        raise RuntimeError(f"refusing to overwrite existing task: {TASK}")
    (TASK / "data").mkdir(parents=True)
    write_text(TASK / "data/observations.csv", OBSERVATIONS)
    write_json(TASK / "data/policy.json", POLICY)
    write_text(TASK / "instruction.md", INSTRUCTION)
    write_text(TASK / "task.yaml", TASK_YAML)
    write_text(TASK / "scenario-card.yaml", SCENARIO)
    template = ROOT / "scripts/templates/eb006_donor_stratified_signal"
    for relative in ("verifier.py", "tests/test_verifier.py", "run_calibration.py"):
        source = template / relative
        destination = TASK / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
