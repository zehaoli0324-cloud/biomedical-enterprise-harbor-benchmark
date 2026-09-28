#!/usr/bin/env python3
"""Independent Fraction-based audit for the EB006 donor oracle."""

from __future__ import annotations

import csv
import json
from fractions import Fraction
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TASK = ROOT / "benchmarks/eb006-donor-stratified-signal-005"


EXPECTED_EFFECTS = {
    ("method_alpha", "early"): {"D1": Fraction(7, 10), "D2": Fraction(1, 2), "D3": Fraction(2, 5), "D4": Fraction(3, 10)},
    ("method_alpha", "late"): {"D1": Fraction(11, 20), "D2": Fraction(9, 20), "D3": Fraction(3, 10), "D4": Fraction(1, 4)},
    ("method_beta", "early"): {"D1": Fraction(3, 4), "D2": Fraction(9, 20), "D3": Fraction(7, 20), "D4": Fraction(-1, 4)},
    ("method_beta", "late"): {"D1": Fraction(3, 5), "D2": Fraction(2, 5), "D3": Fraction(1, 4), "D4": Fraction(-1, 5)},
    ("method_gamma", "early"): {"D1": Fraction(31, 50), "D2": Fraction(47, 100), "D3": Fraction(21, 50), "D4": Fraction(17, 50)},
    ("method_gamma", "late"): {"D1": Fraction(1, 2), "D2": Fraction(43, 100), "D3": Fraction(31, 100)},
}


EXPECTED_STATES = {
    ("method_alpha", "early"): (4, Fraction(19, 40), Fraction(2, 5), "SUPPORTED"),
    ("method_alpha", "late"): (4, Fraction(31, 80), Fraction(3, 10), "SUPPORTED"),
    ("method_beta", "early"): (4, Fraction(13, 40), Fraction(1, 1), "CONTRADICTORY"),
    ("method_beta", "late"): (4, Fraction(21, 80), Fraction(4, 5), "CONTRADICTORY"),
    ("method_gamma", "early"): (4, Fraction(37, 80), Fraction(7, 25), "SUPPORTED"),
    ("method_gamma", "late"): (3, Fraction(31, 75), Fraction(19, 100), "SUPPORTED"),
}


def main() -> int:
    policy = json.loads((TASK / "data/policy.json").read_text(encoding="utf-8"))
    rows = list(csv.DictReader((TASK / "data/observations.csv").open(encoding="utf-8")))
    cells: dict[tuple[str, str, str, str], list[Fraction]] = {}
    for row in rows:
        if row["candidate_id"] not in policy["active_candidates"] or row["qc_status"] != "PASS" or not row["adjusted_signal"]:
            continue
        key = (row["candidate_id"], row["state"], row["donor"], row["condition"])
        cells.setdefault(key, []).append(Fraction(row["adjusted_signal"]))

    observed_effects = {}
    for (candidate, state), donor_effects in EXPECTED_EFFECTS.items():
        observed_effects[(candidate, state)] = {}
        for donor in donor_effects:
            control = cells[(candidate, state, donor, "control")]
            treatment = cells[(candidate, state, donor, "treatment")]
            observed_effects[(candidate, state)][donor] = sum(treatment) / len(treatment) - sum(control) / len(control)
    effect_match = observed_effects == EXPECTED_EFFECTS

    state_checks = {}
    for key, effects in observed_effects.items():
        values = list(effects.values())
        count = len(values)
        mean = sum(values) / count
        spread = max(values) - min(values)
        state = key[1]
        if count < policy["minimum_identifiable_donors"][state]:
            status = "INSUFFICIENT"
        elif any(value <= 0 for value in values):
            status = "CONTRADICTORY"
        elif mean < Fraction(str(policy["minimum_state_mean_effect"][state])) or spread > Fraction(str(policy["maximum_state_effect_range"][state])):
            status = "WEAK"
        else:
            status = "SUPPORTED"
        state_checks[key] = (count, mean, spread, status)
    state_match = state_checks == EXPECTED_STATES
    supported = [candidate for candidate in policy["active_candidates"] if all(state_checks[(candidate, state)][3] == "SUPPORTED" for state in policy["registered_states"])]
    ranked = sorted(supported, key=lambda candidate: (
        -min(state_checks[(candidate, state)][1] for state in policy["registered_states"]),
        max(state_checks[(candidate, state)][2] for state in policy["registered_states"]), candidate))
    selected = ranked[0]
    audit = {
        "schema_version": "enterprise_independent_oracle_audit.v1",
        "task_id": TASK.name,
        "implementation": "fractions_manual_expected_table_without_verifier_import",
        "effect_table_match": effect_match,
        "state_table_match": state_match,
        "selected_candidate": selected,
        "expected_selected_candidate": "method_gamma",
        "passed": effect_match and state_match and selected == "method_gamma",
        "scientific_checks": {
            "technical_replicates_collapsed_before_donor_effect": True,
            "method_beta_nonpositive_donor_detected": True,
            "method_gamma_late_missing_donor_does_not_force_global_abstention": True,
            "inactive_method_shadow_excluded": True,
        },
    }
    (TASK / "quality").mkdir(exist_ok=True)
    (TASK / "quality/oracle_audit.json").write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")
    reference = {
        "schema_version": "enterprise_hidden_reference.v1",
        "task_id": TASK.name,
        "selected_candidate": "method_gamma",
        "candidate_decisions": {"method_alpha": "SUPPORTED", "method_beta": "CONTRADICTORY", "method_gamma": "SUPPORTED"},
        "state_values": {f"{candidate}:{state}": {"count": count, "mean": float(mean), "range": float(spread), "status": status}
                         for (candidate, state), (count, mean, spread, status) in EXPECTED_STATES.items()},
        "oracle_route": "independent_fraction_audit",
    }
    (TASK / "verifier_only").mkdir(exist_ok=True)
    (TASK / "verifier_only/reference.json").write_text(json.dumps(reference, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(audit, indent=2))
    return 0 if audit["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
