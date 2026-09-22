"""Choose a bounded independent-evidence follow-up portfolio by context."""
from __future__ import annotations

import argparse
import csv
import hashlib
import itertools
import json
import math
from decimal import Decimal
from pathlib import Path


def unique(pairs):
    out = {}
    for key, value in pairs:
        if key in out:
            raise ValueError("duplicate JSON key: " + key)
        out[key] = value
    return out


def load(path):
    return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=unique)


def number(value):
    if isinstance(value, bool):
        raise ValueError("boolean is not a number")
    result = Decimal(str(value))
    if not result.is_finite():
        raise ValueError("nonfinite number")
    return result


def hashes(data):
    return {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(data.glob("*.json"))}


def apply_portfolio(data, selected):
    rules, evidence, options = (load(data / name) for name in ("rules.json", "evidence.json", "followups.json"))
    rows = [dict(row) for row in evidence["baseline"]]
    option_map = {row["option_id"]: row for row in options["options"]}
    total = Decimal(0)
    for option_id in selected:
        option = option_map[option_id]
        total += number(option["cost"])
        if option["kind"] == "add":
            rows.append({**option["evidence"], "source": option_id})
        elif option["kind"] == "replace":
            rows = [row for row in rows if row["record_id"] != option["replaces"]]
            rows.append({**option["evidence"], "source": option_id})
    return rules, rows, options, total


def classify_context(context_id, rows, rules):
    context_rows = [row for row in rows if row["context_id"] == context_id and row["quality"] == "pass"]
    independent = [row for row in context_rows if row["independence"] == "independent"]
    effects = [number(row["effect"]) for row in independent]
    if len(independent) < rules["minimum_independent_groups"]:
        decision = "INSUFFICIENT"
    elif min(effects) < -number(rules["effect_threshold"]) and max(effects) > number(rules["effect_threshold"]):
        decision = "CONFLICTED"
    elif abs(sum(effects, Decimal(0)) / len(effects)) >= number(rules["effect_threshold"]):
        decision = "SUPPORTED"
    else:
        decision = "INSUFFICIENT"
    return {"context_id": context_id, "n_independent": len(independent),
            "mean_effect": float(sum(effects, Decimal(0)) / len(effects)) if effects else None,
            "min_effect": float(min(effects)) if effects else None,
            "max_effect": float(max(effects)) if effects else None,
            "decision": decision, "pooled_shortcut_invalid": decision == "CONFLICTED"}


def evaluate(data, selected):
    selected = sorted(selected)
    rules, rows, options, total = apply_portfolio(data, selected)
    contexts = [classify_context(context, rows, rules) for context in rules["contexts"]]
    eligible = total <= number(rules["followup_budget"])
    supported = sum(row["decision"] == "SUPPORTED" for row in contexts)
    conflicted = sum(row["decision"] == "CONFLICTED" for row in contexts)
    insufficient = sum(row["decision"] == "INSUFFICIENT" for row in contexts)
    return {"selected_followups": list(selected), "total_cost": float(total), "eligible": eligible,
            "supported_count": supported, "conflicted_count": conflicted, "insufficient_count": insufficient,
            "contexts": contexts}


def objective(result):
    return (-result["supported_count"], result["conflicted_count"], result["insufficient_count"],
            result["total_cost"], tuple(result["selected_followups"]))


def enumerate_portfolios(data):
    options = load(data / "followups.json")["options"]
    results = []
    for size in range(len(options) + 1):
        for selected in itertools.combinations((row["option_id"] for row in options), size):
            results.append(evaluate(data, selected))
    return results


SELECTED = ("selected_followups", "total_cost", "supported_count", "conflicted_count", "insufficient_count")


def selected(result):
    return ({key: result[key] for key in SELECTED} if result else
            {"selected_followups": [], "total_cost": None, "supported_count": 0, "conflicted_count": 0, "insufficient_count": 0})


def expected(data):
    results = enumerate_portfolios(data)
    eligible = [result for result in results if result["eligible"]]
    winner = min(eligible, key=objective) if eligible else None
    return {"winner": winner, "hashes": hashes(data),
            "contexts": load(data / "rules.json")["contexts"],
            "portfolio_count": len(results)}


def compare(actual, wanted, path, errors):
    if wanted is None:
        if actual in (None, ""):
            return
        errors.append(path + ": expected null")
        return
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
        if isinstance(actual, str) and actual.lower() in {"true", "false"}:
            actual = actual.lower() == "true"
        if actual is not wanted:
            errors.append(path + ": wrong boolean")
    elif isinstance(wanted, (int, float)):
        try:
            if not math.isclose(float(number(actual)), wanted, abs_tol=1e-6, rel_tol=0):
                errors.append(path + ": wrong number")
        except (ValueError, ArithmeticError):
            errors.append(path + ": invalid number")
    elif actual != wanted:
        errors.append(path + ": mismatch")


def keyed(rows, key):
    if not isinstance(rows, list) or any(not isinstance(row, dict) or key not in row for row in rows):
        raise ValueError("missing row key: " + key)
    output = {}
    for row in rows:
        if row[key] in output:
            raise ValueError("duplicate row key: " + str(row[key]))
        output[row[key]] = row
    return output


def verify(submission, data, reference=None):
    required = ("plan.json", "decision.json", "portfolio.tsv", "context.tsv", "provenance.json", "audit.md")
    errors = ["delivery_error: missing " + name for name in required if not (submission / name).is_file()]
    if errors:
        return False, errors
    try:
        exp = expected(data)
        winner = exp["winner"]
        plan, decision, provenance = (load(submission / name) for name in ("plan.json", "decision.json", "provenance.json"))
        wanted = selected(winner)
        for payload, label in ((plan, "plan"), (decision, "decision")):
            if "selected_followups" in payload:
                payload["selected_followups"] = sorted(payload["selected_followups"])
            compare(payload, wanted, label, errors)
        compare(decision, {"decision": "execute_followups" if winner else "request_information",
                           "human_review_required": True, "claim_boundary": "context_evidence_only"}, "decision", errors)
        expected_contexts = winner["contexts"] if winner else []
        actual_contexts = keyed(plan.get("contexts"), "context_id")
        required_contexts = keyed(expected_contexts, "context_id")
        if set(actual_contexts) != set(required_contexts):
            errors.append("contexts: exact coverage required")
        for key in actual_contexts.keys() & required_contexts.keys():
            compare(actual_contexts[key], required_contexts[key], "contexts." + key, errors)
        with (submission / "portfolio.tsv").open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle, delimiter="\t"))
        option_map = keyed(rows, "option_id")
        options = load(data / "followups.json")["options"]
        expected_options = keyed([{"option_id": row["option_id"], "selected": row["option_id"] in (winner["selected_followups"] if winner else []),
                                  "cost": row["cost"], "kind": row["kind"], "description": row["description"]}
                                 for row in options], "option_id")
        if set(option_map) != set(expected_options):
            errors.append("portfolio: option coverage required")
        for key in option_map.keys() & expected_options.keys():
            compare(option_map[key], expected_options[key], "portfolio." + key, errors)
        with (submission / "context.tsv").open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle, delimiter="\t"))
        check = keyed(rows, "context_id")
        if set(check) != set(required_contexts):
            errors.append("context_tsv: exact coverage required")
        for key in check.keys() & required_contexts.keys():
            compare(check[key], required_contexts[key], "context_tsv." + key, errors)
        normalized = {name.removeprefix("data/"): value for name, value in provenance.get("input_sha256", {}).items()}
        if normalized != exp["hashes"]:
            errors.append("provenance: wrong or missing hash")
        compare(provenance, {"rules_version": load(data / "rules.json")["rules_version"], "network": "off", "deterministic": True}, "provenance", errors)
        if not (submission / "audit.md").read_text(encoding="utf-8").strip():
            errors.append("delivery_error: empty audit")
    except (ValueError, TypeError, KeyError, OSError, ArithmeticError) as exc:
        errors.append("contract_error: " + str(exc))
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
