from __future__ import annotations

import argparse
import csv
import hashlib
import itertools
import json
from pathlib import Path


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _num(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _empty_result(data: Path, rules: dict, rows: list[dict]) -> dict:
    return {
        "best_batch": None,
        "legal_batches": [],
        "reference_batch": [],
        "material_cost": None,
        "budget": rules.get("material_budget"),
        "required_groups": rules.get("required_groups", []),
        "batch_size": rules.get("batch_size"),
        "candidate_ids": sorted(row.get("candidate_id", "") for row in rows),
        "eligible_candidate_ids": sorted(row.get("candidate_id", "") for row in rows if row.get("scope") == "active"),
        "excluded_candidate_ids": sorted(row.get("candidate_id", "") for row in rows if row.get("scope") != "active"),
        "incompatibility_pairs": [sorted(pair) for pair in rules.get("incompatibility_pairs", [])],
        "evidence_complete": False,
        "hashes": {name: sha(data / name) for name in ("candidates.csv", "constraints.json", "pairwise_correlation.csv", "scenarios.json")},
        "rules_version": rules.get("rules_version"),
    }


def expected(data: Path) -> dict:
    rules = json.loads((data / "constraints.json").read_text())
    rows = list(csv.DictReader((data / "candidates.csv").open(newline="")))
    scenario_path = data / "scenarios.json"
    scenarios = json.loads(scenario_path.read_text()) if scenario_path.exists() else [{"scenario_id": "nominal", "weight": 1.0, "gain_multiplier": 1.0, "failure_multiplier": 1.0}]
    required = ("candidate_id", "scope", "group", "material_cost", "predicted_gain", "uncertainty", "failure_probability")
    if len({row.get("candidate_id") for row in rows}) != len(rows):
        return _empty_result(data, rules, rows)
    if any(any(field not in row or _num(row[field]) is None for field in required[3:]) or any(field not in row for field in required[:3]) for row in rows):
        return _empty_result(data, rules, rows)
    if any("outcome" in field.lower() or "observed" in field.lower() for field in rows[0]):
        return _empty_result(data, rules, rows)

    correlations = {}
    for row in csv.DictReader((data / "pairwise_correlation.csv").open(newline="")):
        correlations[frozenset((row["candidate_a"], row["candidate_b"]))] = abs(float(row["correlation"]))
    active = [row for row in rows if row.get("scope") == "active"]
    incompatible = {frozenset(pair) for pair in rules.get("incompatibility_pairs", [])}
    legal_batches = []
    for batch in itertools.combinations(active, int(rules["batch_size"])):
        ids = sorted(row["candidate_id"] for row in batch)
        cost = sum(float(row["material_cost"]) for row in batch)
        groups = {row["group"] for row in batch}
        counts = {group: sum(row["group"] == group for row in batch) for group in groups}
        pairs = [sorted(pair) for pair in incompatible if pair.issubset(ids)]
        if cost > float(rules["material_budget"]):
            continue
        if not set(rules["required_groups"]).issubset(groups):
            continue
        if any(count > int(rules.get("max_per_group", len(batch))) for count in counts.values()):
            continue
        if pairs:
            continue
        candidate_utilities = {}
        for scenario in scenarios:
            candidate_utilities[scenario["scenario_id"]] = {
                row["candidate_id"]: round(
                    float(row["predicted_gain"]) * float(scenario["gain_multiplier"])
                    + float(rules["exploration_weight"]) * float(row["uncertainty"])
                    - float(rules["failure_penalty"]) * float(row["failure_probability"]) * float(scenario["failure_multiplier"]),
                    6,
                )
                for row in batch
            }
        correlation_total = sum(correlations.get(frozenset(pair), 0.0) for pair in itertools.combinations(ids, 2))
        penalty = float(rules["correlation_penalty"]) * correlation_total
        scenario_utilities = {
            scenario["scenario_id"]: round(sum(candidate_utilities[scenario["scenario_id"]].values()) - penalty, 6)
            for scenario in scenarios
        }
        robust = min(scenario_utilities.values())
        weight_total = sum(float(scenario.get("weight", 1.0)) for scenario in scenarios)
        weighted_mean = sum(float(scenario.get("weight", 1.0)) * scenario_utilities[scenario["scenario_id"]] for scenario in scenarios) / weight_total
        legal_batches.append({
            "ids": ids,
            "material_cost": round(cost, 6),
            "groups": sorted(groups),
            "candidate_utilities": candidate_utilities,
            "candidate_utility_sum": {key: round(sum(values.values()), 6) for key, values in candidate_utilities.items()},
            "correlation_penalty": round(penalty, 6),
            "scenario_utilities": scenario_utilities,
            "robust_batch_utility": round(robust, 6),
            "mean_batch_utility": round(weighted_mean, 6),
            "batch_utility": round(robust, 6),
            "incompatible_pairs": pairs,
        })
    best = min(legal_batches, key=lambda item: (-item["robust_batch_utility"], -item["mean_batch_utility"], item["ids"])) if legal_batches else None
    result = _empty_result(data, rules, rows)
    result.update({"best_batch": best, "legal_batches": legal_batches, "reference_batch": best["ids"] if best else [], "material_cost": best["material_cost"] if best else None, "evidence_complete": bool(rows)})
    result["eligible_candidate_ids"] = sorted(row["candidate_id"] for row in active)
    result["excluded_candidate_ids"] = sorted(row["candidate_id"] for row in rows if row.get("scope") != "active")
    result["incompatibility_pairs"] = [sorted(pair) for pair in incompatible]
    return result


def verify(submission: Path, data: Path, reference: Path) -> tuple[bool, list[str]]:
    exp, errors = expected(data), []
    for name in ("next_batch.csv", "constraint_check.json", "uncertainty_table.tsv", "selection_rationale.md"):
        if not (submission / name).is_file():
            errors.append("missing artifact: " + name)
    if errors:
        return False, errors
    best = exp["best_batch"]
    rows = list(csv.DictReader((submission / "next_batch.csv").open(newline="")))
    selected_ids = sorted(row.get("candidate_id", "") for row in rows)
    if best is None or selected_ids != best["ids"]:
        errors.append("next batch is not optimal under robust scenario utility")
    required_columns = {"candidate_id", "group", "material_cost", "predicted_gain", "uncertainty", "failure_probability", "candidate_utility"}
    if not rows or not required_columns.issubset(rows[0]):
        errors.append("next batch lacks acquisition evidence columns")
    elif "scope" in rows[0] and any(row.get("scope") != "active" for row in rows):
        errors.append("next batch contains a non-active candidate")
    candidates = {row["candidate_id"]: row for row in csv.DictReader((data / "candidates.csv").open(newline=""))}
    for row in rows:
        source = candidates.get(row.get("candidate_id"))
        if source is None or source.get("scope") != "active":
            errors.append(f"{row.get('candidate_id')} is not an active candidate")
            continue
        for field in ("group", "material_cost", "predicted_gain", "uncertainty", "failure_probability"):
            if field in row and str(row[field]) != str(source[field]):
                errors.append(f"{row.get('candidate_id')} {field} mismatch")
    check = json.loads((submission / "constraint_check.json").read_text())
    if best is not None:
        if check.get("legal", check.get("overall_pass")) is not True:
            errors.append("constraint check must pass")
        if abs(float(check.get("material_cost", -1)) - best["material_cost"]) > 1e-5:
            errors.append("constraint check material cost mismatch")
        if "scenario_utilities" in check and check.get("scenario_utilities") != best["scenario_utilities"]:
            errors.append("constraint check scenario utilities mismatch")
        robust_value = check.get("robust_batch_utility", check.get("batch_utility"))
        if robust_value is not None and abs(float(robust_value) - best["robust_batch_utility"]) > 1e-5:
            errors.append("constraint check robust utility mismatch")
        if "incompatible_pairs" in check and check.get("incompatible_pairs", []) != best["incompatible_pairs"]:
            errors.append("constraint check incompatibility mismatch")
    if check.get("rules_version") not in (None, exp["rules_version"]):
        errors.append("constraint rules version mismatch")
    uncertainty_rows = list(csv.DictReader((submission / "uncertainty_table.tsv").open(newline=""), delimiter="\t"))
    if sorted(row.get("candidate_id", "") for row in uncertainty_rows) != exp["candidate_ids"]:
        errors.append("uncertainty table must cover every candidate")
    selected_set = set(exp["reference_batch"])
    for row in uncertainty_rows:
        if row.get("candidate_id") in candidates and "selected" in row:
            value = _num(row.get("selected"))
            selected = row.get("selected", "").strip().lower() in {"true", "yes", "1", "selected"}
            if selected != (row["candidate_id"] in selected_set):
                errors.append(f"{row['candidate_id']} selection audit mismatch")
    text = (submission / "selection_rationale.md").read_text().lower()
    for concept, alternatives in {"scenario robustness": ("scenario", "worst-case", "robust"), "exploration": ("exploration", "uncertainty"), "failure risk": ("failure", "risk"), "redundancy": ("correlation", "redundan", "incompatib"), "feasibility": ("budget", "feasible"), "planning boundary": ("planning recommendation", "not an experimental result", "human review")}.items():
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
