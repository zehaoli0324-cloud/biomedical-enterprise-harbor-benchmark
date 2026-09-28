#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path


TOLERANCE = 1e-6


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def round_six(value: Decimal) -> float:
    return float(value.quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP))


def expected(data: Path) -> dict:
    policy = load_json(data / "policy.json")
    rows = list(csv.DictReader((data / "observations.csv").open(encoding="utf-8")))
    candidates = policy["active_candidates"]
    donors = policy["registered_donors"]
    states = policy["registered_states"]
    grouped = {}
    for row in rows:
        if row["candidate_id"] not in candidates or row["qc_status"] != policy["qc_pass_status"] or not row["adjusted_signal"]:
            continue
        key = (row["candidate_id"], row["donor"], row["state"], row["condition"])
        grouped.setdefault(key, []).append(Decimal(row["adjusted_signal"]))

    diagnostics = []
    decisions = {}
    summaries = []
    for candidate in candidates:
        state_rows = []
        for state in states:
            effects = {}
            missing = []
            for donor in donors:
                control = grouped.get((candidate, donor, state, "control"), [])
                treatment = grouped.get((candidate, donor, state, "treatment"), [])
                if not control or not treatment:
                    missing.append(donor)
                    continue
                control_mean = sum(control, Decimal(0)) / Decimal(len(control))
                treatment_mean = sum(treatment, Decimal(0)) / Decimal(len(treatment))
                effects[donor] = treatment_mean - control_mean
            values = list(effects.values())
            mean = sum(values, Decimal(0)) / Decimal(len(values)) if values else None
            spread = max(values) - min(values) if values else None
            nonpositive = sorted(donor for donor, value in effects.items() if value <= 0)
            if len(values) < policy["minimum_identifiable_donors"][state]:
                status = "INSUFFICIENT"
            elif nonpositive:
                status = "CONTRADICTORY"
            elif mean < Decimal(str(policy["minimum_state_mean_effect"][state])) or spread > Decimal(str(policy["maximum_state_effect_range"][state])):
                status = "WEAK"
            else:
                status = "SUPPORTED"
            item = {
                "candidate_id": candidate,
                "state": state,
                "identifiable_donor_count": len(values),
                "missing_donors": sorted(missing),
                "nonpositive_donors": nonpositive,
                "mean_effect": None if mean is None else round_six(mean),
                "effect_range": None if spread is None else round_six(spread),
                "status": status,
            }
            diagnostics.append(item)
            state_rows.append(item)
        statuses = [item["status"] for item in state_rows]
        decision = next(status for status in policy["decision_precedence"] if status in statuses)
        decisions[candidate] = decision
        if decision == "SUPPORTED":
            worst_mean = min(Decimal(str(item["mean_effect"])) for item in state_rows)
            max_range = max(Decimal(str(item["effect_range"])) for item in state_rows)
            summaries.append({"candidate_id": candidate, "decision": decision, "eligible": True,
                              "worst_state_mean_effect": round_six(worst_mean),
                              "maximum_state_effect_range": round_six(max_range), "rank": None})
        else:
            summaries.append({"candidate_id": candidate, "decision": decision, "eligible": False,
                              "worst_state_mean_effect": None, "maximum_state_effect_range": None, "rank": None})
    eligible = sorted((item for item in summaries if item["eligible"]),
                      key=lambda item: (-item["worst_state_mean_effect"], item["maximum_state_effect_range"], item["candidate_id"]))
    for rank, item in enumerate(eligible, 1):
        item["rank"] = rank
    selected = eligible[0]["candidate_id"] if eligible else None
    return {"summaries": summaries, "diagnostics": diagnostics, "selected": selected,
            "decision": "proceed_to_profile_review" if selected else "hold_for_human_review", "policy": policy}


def parse_bool(value: str) -> bool:
    if value.lower() == "true":
        return True
    if value.lower() == "false":
        return False
    raise ValueError("invalid boolean")


def parse_optional_number(value: object):
    if value in (None, ""):
        return None
    if isinstance(value, bool):
        raise ValueError("boolean is not numeric")
    number = float(value)
    if not math.isfinite(number):
        raise ValueError("number must be finite")
    return number


def compare_number(actual, wanted) -> bool:
    if actual is None or wanted is None:
        return actual is None and wanted is None
    return abs(actual - wanted) <= TOLERANCE


def read_table(path: Path, delimiter: str) -> list[dict]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter=delimiter))


def verify(submission: Path, data: Path, reference: Path | None = None) -> tuple[bool, list[str]]:
    truth = expected(data)
    errors = []
    if reference is not None and reference.is_file():
        frozen = load_json(reference)
        if frozen.get("selected_candidate") != truth["selected"]:
            errors.append("oracle_consistency: selected candidate mismatch")
        frozen_decisions = frozen.get("candidate_decisions", {})
        actual_decisions = {item["candidate_id"]: item["decision"] for item in truth["summaries"]}
        if frozen_decisions != actual_decisions:
            errors.append("oracle_consistency: candidate decisions mismatch")
    required = ["candidate_summary.tsv", "state_diagnostics.tsv", "decision.json", "provenance.json"]
    for name in required:
        if not (submission / name).is_file():
            errors.append(f"missing artifact: {name}")
    if errors:
        return False, errors
    try:
        summaries = read_table(submission / "candidate_summary.tsv", "\t")
        diagnostics = read_table(submission / "state_diagnostics.tsv", "\t")
        decision = load_json(submission / "decision.json")
        provenance = load_json(submission / "provenance.json")
    except Exception as exc:
        return False, [f"delivery_or_contract: {exc}"]

    summary_fields = ["candidate_id", "decision", "eligible", "worst_state_mean_effect", "maximum_state_effect_range", "rank"]
    diagnostic_fields = ["candidate_id", "state", "identifiable_donor_count", "missing_donors", "nonpositive_donors", "mean_effect", "effect_range", "status"]
    if not summaries or list(summaries[0]) != summary_fields:
        errors.append("candidate_summary: exact columns required")
    if not diagnostics or list(diagnostics[0]) != diagnostic_fields:
        errors.append("state_diagnostics: exact columns required")

    expected_summaries = {item["candidate_id"]: item for item in truth["summaries"]}
    if len(summaries) != len(expected_summaries) or len({row.get("candidate_id") for row in summaries}) != len(summaries):
        errors.append("candidate_summary: exact unique active candidates required")
    for row in summaries:
        candidate = row.get("candidate_id")
        wanted = expected_summaries.get(candidate)
        if not wanted:
            errors.append(f"candidate_summary.{candidate}: unexpected")
            continue
        try:
            actual = {
                "decision": row["decision"], "eligible": parse_bool(row["eligible"]),
                "worst_state_mean_effect": parse_optional_number(row["worst_state_mean_effect"]),
                "maximum_state_effect_range": parse_optional_number(row["maximum_state_effect_range"]),
                "rank": None if row["rank"] == "" else int(row["rank"]),
            }
        except Exception as exc:
            errors.append(f"candidate_summary.{candidate}: {exc}")
            continue
        for field in ("decision", "eligible", "rank"):
            if actual[field] != wanted[field]:
                errors.append(f"candidate_summary.{candidate}.{field}: mismatch")
        for field in ("worst_state_mean_effect", "maximum_state_effect_range"):
            if not compare_number(actual[field], wanted[field]):
                errors.append(f"candidate_summary.{candidate}.{field}: numeric mismatch")

    expected_diagnostics = {(item["candidate_id"], item["state"]): item for item in truth["diagnostics"]}
    keys = [(row.get("candidate_id"), row.get("state")) for row in diagnostics]
    if len(diagnostics) != len(expected_diagnostics) or len(set(keys)) != len(keys):
        errors.append("state_diagnostics: exact unique candidate/state rows required")
    for row in diagnostics:
        key = (row.get("candidate_id"), row.get("state"))
        wanted = expected_diagnostics.get(key)
        if not wanted:
            errors.append(f"state_diagnostics.{key}: unexpected")
            continue
        try:
            actual = {"identifiable_donor_count": int(row["identifiable_donor_count"]),
                      "missing_donors": sorted(json.loads(row["missing_donors"])),
                      "nonpositive_donors": sorted(json.loads(row["nonpositive_donors"])),
                      "mean_effect": parse_optional_number(row["mean_effect"]),
                      "effect_range": parse_optional_number(row["effect_range"]), "status": row["status"]}
        except Exception as exc:
            errors.append(f"state_diagnostics.{key}: {exc}")
            continue
        for field in ("identifiable_donor_count", "missing_donors", "nonpositive_donors", "status"):
            if actual[field] != wanted[field]:
                errors.append(f"state_diagnostics.{key}.{field}: mismatch")
        for field in ("mean_effect", "effect_range"):
            if not compare_number(actual[field], wanted[field]):
                errors.append(f"state_diagnostics.{key}.{field}: numeric mismatch")

    policy = truth["policy"]
    expected_decision = {"decision": truth["decision"], "selected_candidate": truth["selected"],
                         "rules_version": policy["rules_version"], "claim_boundary": policy["claim_boundary"],
                         "human_review_required": True}
    for field, wanted in expected_decision.items():
        if decision.get(field) != wanted:
            errors.append(f"decision.{field}: mismatch")
    expected_hashes = {name: hashlib.sha256((data / name).read_bytes()).hexdigest() for name in ("observations.csv", "policy.json")}
    if provenance.get("input_sha256") != expected_hashes:
        errors.append("provenance.input_sha256: mismatch")
    for field, wanted in {"rules_version": policy["rules_version"], "network": "off", "deterministic": True}.items():
        if provenance.get(field) != wanted:
            errors.append(f"provenance.{field}: mismatch")
    return not errors, errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--submission", type=Path, required=True)
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--reference", type=Path)
    args = parser.parse_args()
    passed, errors = verify(args.submission, args.data, args.reference)
    contract_prefixes = ("missing artifact", "delivery_or_contract", "candidate_summary: exact", "state_diagnostics: exact", "provenance.", "decision.rules_version", "decision.claim_boundary", "decision.human_review_required", "oracle_consistency")
    contract_errors = [error for error in errors if error.startswith(contract_prefixes)]
    science_errors = [error for error in errors if error not in contract_errors]
    classification = "PASS" if passed else "MIXED_ERROR" if contract_errors and science_errors else "CONTRACT_ERROR" if contract_errors else "SCIENCE_ERROR"
    print(json.dumps({"passed": passed, "classification": classification,
                      "science_score": 1.0 if not science_errors else 0.0,
                      "contract_score": 1.0 if not contract_errors else 0.0,
                      "science_errors": science_errors, "contract_errors": contract_errors, "errors": errors}))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
