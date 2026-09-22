"""Enumerate observation policies with ex-ante shared setup commitments."""
from __future__ import annotations

import argparse
import csv
import hashlib
import itertools
import json
import math
from decimal import Decimal
from pathlib import Path


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key: " + key)
        result[key] = value
    return result


def load(path):
    return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=unique_object)


def number(value):
    if isinstance(value, bool):
        raise ValueError("boolean is not a number")
    result = Decimal(str(value))
    if not result.is_finite():
        raise ValueError("nonfinite number")
    return result


def hashes(data):
    return {p.relative_to(data).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(data.rglob("*.json"))}


def valid(request, rules):
    return (request["status"] == "current" and not request["future_outcome"]
            and request["available_at"] <= rules["decision_date"])


def evaluate_policy(first, actions, rules):
    """Charge the union of preparations before any observation can occur."""
    families = sorted({a["setup_family"] for a in actions})
    setup = sum((number(rules["setup_costs"][f]) for f in families), Decimal(0))
    first_cost = number(first["cost"])
    upfront = first_cost + setup
    rows = []
    for state, action in zip(sorted(first["outcomes"]), actions):
        residuals = {}
        for axis, initial in rules["initial_uncertainty"].items():
            groups = {}
            for request in (first, action):
                group = request["correlation_group"]
                groups[group] = max(groups.get(group, Decimal(0)), number(request["covers"].get(axis, 0)))
            residuals[axis] = max(Decimal(0), number(initial) - sum(groups.values())
                                  - number(first["outcomes"][state].get(axis, 0)))
        rows.append({"observation": state, "stage2_request_id": action["request_id"],
                     "residual_uncertainty": {k: float(v) for k, v in residuals.items()},
                     "max_critical_residual": float(max(residuals[k] for k in rules["critical_thresholds"])),
                     "cost": float(upfront + number(action["cost"])),
                     "eligible": all(residuals[k] <= number(t) for k, t in rules["critical_thresholds"].items())})
    worst_cost = max(row["cost"] for row in rows)
    budget_ok = (first_cost <= number(rules["stage1_budget"])
                 and upfront <= number(rules["commitment_budget"])
                 and number(worst_cost) <= number(rules["total_budget"]))
    return {"stage1_request_id": first["request_id"],
            "stage2_policy": {r["observation"]: r["stage2_request_id"] for r in rows},
            "setup_families": families, "setup_cost": float(setup),
            "worst_case_cost": worst_cost,
            "worst_case_max_critical_residual": max(r["max_critical_residual"] for r in rows),
            "budget_ok": budget_ok, "eligible": budget_ok and all(r["eligible"] for r in rows),
            "states": rows}


def objective(policy):
    return (policy["worst_case_max_critical_residual"], policy["worst_case_cost"],
            policy["setup_cost"], policy["stage1_request_id"], tuple(sorted(policy["stage2_policy"].items())))


def enumerate_policies(data):
    rules = load(data / "rules.json")
    catalog = load(data / "requests.json")
    policies = []
    for first in catalog["stage1"]:
        if not valid(first, rules):
            continue
        options = [[a for a in catalog["stage2"] if valid(a, rules)
                    and state in a["allowed_observations"]
                    and all(dep == first["request_id"] for dep in a["dependency_ids"])]
                   for state in sorted(first["outcomes"])]
        for actions in itertools.product(*options):
            policies.append(evaluate_policy(first, actions, rules))
    return policies


def expected(data):
    policies = enumerate_policies(data)
    eligible = [p for p in policies if p["eligible"]]
    winner = min(eligible, key=objective) if eligible else None
    summaries = []
    for first in load(data / "requests.json")["stage1"]:
        options = [p for p in eligible if p["stage1_request_id"] == first["request_id"]]
        best = min(options, key=objective) if options else None
        summaries.append({"stage1_request_id": first["request_id"], "best_policy":
                          {k: v for k, v in best.items() if k not in {"states", "budget_ok"}} if best else None})
    return {"winner": winner, "summaries": summaries, "hashes": hashes(data)}


def compare(actual, expected_value, path, errors):
    """Compare supplied semantic fields; allow extra explanatory JSON keys."""
    if isinstance(expected_value, dict):
        if not isinstance(actual, dict):
            errors.append(path + ": object required")
            return
        for key, value in expected_value.items():
            if key not in actual:
                errors.append(path + "." + key + ": missing")
            else:
                compare(actual[key], value, path + "." + key, errors)
    elif isinstance(expected_value, bool):
        if actual is not expected_value:
            errors.append(path + ": wrong boolean")
    elif isinstance(expected_value, (int, float)):
        try:
            if not math.isclose(float(number(actual)), expected_value, abs_tol=1e-6, rel_tol=0):
                errors.append(path + ": wrong number")
        except (ValueError, TypeError, ArithmeticError):
            errors.append(path + ": invalid number")
    elif actual != expected_value:
        errors.append(path + ": mismatch")


def keyed(rows, key):
    if not isinstance(rows, list) or any(not isinstance(r, dict) or key not in r for r in rows):
        raise ValueError("missing row key: " + key)
    result = {}
    for row in rows:
        if row[key] in result:
            raise ValueError("duplicate row key: " + str(row[key]))
        result[row[key]] = row
    return result


def verify(submission, data, reference=None):
    errors = []
    required = ("plan.json", "decision.json", "route.tsv", "provenance.json", "audit.md")
    for name in required:
        if not (submission / name).is_file():
            errors.append("delivery: missing " + name)
    if errors:
        return False, errors
    try:
        exp = expected(data)
        rules = load(data / "rules.json")
        plan, decision = load(submission / "plan.json"), load(submission / "decision.json")
        winner = exp["winner"]
        selected = ({k: v for k, v in winner.items() if k not in {"states", "budget_ok", "eligible"}}
                    if winner else {"stage1_request_id": None, "stage2_policy": {}, "setup_families": [],
                                    "setup_cost": None, "worst_case_cost": None, "worst_case_max_critical_residual": None})
        for payload, label in ((plan, "plan"), (decision, "decision")):
            if "setup_families" in payload:
                payload["setup_families"] = sorted(payload["setup_families"])
            compare(payload, selected, label, errors)
            if payload.get("stage2_policy") != selected["stage2_policy"]:
                errors.append(label + ": exact observation coverage required")
        compare(decision, {"decision": "execute_adaptive_route" if winner else "request_information",
                           "human_review_required": True, "claim_boundary": "planning_only"}, "decision", errors)
        summaries = keyed(plan.get("policies"), "stage1_request_id")
        expected_summaries = keyed(exp["summaries"], "stage1_request_id")
        if set(summaries) != set(expected_summaries):
            errors.append("plan.policies: stage1 coverage mismatch")
        for key in set(summaries) & set(expected_summaries):
            best = summaries[key].get("best_policy")
            if isinstance(best, dict) and "setup_families" in best:
                best["setup_families"] = sorted(best["setup_families"])
            compare(summaries[key], expected_summaries[key], "plan.policies." + key, errors)
            if best and best.get("stage2_policy") != expected_summaries[key]["best_policy"]["stage2_policy"]:
                errors.append("plan.policies: exact mapping required")
        with (submission / "route.tsv").open(encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle, delimiter="\t")
            fields = {"observation", "stage2_request_id", "residual_uncertainty", "cost", "eligible"}
            if not fields <= set(reader.fieldnames or []):
                raise ValueError("route.tsv: missing declared header")
            rows = []
            for row in reader:
                row["residual_uncertainty"] = json.loads(row["residual_uncertainty"], object_pairs_hook=unique_object)
                if row["eligible"].lower() not in {"true", "false"}:
                    raise ValueError("route.tsv: invalid boolean")
                row["eligible"] = row["eligible"].lower() == "true"
                rows.append(row)
        actual_rows = keyed(rows, "observation")
        expected_rows = keyed(winner["states"] if winner else [], "observation")
        if set(actual_rows) != set(expected_rows):
            errors.append("route.tsv: observation coverage mismatch")
        for state in set(actual_rows) & set(expected_rows):
            required_row = {k: v for k, v in expected_rows[state].items() if k != "max_critical_residual"}
            compare(actual_rows[state], required_row, "route." + state, errors)
            if set(actual_rows[state]["residual_uncertainty"]) != set(required_row["residual_uncertainty"]):
                errors.append("route.tsv: uncertainty axes mismatch")
        prov = load(submission / "provenance.json")
        supplied = prov.get("input_sha256", {})
        normalized = {}
        for name, digest in supplied.items():
            key = name.removeprefix("data/")
            if key in normalized:
                raise ValueError("duplicate normalized input path")
            normalized[key] = digest
        if normalized != exp["hashes"]:
            errors.append("provenance: missing or wrong input hash")
        compare(prov, {"rules_version": rules["rules_version"], "network": "off", "deterministic": True}, "provenance", errors)
        if not (submission / "audit.md").read_text(encoding="utf-8").strip():
            errors.append("delivery: empty audit")
    except (ValueError, TypeError, KeyError, OSError, ArithmeticError) as exc:
        errors.append("contract: " + str(exc))
    return not errors, errors


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--submission", type=Path, required=True)
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--reference", type=Path)
    args = parser.parse_args()
    passed, errors = verify(args.submission, args.data, args.reference)
    print(json.dumps({"passed": passed, "errors": errors}))
    raise SystemExit(0 if passed else 1)
