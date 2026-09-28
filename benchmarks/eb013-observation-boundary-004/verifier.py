"""Exact finite-policy oracle for observation-limited evidence routing."""
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
from decimal import Decimal
from pathlib import Path


def unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate key: " + key)
        result[key] = value
    return result


def load(path):
    return json.loads(path.read_text(), object_pairs_hook=unique)


def num(value):
    if isinstance(value, bool):
        raise ValueError("boolean numeric value")
    value = Decimal(str(value))
    if not value.is_finite():
        raise ValueError("nonfinite value")
    return value


def inputs(data):
    return tuple(load(data / name) for name in ("rules.json", "requests.json", "worlds.json", "sources.json"))


def blockers(action, sources, rules):
    source = sources[action["source_id"]]
    failed = []
    if source["status"] != "current":
        failed.append("source_status")
    if source["available_at"] > rules["decision_date"]:
        failed.append("future_source")
    if source["scope"] != rules["scope"]:
        failed.append("source_scope")
    if action["future_outcome"]:
        failed.append("future_outcome")
    return sorted(failed)


def evaluate(first, mapping, rules, requests, worlds):
    actions = {a["id"]: a for a in requests["stage2"]}
    selected = [actions[rid] for rid in mapping.values()]
    families = sorted({a["family"] for a in selected})
    setup = sum((num(rules["setup_costs"][f]) for f in families), Decimal(0))
    upfront = num(first["cost"]) + setup
    capacity = sum(rules["setup_slots"][f] for f in families)
    rows = []
    for world in worlds:
        observation = first["observations"][world["id"]]
        action = actions[mapping[observation]]
        residuals = {}
        for axis, initial in world["initial"].items():
            left = num(first["covers"].get(axis, 0))
            right = num(action["covers"][world["scenario"]].get(axis, 0))
            reduction = max(left, right) if first["group"] == action["group"] else left + right
            residuals[axis] = max(Decimal(0), num(initial) - reduction)
        cost = upfront + num(action["cost"])
        duration = num(first["hours"]) + num(action["hours"])
        failed = []
        if any(residuals[k] > num(t) for k, t in rules["thresholds"].items()):
            failed.append("critical_threshold")
        if cost > num(rules["total_budget"]):
            failed.append("total_budget")
        if duration > num(rules["deadline_hours"]):
            failed.append("deadline")
        rows.append({"world_id": world["id"], "observation": observation, "action_id": action["id"],
                     "residuals": {k: float(v) for k, v in residuals.items()}, "cost": float(cost),
                     "hours": float(duration), "blockers": sorted(failed)})
    failed = set()
    if num(first["cost"]) > num(rules["stage1_budget"]):
        failed.add("stage1_budget")
    if upfront > num(rules["commitment_budget"]):
        failed.add("commitment_budget")
    if capacity > rules["capacity_slots"]:
        failed.add("capacity")
    for row in rows:
        failed.update(row["blockers"])
    risk = max(num(row["residuals"][axis]) / num(threshold)
               for row in rows for axis, threshold in rules["thresholds"].items())
    return {"stage1_id": first["id"], "policy": mapping, "setup_families": families,
            "setup_cost": float(setup), "setup_slots": capacity, "worst_cost": max(r["cost"] for r in rows),
            "risk": float(risk), "blockers": sorted(failed), "eligible": not failed, "replay": rows}


def objective(policy):
    return (num(policy["risk"]), num(policy["worst_cost"]), num(policy["setup_cost"]),
            policy["stage1_id"], tuple(sorted(policy["policy"].items())))


def expected(data):
    rules, requests, worlds, sources = inputs(data)
    policies, summaries = [], []
    for first in requests["stage1"]:
        observations = sorted(set(first["observations"].values()))
        options = [[a["id"] for a in requests["stage2"] if not blockers(a, sources, rules)
                    and set(a["dependencies"]) <= {first["id"]}
                    and observation in a["allowed_observations"]] for observation in observations]
        candidates = [evaluate(first, dict(zip(observations, actions)), rules, requests, worlds)
                      for actions in itertools.product(*options)]
        eligible = [p for p in candidates if p["eligible"]]
        best = min(eligible, key=objective) if eligible else None
        summaries.append({"stage1_id": first["id"], "policy_count": len(candidates),
                          "eligible_count": len(eligible), "best": summary(best) if best else None})
        policies.extend(candidates)
    eligible = [p for p in policies if p["eligible"]]
    winner = min(eligible, key=objective) if eligible else None
    return {"winner": winner, "summaries": summaries, "policies": policies,
            "source_audit": [{"action_id": a["id"], "blockers": blockers(a, sources, rules)} for a in requests["stage2"]],
            "hashes": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(data.glob("*.json"))}}


def summary(policy):
    return {key: value for key, value in policy.items() if key not in {"replay", "blockers", "eligible"}}


def compare(actual, wanted, path, errors):
    if isinstance(wanted, dict):
        if not isinstance(actual, dict):
            errors.append(path + ": object required")
            return
        for key, value in wanted.items():
            if key not in actual:
                errors.append(path + "." + key + ": missing")
            else:
                compare(actual[key], value, path + "." + key, errors)
    elif isinstance(wanted, bool):
        if actual is not wanted:
            errors.append(path + ": boolean mismatch")
    elif isinstance(wanted, (int, float)):
        try:
            if abs(num(actual) - num(wanted)) > Decimal("0.000001"):
                errors.append(path + ": numeric mismatch")
        except (ValueError, ArithmeticError):
            errors.append(path + ": invalid number")
    elif actual != wanted:
        errors.append(path + ": mismatch")


def keyed(rows, key):
    if not isinstance(rows, list) or any(not isinstance(r, dict) or key not in r for r in rows):
        raise ValueError("invalid table: " + key)
    result = {}
    for row in rows:
        if row[key] in result:
            raise ValueError("duplicate row: " + str(row[key]))
        result[row[key]] = row
    return result


def verify(submission, data, reference=None):
    errors = []
    try:
        exp = expected(data)
        rules = load(data / "rules.json")
        plan, decision, prov = [load(submission / name) for name in ("plan.json", "decision.json", "provenance.json")]
        winner = exp["winner"]
        wanted = summary(winner) if winner else None
        compare(decision, {"decision": "execute" if winner else "hold", "selected": wanted,
                           "claim_boundary": "planning_only", "human_review_required": True}, "decision", errors)
        if winner and decision.get("selected", {}).get("policy") != winner["policy"]:
            errors.append("decision: exact observation mapping required")
        for name, key, expected_rows in (("alternatives", "stage1_id", exp["summaries"]),
                                         ("source_audit", "action_id", exp["source_audit"]),
                                         ("replay", "world_id", winner["replay"] if winner else [])):
            actual = keyed(plan.get(name), key)
            wanted_rows = keyed(expected_rows, key)
            if set(actual) != set(wanted_rows):
                errors.append(name + ": row coverage mismatch")
            for rid in actual.keys() & wanted_rows.keys():
                compare(actual[rid], wanted_rows[rid], name + "." + rid, errors)
                if name == "alternatives" and wanted_rows[rid]["best"] is not None:
                    if actual[rid].get("best", {}).get("policy") != wanted_rows[rid]["best"]["policy"]:
                        errors.append("alternatives: exact observation mapping required")
        normalized = {}
        for name, digest in prov.get("input_sha256", {}).items():
            name = name.removeprefix("data/")
            if name in normalized:
                raise ValueError("duplicate normalized hash")
            normalized[name] = digest
        if normalized != exp["hashes"]:
            errors.append("provenance: hash mismatch")
        compare(prov, {"rules_version": rules["rules_version"], "network": "off", "deterministic": True}, "provenance", errors)
        if not (submission / "audit.md").read_text().strip():
            errors.append("audit: empty")
    except (ValueError, TypeError, KeyError, OSError, ArithmeticError, AttributeError) as exc:
        errors.append("delivery_or_contract: " + str(exc))
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
