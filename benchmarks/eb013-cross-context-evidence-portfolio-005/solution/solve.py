#!/usr/bin/env python3
"""Standalone exact portfolio planner used by the author-side oracle."""
from __future__ import annotations

import argparse
import csv
import hashlib
import itertools
import json
import shutil
from decimal import Decimal
from pathlib import Path


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def number(value):
    result = Decimal(str(value))
    if not result.is_finite():
        raise ValueError("nonfinite number")
    return result


def classify(context, rows, rules):
    eligible = [
        row for row in rows
        if row["context_id"] == context
        and row["quality"] == "pass"
        and row["independence"] == "independent"
    ]
    effects = [number(row["effect"]) for row in eligible]
    threshold = number(rules["effect_threshold"])
    if len(effects) < rules["minimum_independent_groups"]:
        decision = "INSUFFICIENT"
    elif min(effects) < -threshold and max(effects) > threshold:
        decision = "CONFLICTED"
    elif abs(sum(effects, Decimal(0)) / len(effects)) >= threshold:
        decision = "SUPPORTED"
    else:
        decision = "INSUFFICIENT"
    return {
        "context_id": context,
        "n_independent": len(eligible),
        "mean_effect": float(sum(effects, Decimal(0)) / len(effects)) if effects else None,
        "min_effect": float(min(effects)) if effects else None,
        "max_effect": float(max(effects)) if effects else None,
        "decision": decision,
        "pooled_shortcut_invalid": decision == "CONFLICTED",
    }


def evaluate(selected, rules, baseline, option_map):
    rows = [dict(row) for row in baseline]
    total = Decimal(0)
    for option_id in sorted(selected):
        option = option_map[option_id]
        total += number(option["cost"])
        if option["kind"] == "replace":
            rows = [row for row in rows if row["record_id"] != option["replaces"]]
        rows.append({**option["evidence"], "source": option_id})
    contexts = [classify(context, rows, rules) for context in rules["contexts"]]
    return {
        "selected_followups": sorted(selected),
        "total_cost": float(total),
        "eligible": total <= number(rules["followup_budget"]),
        "supported_count": sum(row["decision"] == "SUPPORTED" for row in contexts),
        "conflicted_count": sum(row["decision"] == "CONFLICTED" for row in contexts),
        "insufficient_count": sum(row["decision"] == "INSUFFICIENT" for row in contexts),
        "contexts": contexts,
    }


def objective(result):
    return (
        -result["supported_count"],
        result["conflicted_count"],
        result["insufficient_count"],
        number(result["total_cost"]),
        tuple(result["selected_followups"]),
    )


def solve(data):
    rules = load(data / "rules.json")
    baseline = load(data / "evidence.json")["baseline"]
    options = load(data / "followups.json")["options"]
    option_map = {row["option_id"]: row for row in options}
    candidates = []
    ids = sorted(option_map)
    for size in range(len(ids) + 1):
        for selected in itertools.combinations(ids, size):
            result = evaluate(selected, rules, baseline, option_map)
            if result["eligible"]:
                candidates.append(result)
    return min(candidates, key=objective) if candidates else None


def write_outputs(data, out):
    out.mkdir(parents=True, exist_ok=True)
    rules = load(data / "rules.json")
    options = load(data / "followups.json")["options"]
    winner = solve(data)
    summary = (
        {key: winner[key] for key in ("selected_followups", "total_cost", "supported_count", "conflicted_count", "insufficient_count")}
        if winner else
        {"selected_followups": [], "total_cost": None, "supported_count": 0, "conflicted_count": 0, "insufficient_count": 0}
    )
    (out / "plan.json").write_text(json.dumps({**summary, "contexts": winner["contexts"] if winner else []}, indent=2) + "\n")
    (out / "decision.json").write_text(json.dumps({**summary, "decision": "execute_followups" if winner else "request_information", "human_review_required": True, "claim_boundary": rules["claim_boundary"]}, indent=2) + "\n")
    with (out / "portfolio.tsv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["option_id", "selected", "cost", "kind", "description"], delimiter="\t")
        writer.writeheader()
        selected = set(winner["selected_followups"] if winner else [])
        for option in options:
            writer.writerow({"option_id": option["option_id"], "selected": str(option["option_id"] in selected).lower(), "cost": option["cost"], "kind": option["kind"], "description": option["description"]})
    with (out / "context.tsv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["context_id", "n_independent", "mean_effect", "min_effect", "max_effect", "decision", "pooled_shortcut_invalid"], delimiter="\t")
        writer.writeheader()
        writer.writerows(winner["contexts"] if winner else [])
    hashes = {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in sorted(data.glob("*.json"))}
    (out / "provenance.json").write_text(json.dumps({"input_sha256": hashes, "rules_version": rules["rules_version"], "network": "off", "deterministic": True}, indent=2) + "\n")
    (out / "audit.md").write_text("Independent groups are counted by context; replacements remove only their declared record; conflicts precede mean support. The exact lexicographic optimum is context evidence only and requires human review.\n")
    shutil.copy2(Path(__file__), out / "planner.py")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    write_outputs(args.data, args.out)
