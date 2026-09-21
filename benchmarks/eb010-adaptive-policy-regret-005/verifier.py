from __future__ import annotations
import argparse, csv, hashlib, json
from pathlib import Path

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()

def expected(data):
    rules = json.loads((data / "rules.json").read_text())
    scenarios = json.loads((data / "inputs/scenarios.json").read_text())
    actions = {row["action_id"]: row for row in json.loads((data / "inputs/actions.json").read_text())}
    policies = json.loads((data / "inputs/policies.json").read_text())
    required = set(rules["required_observations"])
    rows = {}
    for policy in policies:
        blockers = []
        if policy["scope"] != rules["required_scope"]: blockers.append("scope")
        if set(policy["branches"]) != required: blockers.append("branch_completeness")
        if policy["uses_future_outcome"]: blockers.append("future_outcome_leakage")
        branches = {}
        for scenario in scenarios:
            sid, observation = scenario["scenario_id"], scenario["observation"]
            action_id = policy["branches"].get(observation)
            action = actions.get(action_id)
            if action is None:
                if action_id is not None:
                    blockers.append("unknown_action")
                branches[sid] = {"observation": observation, "action": action_id, "total_cost": None, "utility": None}
                continue
            total_cost = round(float(policy["initial_cost"]) + float(action["cost"]), 6)
            if total_cost > rules["max_budget"]: blockers.append("budget")
            gain, risk = map(float, action["values"][sid])
            utility = round(gain - rules["risk_weight"] * risk - rules["cost_weight"] * total_cost, 6)
            branches[sid] = {"observation": observation, "action": action_id, "total_cost": total_cost, "utility": utility}
        rows[policy["policy_id"]] = {"eligible": not blockers, "blockers": sorted(set(blockers)), "branches": branches}
    eligible = {pid: row for pid, row in rows.items() if row["eligible"]}
    scenario_best = {scenario["scenario_id"]: max(row["branches"][scenario["scenario_id"]]["utility"] for row in eligible.values()) for scenario in scenarios}
    for row in rows.values():
        if not row["eligible"]:
            row.update({"max_regret": None, "worst_utility": None, "mean_utility": None})
            for sid, branch in row["branches"].items(): branch["regret"] = None
            continue
        utilities = []
        regrets = []
        for sid, branch in row["branches"].items():
            branch["regret"] = round(scenario_best[sid] - branch["utility"], 6)
            utilities.append(branch["utility"]); regrets.append(branch["regret"])
        row.update({"max_regret": max(regrets), "worst_utility": min(utilities), "mean_utility": round(sum(utilities) / len(utilities), 6)})
    selected = min(eligible, key=lambda pid: (rows[pid]["max_regret"], -rows[pid]["worst_utility"], -rows[pid]["mean_utility"], pid)) if eligible else "human_review"
    hashes = {str(path.relative_to(data)): sha(path) for path in sorted(data.rglob("*.json"))}
    return {"selected_policy": selected, "policies": rows, "scenario_best": scenario_best, "rules_version": rules["rules_version"], "hashes": hashes}

def verify(submission, data, reference):
    exp, errors = expected(data), []
    for name in ("policy.json", "branches.tsv", "audit.md", "manifest.json"):
        if not (submission / name).is_file(): errors.append("missing artifact: " + name)
    if errors: return False, errors
    report = json.loads((submission / "policy.json").read_text())
    for field in ("selected_policy", "rules_version", "claim_boundary", "human_review_required"):
        wanted = exp[field] if field in exp else ("planning_only_not_experimental_proof" if field == "claim_boundary" else True)
        if report.get(field) != wanted: errors.append(field + " mismatch")
    submitted = report.get("policies", {})
    if not isinstance(submitted, dict) or set(submitted) != set(exp["policies"]): errors.append("policy report must cover every policy exactly once")
    for pid, expected_row in exp["policies"].items():
        row = submitted.get(pid, {}) if isinstance(submitted, dict) else {}
        for field in ("eligible", "blockers", "max_regret", "worst_utility", "mean_utility", "branches"):
            if row.get(field) != expected_row[field]: errors.append(f"{pid} {field} mismatch")
    evidence = list(csv.DictReader((submission / "branches.tsv").open(newline=""), delimiter="\t"))
    expected_pairs = {(pid, sid) for pid, row in exp["policies"].items() for sid in row["branches"]}
    if {(row.get("policy_id"), row.get("scenario_id")) for row in evidence} != expected_pairs or len(evidence) != len(expected_pairs): errors.append("branch evidence coverage mismatch")
    for row in evidence:
        branch = exp["policies"].get(row.get("policy_id"), {}).get("branches", {}).get(row.get("scenario_id"), {})
        expected_action = "" if branch.get("action") is None else str(branch.get("action"))
        expected_values = {
            "action": expected_action,
            "observation": str(branch.get("observation")),
            "total_cost": "" if branch.get("total_cost") is None else str(branch.get("total_cost")),
            "utility": "" if branch.get("utility") is None else str(branch.get("utility")),
            "regret": "" if branch.get("regret") is None else str(branch.get("regret")),
            "eligible": str(exp["policies"].get(row.get("policy_id"), {}).get("eligible")).lower(),
            "blockers": ";".join(exp["policies"].get(row.get("policy_id"), {}).get("blockers", [])),
        }
        for field, expected_value in expected_values.items():
            if row.get(field) != expected_value:
                errors.append(f"branch evidence {field} mismatch")
    manifest = json.loads((submission / "manifest.json").read_text())
    if manifest.get("input_sha256") != exp["hashes"] or manifest.get("rules_version") != exp["rules_version"] or manifest.get("deterministic") is not True: errors.append("manifest provenance mismatch")
    audit = (submission / "audit.md").read_text().lower()
    for term in ("minimax regret", "budget", "future outcome", "branch", "human review", "not experimental proof"):
        if term not in audit: errors.append("audit missing " + term)
    return not errors, errors

if __name__ == "__main__":
    p=argparse.ArgumentParser(); p.add_argument("--submission",type=Path,required=True); p.add_argument("--data",type=Path,required=True); p.add_argument("--reference",type=Path,required=True); a=p.parse_args(); ok,errors=verify(a.submission,a.data,a.reference); print(json.dumps({"passed":ok,"errors":errors})); raise SystemExit(0 if ok else 1)
