"""Finite partially observable planning with temporal evidence and robust tail risk."""
from __future__ import annotations

import argparse
import csv
import hashlib
import itertools
import json
from decimal import Decimal
from pathlib import Path


def unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key: " + key)
        result[key] = value
    return result


def load(path):
    return json.loads(path.read_text(), object_pairs_hook=unique)


def num(value):
    if isinstance(value, bool):
        raise ValueError("boolean is not numeric")
    value = Decimal(str(value))
    if not value.is_finite():
        raise ValueError("nonfinite number")
    return value


def hashes(data):
    return {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(data.glob("*.json"))}


def resolve(data):
    rules, catalog, ledger = (load(data / name) for name in ("rules.json", "catalog.json", "evidence.json"))
    selected, audit = {}, []
    for action in catalog["actions"]:
        rows = [r for r in ledger if r["action_id"] == action["id"] and r["published_at"] <= rules["decision_date"]]
        latest = max(rows, key=lambda r: (r["published_at"], r["revision"])) if rows else None
        usable = latest is not None and latest["status"] == "active"
        audit.append({"action_id": action["id"], "revision": latest["revision"] if latest else None,
                      "status": latest["status"] if latest else "unavailable", "usable": usable})
        if usable:
            selected[action["id"]] = latest["reductions"]
    return rules, catalog, selected, sorted(audit, key=lambda r: r["action_id"])


def tail_risk(losses, probabilities, alpha):
    remaining = Decimal(1) - num(alpha)
    mass = remaining
    value = Decimal(0)
    for state in sorted(losses, key=lambda s: (-losses[s], s)):
        take = min(remaining, num(probabilities[state]))
        value += take * losses[state]
        remaining -= take
        if remaining == 0:
            break
    if remaining != 0:
        raise ValueError("probability mass below tail mass")
    return value / mass


def evaluate(probe, mapping, rules, catalog, evidence):
    actions = {a["id"]: a for a in catalog["actions"]}
    families = sorted({actions[a]["family"] for a in mapping.values()})
    setup = sum((num(rules["setup_costs"][f]) for f in families), Decimal(0))
    upfront = num(probe["cost"]) + setup
    rows, losses = [], {}
    for state in sorted(rules["states"]):
        observation = probe["observations"][state]
        aid = mapping[observation]
        residual = {axis: max(Decimal(0), num(initial) - num(evidence[aid][state][axis]))
                    for axis, initial in rules["initial_uncertainty"].items()}
        loss = max(residual.values())
        cost = upfront + num(actions[aid]["cost"])
        losses[state] = loss
        rows.append({"state": state, "observation": observation, "action_id": aid,
                     **{axis + "_residual": float(v) for axis, v in residual.items()},
                     "loss": float(loss), "cost": float(cost)})
    risks = [{"model_id": model["id"],
              "mean_loss": float(sum(num(p) * losses[s] for s, p in model["probabilities"].items())),
              "cvar": float(tail_risk(losses, model["probabilities"], rules["alpha"]))}
             for model in rules["probability_models"]]
    worst_cost = max(r["cost"] for r in rows)
    eligible = (upfront <= num(rules["commitment_budget"]) and num(worst_cost) <= num(rules["total_budget"])
                and all(num(r[axis + "_residual"]) <= num(limit) for r in rows
                        for axis, limit in rules["critical_thresholds"].items()))
    return {"probe_id": probe["id"], "observation_policy": mapping, "setup_families": families,
            "setup_cost": float(setup), "worst_cost": worst_cost,
            "robust_cvar": max(r["cvar"] for r in risks),
            "worst_mean_loss": max(r["mean_loss"] for r in risks),
            "eligible": eligible, "states": rows, "risk_by_model": risks}


def objective(policy):
    return (policy["robust_cvar"], policy["worst_mean_loss"], policy["worst_cost"], policy["setup_cost"],
            policy["probe_id"], tuple(sorted(policy["observation_policy"].items())))


def enumerate_policies(data):
    rules, catalog, evidence, _ = resolve(data)
    results = []
    for probe in catalog["probes"]:
        observations = sorted(set(probe["observations"].values()))
        choices = [a["id"] for a in catalog["actions"] if a["id"] in evidence
                   and set(a["requires"]) <= set(probe["capabilities"])]
        for actions in itertools.product(choices, repeat=len(observations)):
            results.append(evaluate(probe, dict(zip(observations, actions)), rules, catalog, evidence))
    return results


SELECTED = ("probe_id", "observation_policy", "setup_families", "setup_cost", "worst_cost", "robust_cvar", "worst_mean_loss")
ROUTE = ("state", "observation", "action_id", "signal_residual", "selectivity_residual", "loss", "cost")


def selected(policy):
    return ({k: policy[k] for k in SELECTED} if policy else dict(zip(SELECTED, (None, {}, [], None, None, None, None))))


def expected(data):
    policies = enumerate_policies(data)
    eligible = [p for p in policies if p["eligible"]]
    winner = min(eligible, key=objective) if eligible else None
    catalog = load(data / "catalog.json")
    summaries = []
    for probe in catalog["probes"]:
        options = [p for p in eligible if p["probe_id"] == probe["id"]]
        summaries.append({"probe_id": probe["id"], "best_policy": selected(min(options, key=objective)) if options else None})
    return {"winner": winner, "summaries": summaries, "evidence_resolution": resolve(data)[3], "hashes": hashes(data)}


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
            errors.append(path + ": incorrect boolean")
    elif isinstance(wanted, (int, float)):
        try:
            if abs(num(actual) - num(wanted)) > Decimal("0.000001"):
                errors.append(path + ": wrong number")
        except (ValueError, ArithmeticError):
            errors.append(path + ": invalid number")
    elif actual != wanted:
        errors.append(path + ": mismatch")


def keyed(rows, key):
    if not isinstance(rows, list) or any(not isinstance(r, dict) or key not in r for r in rows):
        raise ValueError("missing row key: " + key)
    result = {}
    for row in rows:
        if row[key] in result:
            raise ValueError("duplicate row: " + str(row[key]))
        result[row[key]] = row
    return result


def check_rows(actual, wanted, key, label, errors):
    left, right = keyed(actual, key), keyed(wanted, key)
    if set(left) != set(right):
        errors.append(label + ": coverage mismatch")
    for name in left.keys() & right.keys():
        compare(left[name], right[name], label + "." + name, errors)


def verify(submission, data, reference=None):
    for name in ("plan.json", "decision.json", "route.tsv", "provenance.json", "audit.md"):
        if not (submission / name).is_file():
            return False, ["delivery_error: missing " + name]
    errors = []
    try:
        exp = expected(data)
        winner = exp["winner"]
        plan, decision, prov = (load(submission / name) for name in ("plan.json", "decision.json", "provenance.json"))
        for payload, label in ((plan, "plan"), (decision, "decision")):
            if "setup_families" in payload:
                payload["setup_families"] = sorted(payload["setup_families"])
            compare(payload, selected(winner), label, errors)
            if payload.get("observation_policy") != selected(winner)["observation_policy"]:
                errors.append(label + ": exact observation policy required; hidden states cannot be policy keys")
        compare(decision, {"decision": "execute_policy" if winner else "request_information",
                           "human_review_required": True, "claim_boundary": "synthetic_planning_only"}, "decision", errors)
        for row in plan.get("policies", []):
            if isinstance(row.get("best_policy"), dict) and "setup_families" in row["best_policy"]:
                row["best_policy"]["setup_families"] = sorted(row["best_policy"]["setup_families"])
        check_rows(plan.get("policies"), exp["summaries"], "probe_id", "policies", errors)
        for row in plan["policies"]:
            best = row.get("best_policy")
            match = next((r["best_policy"] for r in exp["summaries"] if r["probe_id"] == row["probe_id"]), None)
            if isinstance(best, dict) and (not match or best.get("observation_policy") != match["observation_policy"]):
                errors.append("policies: exact observation mapping required")
        check_rows(plan.get("risk_by_model"), winner["risk_by_model"] if winner else [], "model_id", "risk", errors)
        check_rows(plan.get("evidence_resolution"), exp["evidence_resolution"], "action_id", "evidence", errors)
        with (submission / "route.tsv").open(newline="") as handle:
            reader = csv.DictReader(handle, delimiter="\t")
            if not set(ROUTE) <= set(reader.fieldnames or []):
                raise ValueError("route.tsv missing header")
            check_rows(list(reader), winner["states"] if winner else [], "state", "route", errors)
        normalized = {}
        for name, value in prov["input_sha256"].items():
            name = name.removeprefix("data/")
            if name in normalized:
                raise ValueError("duplicate normalized hash path")
            normalized[name] = value
        if normalized != exp["hashes"]:
            errors.append("provenance: wrong or missing hash")
        compare(prov, {"rules_version": load(data / "rules.json")["rules_version"], "network": "off", "deterministic": True}, "provenance", errors)
        if not (submission / "audit.md").read_text().strip():
            errors.append("delivery_error: empty audit")
    except (ValueError, TypeError, KeyError, AttributeError, OSError, ArithmeticError) as exc:
        return False, errors + ["contract_error: " + str(exc)]
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
