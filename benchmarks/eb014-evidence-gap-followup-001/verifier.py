from __future__ import annotations

import argparse
import hashlib
import itertools
import json
from decimal import Decimal
from pathlib import Path


def _unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key: " + key)
        result[key] = value
    return result


def load(path):
    def invalid(value):
        raise ValueError("non-finite JSON number: " + value)
    return json.loads(path.read_text(), object_pairs_hook=_unique, parse_constant=invalid)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def number(value):
    if isinstance(value, bool):
        raise ValueError("boolean is not a number")
    result = Decimal(str(value))
    if not result.is_finite():
        raise ValueError("non-finite number")
    return result


def index(rows):
    result = {row["id"]: row for row in rows}
    if len(result) != len(rows):
        raise ValueError("duplicate record ID")
    return result


class Problem:
    def __init__(self, data):
        self.rules = load(data / "rules.json")
        self.evidence = load(data / "evidence.json")
        self.sources = index(load(data / "sources.json"))
        self.actions = index(load(data / "actions.json"))
        self.feedback = load(data / "feedback.json")
        self.premises = index(self.evidence["premises"])
        self.claims = index(self.evidence["claims"])
        index(self.evidence["observations"])
        for outcomes in self.feedback.values():
            if not outcomes:
                raise ValueError("an action needs at least one outcome")
            index(outcomes)
        self.initial = []
        self.audit = []
        for row in self.evidence["observations"]:
            premise = self.premises[row["premise_id"]]
            source = self.sources[row["source_id"]]
            reasons = []
            if source["status"] != "current":
                reasons.append("source_status")
            if source["available_on"] > self.rules["decision_date"]:
                reasons.append("future_source")
            if source["scope"] != premise["scope"]:
                reasons.append("scope")
            effect = self.effect(row)
            self.audit.append({
                "id": row["id"], "source_id": source["id"],
                "premise_id": premise["id"],
                "independence_group": source["independence_group"],
                "effect": float(effect), "included": not reasons,
                "exclusion_reasons": reasons,
            })
            if not reasons:
                self.initial.append((premise["id"], source["independence_group"], effect))

    @staticmethod
    def effect(row):
        def mean(values):
            if not values:
                raise ValueError("empty measurement cell")
            return sum(map(number, values)) / len(values)
        return mean(row["treatment"]) - mean(row["control"])

    def ledger(self, observations):
        premises = []
        for key, premise in sorted(self.premises.items()):
            groups = {}
            for premise_id, group, effect in observations:
                if premise_id == key:
                    groups[group] = groups.get(group, True) and effect >= number(premise["min_effect"])
            positive = sorted(group for group, ok in groups.items() if ok)
            negative = sorted(group for group, ok in groups.items() if not ok)
            status = "refuted" if negative else "supported" if len(positive) >= premise["quorum"] else "unknown"
            premises.append({"id": key, "status": status, "positive_groups": positive, "negative_groups": negative})
        states = {row["id"]: row["status"] for row in premises}
        claims = []
        for key, claim in sorted(self.claims.items()):
            required = [states[p] for p in claim["requires"]]
            status = "refuted" if "refuted" in required else "supported" if all(s == "supported" for s in required) else "unknown"
            claims.append({
                "id": key, "scope": claim["scope"], "status": status,
                "allowed": status == "supported",
                "blocking_premises": sorted(p for p in claim["requires"] if states[p] != "supported"),
            })
        allowed = {self.claims[row["id"]]["permission"] for row in claims if row["allowed"]}
        ceiling = next((p for p in self.rules["claim_order"] if p in allowed), None)
        return {"premises": premises, "claims": claims, "claim_ceiling": ceiling}

    def legal(self, observations, used, cost):
        ledger = self.ledger(observations)
        if all(row["status"] != "unknown" for row in ledger["claims"] if self.claims[row["id"]]["resolution_weight"] > 0):
            return []
        states = {r["id"]: r["status"] for r in ledger["premises"]}
        return [
            action for key, action in sorted(self.actions.items())
            if key not in used and action["status"] == "current"
            and action["available_on"] <= self.rules["decision_date"]
            and cost + number(action["cost"]) <= number(self.rules["budget"])
            and all(states[p] == "supported" for p in action["depends_on"])
        ]

    def append(self, observations, action, outcome):
        if action["scope"] != self.premises[action["premise_id"]]["scope"]:
            return observations[:]
        return observations + [(action["premise_id"], action["independence_group"], self.effect(outcome))]

    def leaf(self, observations, path, cost):
        ledger = self.ledger(observations)
        return {
            "id": json.dumps(path, separators=(",", ":")),
            "path": path, "cost": float(cost),
            "premises": {r["id"]: r["status"] for r in ledger["premises"]},
            "claims": {r["id"]: r["status"] for r in ledger["claims"]},
            "claim_ceiling": ledger["claim_ceiling"],
            "resolved_weight": sum(self.claims[r["id"]]["resolution_weight"] for r in ledger["claims"] if r["status"] != "unknown"),
        }

    def policies(self, observations=None, used=(), path=(), cost=Decimal(0)):
        observations = self.initial if observations is None else observations
        yield {"action": "hold", "branches": {}}, [self.leaf(observations, list(path), cost)]
        if len(used) >= self.rules["max_actions"]:
            return
        for action in self.legal(observations, used, cost):
            outcomes = sorted(self.feedback[action["outcomes"]], key=lambda row: row["id"])
            choices = [
                list(self.policies(
                    self.append(observations, action, result),
                    used + (action["id"],),
                    path + (action["id"] + ":" + result["id"],),
                    cost + number(action["cost"]),
                ))
                for result in outcomes
            ]
            # Enumerate complete contingent trees, not independently optimal branches.
            for combination in itertools.product(*choices):
                tree = {"action": action["id"], "branches": {outcome["id"]: item[0] for outcome, item in zip(outcomes, combination)}}
                yield tree, [leaf for item in combination for leaf in item[1]]


def objective(tree, leaves):
    return {
        "worst_resolved_weight": min(row["resolved_weight"] for row in leaves),
        "worst_cost": max(row["cost"] for row in leaves),
        "max_action_count": max(len(row["path"]) for row in leaves),
        "policy_key": json.dumps(tree, sort_keys=True, separators=(",", ":")),
    }


def rank(value):
    return (-value["worst_resolved_weight"], value["worst_cost"], value["max_action_count"], value["policy_key"])


def expected(data):
    problem = Problem(data)
    candidates = [(objective(tree, leaves), tree, leaves) for tree, leaves in problem.policies()]
    value, tree, leaves = min(candidates, key=lambda item: rank(item[0]))
    ledger = problem.ledger(problem.initial)
    ledger["observations"] = problem.audit
    return {
        "claim_ledger.json": ledger,
        "research_plan.json": {
            "policy": tree, "objective": value,
            "stop_reason": "hold" if tree["action"] == "hold" else "conditional_plan",
        },
        "adaptive_update.json": {"hypothetical": True, "leaves": leaves},
        "provenance.json": {
            "input_sha256": {p.name: sha(p) for p in sorted(data.glob("*.json"))},
            "rules_version": problem.rules["rules_version"], "network": "off", "deterministic": True,
        },
    }


def compare(actual, wanted, path, errors):
    if isinstance(wanted, bool) or wanted is None or isinstance(wanted, str):
        if type(actual) is not type(wanted) or actual != wanted:
            errors.append("scientific: " + path + " mismatch")
    elif isinstance(wanted, (float, int)):
        try:
            if abs(number(actual) - number(wanted)) > Decimal("0.00000001"):
                errors.append("scientific: " + path + " mismatch")
        except (ValueError, ArithmeticError):
            errors.append("contract: " + path + " must be finite numeric")
    elif isinstance(wanted, dict):
        if not isinstance(actual, dict):
            errors.append("contract: " + path + " must be an object")
            return
        actual = {k: v for k, v in actual.items() if k != "notes"}
        if set(actual) != set(wanted):
            errors.append("contract: " + path + " key coverage mismatch")
        for key in wanted:
            if key in actual:
                compare(actual[key], wanted[key], path + "." + key, errors)
    elif isinstance(wanted, list):
        if wanted and isinstance(wanted[0], dict) and "id" in wanted[0]:
            if isinstance(actual, dict):
                rows = []
                for key, row in actual.items():
                    if not isinstance(row, dict) or row.get("id", key) != key:
                        errors.append("contract: " + path + " keyed row identity mismatch")
                        return
                    rows.append(dict(row, id=key))
                actual = rows
            if not isinstance(actual, list) or not all(isinstance(row, dict) and isinstance(row.get("id"), str) for row in actual):
                errors.append("contract: " + path + " requires identified rows")
                return
            ids = [row["id"] for row in actual]
            if len(ids) != len(set(ids)) or set(ids) != {row["id"] for row in wanted}:
                errors.append("contract: " + path + " row coverage mismatch")
                return
            by_id = {row["id"]: row for row in actual}
            for row in wanted:
                compare(by_id[row["id"]], row, path + "[" + row["id"] + "]", errors)
        elif not isinstance(actual, list):
            errors.append("contract: " + path + " requires an array")
        elif path.endswith(".path"):
            if actual != wanted:
                errors.append("scientific: " + path + " ordered path mismatch")
        elif sorted(map(lambda v: json.dumps(v, sort_keys=True), actual)) != sorted(map(lambda v: json.dumps(v, sort_keys=True), wanted)):
            errors.append("scientific: " + path + " members mismatch")


def verify(submission, data, reference=None):
    wanted = expected(data)
    errors = []
    for name, document in wanted.items():
        try:
            actual = load(submission / name)
            if name == "provenance.json" and isinstance(actual, dict) and isinstance(actual.get("input_sha256"), dict):
                hashes = actual["input_sha256"]
                normalized = {k.removeprefix("data/"): v for k, v in hashes.items()}
                if len(normalized) != len(hashes):
                    errors.append("contract: duplicate normalized input path")
                actual["input_sha256"] = normalized
            compare(actual, document, name, errors)
        except (OSError, ValueError, UnicodeError) as exc:
            errors.append("delivery: " + name + ": " + str(exc))
    try:
        audit = (submission / "audit.md").read_text()
        if not audit.strip():
            errors.append("delivery: empty audit.md")
    except (OSError, UnicodeError) as exc:
        errors.append("delivery: audit.md: " + str(exc))
    return not errors, errors


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--submission", type=Path, required=True)
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--reference", type=Path, required=True)
    args = parser.parse_args()
    passed, errors = verify(args.submission, args.data, args.reference)
    print(json.dumps({"passed": passed, "errors": errors}))
    raise SystemExit(0 if passed else 1)
