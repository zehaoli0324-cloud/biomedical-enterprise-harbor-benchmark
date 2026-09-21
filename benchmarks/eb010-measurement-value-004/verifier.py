from __future__ import annotations

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
        reader = csv.DictReader(handle, delimiter="	")
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
    for concept in ("planning aid", "human review", "experimental improvement", "future-outcome", "redundancy"):
        if concept not in request:
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
