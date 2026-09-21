#!/usr/bin/env python3
"""Materialize EB010 measurement-value prioritization benchmark."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TASK = ROOT / "benchmarks/eb010-measurement-value-004"


def write(path: Path, value: str | dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(value, dict):
        path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    else:
        path.write_text(value, encoding="utf-8")


def main() -> None:
    write(TASK / "task.yaml", '''id: eb010-measurement-value-004
version: "0.1.0"
status: ready_for_calibration
title: "Decision-critical measurement prioritization"
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
  - {id: measurement_priority, path: outputs/measurement_priority.tsv, required_fields: [measurement_id, candidate_id, eligible, exclusion_reason, raw_information_gain, redundancy_penalty, net_information_value, rank]}
  - {id: information_value_audit, path: outputs/information_value_audit.json, required_fields: [selected_measurement_id, eligible_count, max_cost, rules_version, formula_id, input_sha256, claim_boundary]}
  - {id: approval_request, path: outputs/approval_request.md, required_fields: [selected_measurement, uncertainty_addressed, feasibility_and_leakage_review, human_review, claim_boundary]}
hidden_truth:
  path: verifier_only/reference.json
  status: verifier_only
''')
    write(TASK / "scenario-card.yaml", '''scenario_id: eb010-measurement-value-004
status: ready
source_scenarios: [EB010]
domain: biomedical_enterprise
scientific_decision: choose one additional measurement before the next experiment batch to reduce decision-critical uncertainty
scientific_judgments:
  - information_value_under_correlated_uncertainty
  - measurement_feasibility_and_visibility
  - bounded_planning_claim
workflow_handoffs:
  - from: optimization_state
    to: measurement_request
    artifact: outputs/measurement_priority.tsv
    invariant: rank only measurements supported by current observable state
  - from: measurement_request
    to: next_batch_review
    artifact: outputs/approval_request.md
    invariant: information value is a planning aid and requires human review
release_gates:
  scientific_reality: pass
  observability: pass
  verifiability: pass
  naive_resistance: pass
''')
    write(TASK / "instruction.md", '''# Decision-critical measurement prioritization

Choose one additional measurement to request before the next experiment batch. Rank measurement options using only the frozen current optimization state. This task selects a measurement request; it does not select the next experiment batch, decide whether the program should stop, or claim that a policy replay improved outcomes.

Eligibility is conjunctive. A measurement is eligible only when current_outcome_status is missing, assay_feasible is true, uses_future_outcome is false, and cost is no greater than max_cost in rules.json. Report every option, including ineligible options. Use these exclusion reasons in this order when applicable: outcome_already_observed, assay_infeasible, future_outcome_leakage, over_budget. Join multiple reasons with a semicolon.

For each option calculate:

- raw_information_gain = current_uncertainty * decision_sensitivity * expected_variance_reduction
- redundancy_penalty = raw_information_gain * abs(correlation_with_existing)
- net_information_value = (raw_information_gain - redundancy_penalty) / cost

Round reported numeric values to six decimal places using decimal round-half-up. Rank eligible options by descending net_information_value, breaking exact ties by measurement_id in ascending lexical order. Ineligible options have a blank rank. Select the rank-1 measurement. The formula_id is decision-information-value-v1.

Write exactly these files under outputs/:

- outputs/measurement_priority.tsv with columns measurement_id, candidate_id, eligible, exclusion_reason, raw_information_gain, redundancy_penalty, net_information_value, and rank. Encode eligible as true or false.
- outputs/information_value_audit.json with selected_measurement_id, eligible_count, max_cost, rules_version, formula_id, input_sha256 keyed by measurement_options.csv and rules.json, and claim_boundary containing experimental_improvement_established: false and human_review_required: true.
- outputs/approval_request.md naming the selected measurement, the uncertainty addressed, the feasibility and future-outcome leakage review, the redundancy assessment, and the required human review. State that the ranking is a planning aid and is not evidence of experimental improvement.
''')
    write(TASK / "expected_artifacts.md", '''# Expected artifacts

The frozen synthetic fixture contains both eligible and deliberately tempting ineligible options. The verifier recomputes eligibility, information value, provenance, and ranking from agent-visible inputs. A high score cannot override assay infeasibility, observed outcomes, future-outcome leakage, or budget limits.
''')
    write(TASK / "data/measurement_options.csv", '''measurement_id,candidate_id,current_outcome_status,current_uncertainty,decision_sensitivity,expected_variance_reduction,correlation_with_existing,assay_feasible,uses_future_outcome,cost,uncertainty_addressed
M-01,C-02,missing,0.80,0.90,0.60,0.10,true,false,2.00,response-window uncertainty
M-02,C-04,missing,0.90,0.80,0.70,0.80,true,false,1.50,pathway-state uncertainty
M-03,C-01,observed,0.60,0.70,0.80,0.05,true,false,1.00,dose-response uncertainty
M-04,C-05,missing,0.95,0.95,0.90,0.00,false,false,1.00,phenotype uncertainty
M-05,C-03,missing,0.85,0.90,0.85,0.05,true,true,1.20,durability uncertainty
M-06,C-06,missing,0.50,0.75,0.55,0.15,true,false,1.50,selectivity uncertainty
''')
    write(TASK / "data/rules.json", {
        "rules_version": "measurement-value-v1",
        "formula_id": "decision-information-value-v1",
        "max_cost": 2.0,
        "numeric_precision": 6,
        "tie_break": "measurement_id_ascending",
    })
    write(TASK / "verifier_only/reference.json", {
        "oracle_route": "independent_recomputation_from_agent_visible_inputs",
        "expected_selection": "M-01",
        "claim_boundary": "planning_aid_not_experimental_improvement",
    })
    write(TASK / "verifier.py", '''from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path


FIELDS = [
    "measurement_id", "candidate_id", "eligible", "exclusion_reason",
    "raw_information_gain", "redundancy_penalty", "net_information_value", "rank",
]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def as_bool(value: str) -> bool:
    return value.strip().lower() == "true"


def round_six(value: Decimal) -> float:
    return float(value.quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP))


def expected(data: Path) -> dict:
    options = list(csv.DictReader((data / "measurement_options.csv").open(newline="", encoding="utf-8")))
    rules = json.loads((data / "rules.json").read_text(encoding="utf-8"))
    rows = []
    for option in options:
        raw = Decimal(option["current_uncertainty"]) * Decimal(option["decision_sensitivity"]) * Decimal(option["expected_variance_reduction"])
        penalty = raw * abs(Decimal(option["correlation_with_existing"]))
        net = (raw - penalty) / Decimal(option["cost"])
        reasons = []
        if option["current_outcome_status"] != "missing":
            reasons.append("outcome_already_observed")
        if not as_bool(option["assay_feasible"]):
            reasons.append("assay_infeasible")
        if as_bool(option["uses_future_outcome"]):
            reasons.append("future_outcome_leakage")
        if float(option["cost"]) > float(rules["max_cost"]):
            reasons.append("over_budget")
        rows.append({
            "measurement_id": option["measurement_id"],
            "candidate_id": option["candidate_id"],
            "eligible": not reasons,
            "exclusion_reason": ";".join(reasons),
            "raw_information_gain": round_six(raw),
            "redundancy_penalty": round_six(penalty),
            "net_information_value": round_six(net),
            "rank": None,
        })
    eligible = sorted((row for row in rows if row["eligible"]), key=lambda row: (-row["net_information_value"], row["measurement_id"]))
    for rank, row in enumerate(eligible, start=1):
        row["rank"] = rank
    return {
        "rows": rows,
        "selected_measurement_id": eligible[0]["measurement_id"],
        "eligible_count": len(eligible),
        "max_cost": rules["max_cost"],
        "rules_version": rules["rules_version"],
        "formula_id": rules["formula_id"],
        "input_sha256": {name: sha256(data / name) for name in ("measurement_options.csv", "rules.json")},
        "claim_boundary": {"experimental_improvement_established": False, "human_review_required": True},
    }


def verify(submission: Path, data: Path, reference: Path) -> tuple[bool, list[str]]:
    del reference
    exp = expected(data)
    errors = []
    for name in ("measurement_priority.tsv", "information_value_audit.json", "approval_request.md"):
        if not (submission / name).is_file():
            errors.append("missing artifact: " + name)
    if errors:
        return False, errors

    with (submission / "measurement_priority.tsv").open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if reader.fieldnames != FIELDS:
            errors.append("measurement priority columns mismatch")
        submitted_rows = list(reader)
    by_id = {row.get("measurement_id"): row for row in submitted_rows}
    if len(by_id) != len(submitted_rows):
        errors.append("measurement priority contains duplicate identifiers")
    if set(by_id) != {row["measurement_id"] for row in exp["rows"]}:
        errors.append("measurement priority must cover every option exactly once")
    for expected_row in exp["rows"]:
        actual = by_id.get(expected_row["measurement_id"])
        if actual is None:
            continue
        for key in ("candidate_id", "exclusion_reason"):
            if actual.get(key) != str(expected_row[key]):
                errors.append(f"{expected_row['measurement_id']} mismatch: {key}")
        if actual.get("eligible", "").lower() != str(expected_row["eligible"]).lower():
            errors.append(f"{expected_row['measurement_id']} mismatch: eligible")
        expected_rank = "" if expected_row["rank"] is None else str(expected_row["rank"])
        if actual.get("rank", "") != expected_rank:
            errors.append(f"{expected_row['measurement_id']} mismatch: rank")
        for key in ("raw_information_gain", "redundancy_penalty", "net_information_value"):
            try:
                value = float(actual.get(key, ""))
            except ValueError:
                errors.append(f"{expected_row['measurement_id']} invalid numeric value: {key}")
                continue
            if not math.isclose(value, expected_row[key], abs_tol=1e-6):
                errors.append(f"{expected_row['measurement_id']} mismatch: {key}")

    try:
        audit = json.loads((submission / "information_value_audit.json").read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        errors.append("information value audit is not valid JSON")
        audit = {}
    for key in ("selected_measurement_id", "eligible_count", "max_cost", "rules_version", "formula_id"):
        if audit.get(key) != exp[key]:
            errors.append("information value audit mismatch: " + key)
    if audit.get("input_sha256") != exp["input_sha256"]:
        errors.append("information value audit provenance mismatch")
    if audit.get("claim_boundary") != exp["claim_boundary"]:
        errors.append("information value audit claim boundary mismatch")

    request = (submission / "approval_request.md").read_text(encoding="utf-8").lower()
    if exp["selected_measurement_id"].lower() not in request:
        errors.append("approval request does not name the selected measurement")
    for concept, alternatives in {
        "planning aid": ("planning aid",),
        "human review": ("human review",),
        "experimental improvement": ("experimental improvement",),
        "future outcome": ("future outcome", "future-outcome"),
        "redundancy": ("redundancy",),
    }.items():
        if not any(variant in request for variant in alternatives):
            errors.append("approval request missing required concept: " + concept)
    return not errors, errors


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--submission", type=Path, required=True)
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--reference", type=Path, required=True)
    args = parser.parse_args()
    passed, problems = verify(args.submission, args.data, args.reference)
    print(json.dumps({"passed": passed, "errors": problems}))
    raise SystemExit(0 if passed else 1)
''')
    write(TASK / "tests/test_verifier.py", '''import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("verifier", ROOT / "verifier.py")
verifier = importlib.util.module_from_spec(spec)
assert spec.loader
spec.loader.exec_module(verifier)


def test_expected_is_deterministic_and_selects_eligible_option():
    first = verifier.expected(ROOT / "data")
    assert first == verifier.expected(ROOT / "data")
    assert first["selected_measurement_id"] == "M-01"
    assert first["eligible_count"] == 3


def test_missing_submission_fails(tmp_path):
    passed, errors = verifier.verify(tmp_path, ROOT / "data", ROOT / "verifier_only/reference.json")
    assert not passed
    assert errors
''')
    cards = {
        "candidate_set_card.json": {"candidate_set_id": "CSET-EB010-MEASUREMENT-VALUE-004-001", "source_benchmark_id": "EB010", "candidates": [{"candidate_id": "eb010-measurement-value-004", "selection_status": "MATERIALIZED", "semantic_axes": ["scientific_decision", "data_visibility", "evidence_reconciliation"]}], "selection_gate": {"minimum_candidates": 3, "maximum_candidates": 5, "require_two_semantic_differences": True, "require_independent_review": True}, "status": "REVIEW_REQUIRED"},
        "enterprise_value_card.json": {"enterprise_value_card_id": "VALUE-EB010-MEASUREMENT-VALUE-004-001", "task_id": "eb010-measurement-value-004", "enterprise_reality": {"evidence_class": "B", "named_role": "experimental_design_scientist", "decision": "choose an additional measurement before the next batch", "downstream_action": "optimization_state->measurement_request->next_batch_review", "error_consequence": "redundant, infeasible, or leaked measurements consume budget without resolving the decision bottleneck", "human_owner": "experimental_design_lead"}, "status": "REVIEW_REQUIRED"},
        "difficulty_card.json": {"difficulty_card_id": "DIFF-EB010-MEASUREMENT-VALUE-004-001", "task_id": "eb010-measurement-value-004", "difficulty_hypothesis": {"reasoning_chain": ["screen measurement eligibility", "discount correlated uncertainty", "normalize information gain by cost", "preserve the planning claim boundary"], "target_failure_mechanism": "a fluent shortcut selects the highest apparent uncertainty reduction despite infeasibility or future-outcome leakage"}, "shortcut_probes": ["highest raw score", "ignore correlation", "ignore future visibility", "always abstain"], "status": "DRAFT"},
        "training_value_card.json": {"training_value_card_id": "TRAIN-EB010-MEASUREMENT-VALUE-004-001", "task_id": "eb010-measurement-value-004", "capability_targets": ["information-value reasoning", "evidence reconciliation", "visibility control", "claim boundary"], "error_labels": ["input_understanding", "method_choice", "calculation_or_tool", "claim_overreach", "delivery_failure"], "training_use": "EVAL_ONLY_UNTIL_CALIBRATED", "status": "REVIEW_REQUIRED"},
        "control_plan_card.json": {"control_plan_id": "CONTROL-EB010-MEASUREMENT-VALUE-004-001", "task_id": "eb010-measurement-value-004", "controls": [{"control_id": "positive-reference", "kind": "positive"}, {"control_id": "negative-corrupt-ranking", "kind": "negative"}, {"control_id": "invariance-row-order", "kind": "invariance"}, {"control_id": "insufficient-provenance", "kind": "insufficient_evidence"}], "single_factor_policy": True, "calibration_status": "NOT_RUN", "status": "REVIEW_REQUIRED"},
        "model_trial_card.json": {"model_trial_card_id": "TRIAL-EB010-MEASUREMENT-VALUE-004-001", "task_id": "eb010-measurement-value-004", "protocol_version": "enterprise-model-trial.v1", "strategies": ["reference_solution", "simple_legal_baseline", "always_abstain", "template_or_keyword", "target_model"], "target_model_status": "NOT_RUN", "status": "NOT_RUN", "run_records": []},
        "sop_card.json": {"schema_version": "enterprise_harbor_sop_card.v1", "task_id": "eb010-measurement-value-004", "sop_version": "enterprise-harbor-sop-v1.1", "source_status": "REVIEW_REQUIRED", "contract_status": "CONTRACT_ONLY", "control_status": "NOT_RUN", "model_trial_status": "NOT_RUN", "target_model_failure_policy": "infrastructure_failures_are_not_difficulty_evidence", "independent_verifier_status": "NOT_RUN", "release_status": "BLOCKED", "release_blockers": ["source/license/privacy review", "independent verifier contract audit", "control calibration", "author-side baselines", "target-model trial"]},
    }
    for name, value in cards.items():
        write(TASK / "quality" / name, value)
    write(TASK / "controls/calibration_results.json", {"schema_version": "enterprise_control_calibration.v1", "task_id": "eb010-measurement-value-004", "status": "NOT_RUN", "controls": []})
    print(TASK)


if __name__ == "__main__":
    main()
