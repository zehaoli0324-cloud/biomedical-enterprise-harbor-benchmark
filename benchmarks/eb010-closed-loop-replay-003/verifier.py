from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path


BLOCKER_ALIASES = {
    "cost_exceeds_max_budget": "budget",
    "max_budget_exceeded": "budget",
    "budget_exceeded": "budget",
    "future_outcome": "future_outcome_leakage",
    "uses_future_outcome": "future_outcome_leakage",
    "unstable": "replay_stability",
    "insufficient_seeds": "replay_stability",
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _canonical_blockers(values) -> list[str]:
    if not isinstance(values, list):
        return []
    return [BLOCKER_ALIASES.get(str(value), str(value)) for value in values]


def expected(data: Path) -> dict:
    case = json.loads((data / "case.json").read_text())
    rules = json.loads((data / "rules.json").read_text())
    results = {}
    for policy in case["policies"]:
        actions = policy["actions"]
        cost = round(sum(float(row.get("cost", 0)) for row in actions), 6)
        order_ok = [row.get("stage") for row in actions] == case["stage_order"]
        leakage = any(
            row.get("uses_future_outcome") is True
            or any("outcome" in key.lower() and key != "uses_future_outcome" for key in row)
            for row in actions
        )
        replay = [row for row in case["replays"] if row["policy_id"] == policy["policy_id"]]
        gains = [float(row["observed_gain"]) for row in replay]
        spread = round(max(gains) - min(gains), 6) if gains else None
        seed_count = len({row["replay_id"] for row in replay})
        stable = spread is not None and seed_count >= rules["min_seed_count"] and spread <= rules["max_utility_range"]
        eligible = policy["scope"] == "active" and cost <= rules["max_budget"] and order_ok and not leakage and stable
        blockers = []
        if policy["scope"] != "active":
            blockers.append("scope")
        if cost > rules["max_budget"]:
            blockers.append("budget")
        if not order_ok:
            blockers.append("stage_order")
        if leakage:
            blockers.append("future_outcome_leakage")
        if not stable:
            blockers.append("replay_stability")
        results[policy["policy_id"]] = {
            "cost": cost,
            "budget_ok": cost <= rules["max_budget"],
            "order_ok": order_ok,
            "future_outcome_leakage": leakage,
            "seed_count": seed_count,
            "utility": round(sum(gains) / len(gains), 6) if gains else None,
            "utility_range": spread,
            "stable": stable,
            "blocker_reasons": blockers,
            "eligible": eligible,
        }
    eligible = [(key, value) for key, value in results.items() if value["eligible"]]
    selected = min(eligible, key=lambda pair: (-pair[1]["utility"], pair[0]))[0] if eligible else "request_information"
    return {"selected_policy": selected, "policies": results, "replays": case["replays"], "hashes": {"case.json": sha(data / "case.json"), "rules.json": sha(data / "rules.json")}, "rules_version": rules["rules_version"]}


def verify(submission: Path, data: Path, reference: Path) -> tuple[bool, list[str]]:
    exp, errors = expected(data), []
    for name in ("policy.json", "replay.tsv", "audit.md", "manifest.json"):
        if not (submission / name).is_file():
            errors.append("missing artifact: " + name)
    if errors:
        return False, errors
    report = json.loads((submission / "policy.json").read_text())
    if report.get("selected_policy") != exp["selected_policy"]:
        errors.append("selected policy mismatch")
    if report.get("rules_version") != exp["rules_version"]:
        errors.append("policy rules version mismatch")
    if report.get("claim_boundary") != "planning_only_not_experimental_proof":
        errors.append("claim boundary mismatch")
    if report.get("human_review_required") is not True:
        errors.append("human review gate mismatch")
    submitted_policies = report.get("policies", {})
    if not isinstance(submitted_policies, dict) or set(submitted_policies) != set(exp["policies"]):
        errors.append("policy report must cover every policy exactly once")
    for policy_id, expected_row in exp["policies"].items():
        row = submitted_policies.get(policy_id, {}) if isinstance(submitted_policies, dict) else {}
        for field in ("budget_ok", "order_ok", "future_outcome_leakage", "seed_count", "stable", "eligible"):
            if row.get(field) != expected_row[field]:
                errors.append(f"{policy_id} {field} mismatch")
        for field in ("cost", "utility", "utility_range"):
            actual = row.get(field)
            expected_value = expected_row[field]
            if not isinstance(actual, (int, float)) or abs(float(actual) - expected_value) > 1e-6:
                errors.append(f"{policy_id} {field} mismatch")
        if sorted(_canonical_blockers(row.get("blocker_reasons", []))) != sorted(expected_row["blocker_reasons"]):
            errors.append(f"{policy_id} blocker reasons mismatch")
    replay_rows = list(csv.DictReader((submission / "replay.tsv").open(newline=""), delimiter="\t"))
    actual_replays = {}
    for row in replay_rows:
        key = (row.get("replay_id"), row.get("policy_id"))
        try:
            actual_replays[key] = float(row.get("observed_gain", ""))
        except (TypeError, ValueError):
            actual_replays[key] = None
    expected_replays = {(row["replay_id"], row["policy_id"]): float(row["observed_gain"]) for row in exp["replays"]}
    if set(actual_replays) != set(expected_replays) or any(
        actual_replays.get(key) is None or abs(actual_replays[key] - value) > 1e-6
        for key, value in expected_replays.items()
    ):
        errors.append("replay table coverage mismatch")
    audit = (submission / "audit.md").read_text().lower()
    if len(audit.split()) < 20:
        errors.append("audit is too short to explain the decision")
    manifest = json.loads((submission / "manifest.json").read_text())
    if manifest.get("input_sha256") != exp["hashes"] or manifest.get("rules_version") != exp["rules_version"] or manifest.get("deterministic") is not True:
        errors.append("manifest provenance mismatch")
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
