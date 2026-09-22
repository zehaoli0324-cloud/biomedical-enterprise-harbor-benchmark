#!/usr/bin/env python3
"""Build the shared-setup extension without modifying earlier EB013 trials."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TASK = ROOT / "benchmarks/eb013-shared-setup-routing-003"


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def main():
    if (TASK / "data").exists():
        raise FileExistsError("Existing package preserved; revise its version explicitly instead of rematerializing over trial evidence")
    rules = {"rules_version": "shared-setup-v1", "decision_date": "2026-09-22",
             "stage1_budget": 2.5, "commitment_budget": 5.5, "total_budget": 6.8,
             "initial_uncertainty": {"signal": 0.8, "selectivity": 0.7},
             "critical_thresholds": {"signal": 0.25, "selectivity": 0.25},
             "setup_costs": {"F1": 2.0, "F2": 1.5, "F3": 2.0, "F4": 2.0, "F5": 2.0},
             "objective": ["worst_case_max_critical_residual", "worst_case_cost", "setup_cost", "stage1_request_id", "sorted_stage2_policy"],
             "cost_semantics": "pay the union of all policy setup families before observing; only one branch execution is paid"}
    common = {"status": "current", "future_outcome": False, "available_at": "2026-09-01"}
    first = [
        {**common, "request_id": "P01", "cost": 1.5, "correlation_group": "G0", "covers": {"signal": .35, "selectivity": .30}, "outcomes": {"high": {"signal": .10}, "low": {"selectivity": .10}, "mid": {"signal": .04, "selectivity": .04}}},
        {**common, "request_id": "P02", "cost": 2.0, "correlation_group": "G0", "covers": {"signal": .30, "selectivity": .30}, "outcomes": {"high": {"signal": .10, "selectivity": .05}, "low": {"signal": .10, "selectivity": .05}, "mid": {"signal": .08, "selectivity": .03}}},
        {**common, "request_id": "P03", "cost": 2.5, "correlation_group": "G0", "covers": {"signal": .32, "selectivity": .30}, "outcomes": {"high": {"signal": .08}, "low": {"selectivity": .08}, "mid": {"signal": .03, "selectivity": .03}}},
    ]
    second = []
    specs = [
        ("M01", "high", "F3", 1.0, .25, .35), ("M02", "high", "F1", 1.3, .10, .28), ("M03", "high", "F2", 1.6, .20, .16),
        ("M04", "low", "F4", 1.0, .40, .10), ("M05", "low", "F1", 1.3, .28, .10), ("M06", "low", "F2", 1.6, .22, .18),
        ("M07", "mid", "F5", 1.0, .28, .28), ("M08", "mid", "F1", 1.3, .18, .18), ("M09", "mid", "F2", 1.6, .22, .12),
    ]
    for rid, state, family, cost, signal, selectivity in specs:
        second.append({**common, "request_id": rid, "cost": cost, "setup_family": family,
                       "correlation_group": "G-" + rid, "covers": {"signal": signal, "selectivity": selectivity},
                       "allowed_observations": [state], "dependency_ids": []})
    second.extend([
        {**second[0], "request_id": "M10", "covers": {"signal": .8, "selectivity": .8}, "future_outcome": True, "allowed_observations": ["high", "mid", "low"]},
        {**second[0], "request_id": "M11", "covers": {"signal": .8, "selectivity": .8}, "status": "retracted", "allowed_observations": ["high", "mid", "low"]},
        {**second[0], "request_id": "M12", "covers": {"signal": .8, "selectivity": .8}, "dependency_ids": ["P01", "unavailable-QC"], "allowed_observations": ["high", "mid", "low"]},
        {**second[7], "request_id": "M13", "covers": {"signal": .36, "selectivity": .31}, "correlation_group": "G0"},
    ])
    write(TASK / "data/rules.json", rules)
    write(TASK / "data/requests.json", {"stage1": first, "stage2": second})
    write(TASK / "data/output_contract.json", {
        "version": "1.0.0", "units": "abstract planning cost and bounded uncertainty; synthetic, not empirical efficacy",
        "required_hash_paths": ["rules.json", "requests.json", "output_contract.json"],
        "numeric_tolerance": 0.000001,
        "equivalents": ["JSON field order", "policies and route row order", "setup family order", "data/ hash prefix", "finite numeric strings"],
        "forbidden": ["duplicate keys or rows", "missing observations", "invented hashes", "wrong scientific values"],
        "selected_fields": ["stage1_request_id", "stage2_policy", "setup_families", "setup_cost", "worst_case_cost", "worst_case_max_critical_residual"],
        "route_fields": ["observation", "stage2_request_id", "residual_uncertainty", "cost", "eligible"]})
    write(TASK / "quality/source_ledger.json", {"status": "SYNTHETIC_DISCLOSED", "source": "locally authored analytic fixture", "license": "repository license", "empirical_claim": False, "transformation": "literal planning parameters in scripts/materialize_shared_setup_routing.py"})
    write(TASK / "quality/difficulty_card.json", {"task_id": TASK.name,
        "primary_module": "math_ex_ante_shared_setup", "secondary_modules": ["horizon_adaptive_policy_replay", "math_minimax_evidence_route_selection"],
        "held_out_variants": ["total budget contraction", "setup price reduction", "action retraction"],
        "decision_flip_controls": ["branchwise greedy overspends", "charge only observed setup changes winner", "shared setup charged once", "threshold crossing dominated policy"],
        "status": "CALIBRATION_REQUIRED"})
    write(TASK / "quality/sop_card.json", {"schema_version": "enterprise_harbor_sop_card.v1", "task_id": TASK.name,
        "sop_version": "enterprise-harbor-sop-v1.2", "source_status": "SYNTHETIC_DISCLOSED", "contract_status": "FROZEN_V1.0.0",
        "control_status": "NOT_RUN", "model_trial_status": "NOT_RUN", "independent_verifier_status": "NOT_RUN",
        "release_status": "BLOCKED", "release_blockers": ["target-model trial", "fixed-container replay", "practitioner review", "held-out target trials"]})
    print(TASK)


if __name__ == "__main__":
    main()
