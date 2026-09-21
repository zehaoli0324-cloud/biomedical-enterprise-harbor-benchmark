from __future__ import annotations

import argparse
import csv
import hashlib
import itertools
import json
from pathlib import Path


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def expected(data: Path) -> dict:
    rules = json.loads((data / "constraints.json").read_text())
    rows = list(csv.DictReader((data / "candidates.csv").open()))
    correlations = {}
    for row in csv.DictReader((data / "pairwise_correlation.csv").open()):
        correlations[frozenset((row["candidate_a"], row["candidate_b"]))] = abs(float(row["correlation"]))
    legal_batches = []
    for batch in itertools.combinations(rows, rules["batch_size"]):
        ids = sorted(row["candidate_id"] for row in batch)
        cost = sum(float(row["material_cost"]) for row in batch)
        groups = {row["group"] for row in batch}
        if cost > rules["material_budget"] or not set(rules["required_groups"]).issubset(groups):
            continue
        candidate_utilities = {
            row["candidate_id"]: round(
                float(row["predicted_gain"])
                + rules["exploration_weight"] * float(row["uncertainty"])
                - rules["failure_penalty"] * float(row["failure_probability"]),
                6,
            )
            for row in batch
        }
        correlation_total = sum(correlations.get(frozenset(pair), 0.0) for pair in itertools.combinations(ids, 2))
        penalty = rules["correlation_penalty"] * correlation_total
        utility = sum(candidate_utilities.values()) - penalty
        legal_batches.append({
            "ids": ids,
            "material_cost": round(cost, 6),
            "candidate_utilities": candidate_utilities,
            "candidate_utility_sum": round(sum(candidate_utilities.values()), 6),
            "correlation_penalty": round(penalty, 6),
            "batch_utility": round(utility, 6),
        })
    best = min(legal_batches, key=lambda item: (-item["batch_utility"], item["ids"])) if legal_batches else None
    return {
        "best_batch": best,
        "legal_batches": legal_batches,
        "reference_batch": best["ids"] if best else [],
        "material_cost": best["material_cost"] if best else None,
        "budget": rules["material_budget"],
        "required_groups": rules["required_groups"],
        "batch_size": rules["batch_size"],
        "candidate_ids": sorted(row["candidate_id"] for row in rows),
        "hashes": {name: sha(data / name) for name in ("candidates.csv", "constraints.json", "pairwise_correlation.csv")},
        "rules_version": rules["rules_version"],
    }


def verify(submission: Path, data: Path, reference: Path) -> tuple[bool, list[str]]:
    exp, errors = expected(data), []
    for name in ("next_batch.csv", "constraint_check.json", "uncertainty_table.tsv", "selection_rationale.md"):
        if not (submission / name).is_file():
            errors.append("missing artifact: " + name)
    if errors:
        return False, errors
    rows = list(csv.DictReader((submission / "next_batch.csv").open()))
    selected_ids = sorted(row.get("candidate_id", "") for row in rows)
    best = exp["best_batch"]
    if best is None or selected_ids != best["ids"]:
        errors.append("next batch is not optimal under risk-adjusted acquisition utility")
    required_columns = {"candidate_id", "group", "material_cost", "predicted_gain", "uncertainty", "failure_probability", "candidate_utility"}
    if not rows or not required_columns.issubset(rows[0]):
        errors.append("next batch lacks acquisition evidence columns")
    check = json.loads((submission / "constraint_check.json").read_text())
    if check.get("legal", check.get("overall_pass")) is not True:
        errors.append("constraint check must pass")
    for field in ("material_cost", "candidate_utility_sum", "correlation_penalty", "batch_utility"):
        actual = check.get(field)
        if not isinstance(actual, (int, float)) or abs(actual - best[field]) > 1e-5:
            errors.append("constraint check mismatch: " + field)
    if check.get("rules_version") not in (None, exp["rules_version"]):
        errors.append("constraint rules version mismatch")
    uncertainty_rows = list(csv.DictReader((submission / "uncertainty_table.tsv").open(), delimiter="\t"))
    if sorted(row.get("candidate_id", "") for row in uncertainty_rows) != exp["candidate_ids"]:
        errors.append("uncertainty table must cover every candidate")
    text = (submission / "selection_rationale.md").read_text().lower()
    for concept, alternatives in {
        "exploration": ("exploration", "uncertainty"),
        "failure risk": ("failure", "risk"),
        "redundancy": ("correlation", "redundan"),
        "feasibility": ("budget", "feasible"),
        "planning boundary": ("planning recommendation", "not an experimental result", "human review"),
    }.items():
        if not any(term in text for term in alternatives):
            errors.append("selection rationale omits " + concept)
    return not errors, errors


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--submission", type=Path, required=True)
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--reference", type=Path, required=True)
    args = parser.parse_args()
    ok, errors = verify(args.submission, args.data, args.reference)
    print(json.dumps({"passed": ok, "errors": errors}))
    raise SystemExit(0 if ok else 1)
