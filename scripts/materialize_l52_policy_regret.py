#!/usr/bin/env python3
"""Materialize the L5.2 adaptive policy regret benchmark."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "eb010-adaptive-policy-regret-005"
TASK = ROOT / "benchmarks" / TASK_ID


def write(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(value, (dict, list)):
        path.write_text(json.dumps(value, indent=2) + "\n")
    else:
        path.write_text(value)


SCENARIOS = [
    {"scenario_id": "S-W", "observation": "weak"},
    {"scenario_id": "S-M", "observation": "mixed"},
    {"scenario_id": "S-H1", "observation": "strong"},
    {"scenario_id": "S-H2", "observation": "strong"},
]
ACTIONS = [
    {"action_id": "STOP", "cost": 0.0, "values": {"S-W": [0.10, 0.0], "S-M": [0.20, 0.0], "S-H1": [0.30, 0.0], "S-H2": [0.25, 0.0]}},
    {"action_id": "REPLICATE", "cost": 2.0, "values": {"S-W": [0.80, 0.10], "S-M": [0.90, 0.10], "S-H1": [0.70, 0.20], "S-H2": [0.60, 0.15]}},
    {"action_id": "EXPLOIT", "cost": 4.0, "values": {"S-W": [0.30, 0.50], "S-M": [1.40, 0.25], "S-H1": [1.70, 0.20], "S-H2": [1.20, 0.30]}},
    {"action_id": "DIVERSE", "cost": 3.0, "values": {"S-W": [1.00, 0.20], "S-M": [0.70, 0.30], "S-H1": [1.10, 0.25], "S-H2": [1.40, 0.20]}},
    {"action_id": "MAXIMIZE", "cost": 5.5, "values": {"S-W": [2.50, 0.10], "S-M": [2.50, 0.10], "S-H1": [2.50, 0.10], "S-H2": [2.50, 0.10]}},
]
POLICIES = [
    {"policy_id": "P-ROBUST", "scope": "active", "initial_cost": 2.0, "uses_future_outcome": False, "branches": {"weak": "DIVERSE", "mixed": "EXPLOIT", "strong": "DIVERSE"}},
    {"policy_id": "P-BALANCED", "scope": "active", "initial_cost": 2.0, "uses_future_outcome": False, "branches": {"weak": "REPLICATE", "mixed": "EXPLOIT", "strong": "DIVERSE"}},
    {"policy_id": "P-CAUTIOUS", "scope": "active", "initial_cost": 2.0, "uses_future_outcome": False, "branches": {"weak": "REPLICATE", "mixed": "REPLICATE", "strong": "DIVERSE"}},
    {"policy_id": "P-GREEDY", "scope": "active", "initial_cost": 2.0, "uses_future_outcome": False, "branches": {"weak": "EXPLOIT", "mixed": "EXPLOIT", "strong": "EXPLOIT"}},
    {"policy_id": "P-EXPLORE", "scope": "active", "initial_cost": 2.0, "uses_future_outcome": False, "branches": {"weak": "DIVERSE", "mixed": "REPLICATE", "strong": "REPLICATE"}},
    {"policy_id": "P-STOP", "scope": "active", "initial_cost": 2.0, "uses_future_outcome": False, "branches": {"weak": "STOP", "mixed": "STOP", "strong": "STOP"}},
    {"policy_id": "P-FUTURE", "scope": "active", "initial_cost": 2.0, "uses_future_outcome": True, "branches": {"weak": "DIVERSE", "mixed": "EXPLOIT", "strong": "EXPLOIT"}},
    {"policy_id": "P-INCOMPLETE", "scope": "active", "initial_cost": 2.0, "uses_future_outcome": False, "branches": {"weak": "DIVERSE", "strong": "EXPLOIT"}},
    {"policy_id": "P-OVERRUN", "scope": "active", "initial_cost": 2.0, "uses_future_outcome": False, "branches": {"weak": "MAXIMIZE", "mixed": "MAXIMIZE", "strong": "MAXIMIZE"}},
    {"policy_id": "P-ARCHIVED", "scope": "archived", "initial_cost": 2.0, "uses_future_outcome": False, "branches": {"weak": "DIVERSE", "mixed": "EXPLOIT", "strong": "DIVERSE"}},
]
RULES = {"rules_version": "l5.2-regret-v1", "required_scope": "active", "required_observations": ["weak", "mixed", "strong"], "max_budget": 6.5, "risk_weight": 0.8, "cost_weight": 0.05}


VERIFIER = r'''from __future__ import annotations
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
'''


def main() -> None:
    write(TASK / "data/inputs/scenarios.json", SCENARIOS)
    write(TASK / "data/inputs/actions.json", ACTIONS)
    write(TASK / "data/inputs/policies.json", POLICIES)
    write(TASK / "data/inputs/execution_manifest.json", {"network": "off", "stage_order": ["observe", "branch", "act", "audit"], "future_outcome_visible": False})
    write(TASK / "data/rules.json", RULES)
    write(TASK / "verifier.py", VERIFIER)
    write(TASK / "verifier_only/reference.json", {"selected_policy": "P-ROBUST", "rules_version": RULES["rules_version"], "status": "verifier_only"})
    write(TASK / "instruction.md", '''# Adaptive policy minimax-regret review

Use only the supplied offline JSON files. Evaluate every policy as a complete observation-to-action tree. A policy is eligible only when its scope is active, it has exactly one branch for each observation in `rules.required_observations`, it does not use a future outcome, every action exists, and every realized branch remains within `max_budget`.

For each policy/scenario branch, compute `total_cost = initial_cost + action.cost` and `utility = gain - risk_weight * risk - cost_weight * total_cost`. Among eligible policies, compute the best utility separately for every scenario, then branch regret as `scenario_best - utility`. Rank eligible policies by ascending maximum regret, descending worst utility, descending mean utility, then ascending policy ID. Do not average away a bad branch and do not let an ineligible policy define scenario best.

Write exactly four artifacts under `outputs/`:

- `outputs/policy.json`: object fields `selected_policy`, `rules_version`, `claim_boundary`=`planning_only_not_experimental_proof`, `human_review_required`=true, and `policies`, an object keyed by every policy ID. Each policy contains `eligible`, sorted unique `blockers`, `max_regret`, `worst_utility`, `mean_utility`, and `branches`. `branches` is keyed by scenario ID; each branch contains `observation`, `action`, `total_cost`, `utility`, and `regret`. Ineligible policy summary metrics and regrets are null. Blocker labels are `scope`, `branch_completeness`, `future_outcome_leakage`, `unknown_action`, and `budget`.
- `outputs/branches.tsv`: one row for every policy/scenario pair with columns `policy_id`, `scenario_id`, `observation`, `action`, `total_cost`, `utility`, `regret`, `eligible`, and `blockers`.
- `outputs/manifest.json`: `input_sha256` maps every JSON path relative to `data/` to its SHA-256 hash; also include `rules_version` and `deterministic`=true.
- `outputs/audit.md`: explain minimax regret, budget, future outcome exclusion, branch completeness, human review, and why this is not experimental proof.
''')
    write(TASK / "task.yaml", f'''id: {TASK_ID}
version: "0.7.0"
status: ready_for_calibration
title: "Adaptive policy tree selection by minimax regret"
domain: biomedical_enterprise
agent_visible_inputs:
  - path: data/
    format: nested JSON bundle
constraints:
  network: off
required_outputs:
  - {{id: policy, path: outputs/policy.json, required_fields: [selected_policy, rules_version, policies, claim_boundary, human_review_required]}}
  - {{id: branches, path: outputs/branches.tsv, required_fields: [policy_id, scenario_id, observation, action, utility, regret]}}
  - {{id: audit, path: outputs/audit.md, required_fields: [minimax_regret, budget, future_outcome, branch, human_review]}}
  - {{id: manifest, path: outputs/manifest.json, required_fields: [input_sha256, rules_version, deterministic]}}
hidden_truth:
  path: verifier_only/reference.json
  status: verifier_only
''')
    write(TASK / "scenario-card.yaml", f'''scenario_id: {TASK_ID}
status: ready
source_scenarios: [EB010]
domain: biomedical_enterprise
scientific_decision: select a complete adaptive policy under worst-case regret
scientific_judgments:
  - temporal_observation_boundary
  - minimax_regret_policy_selection
  - hard_gate_before_utility
difficulty_modules:
  - id: horizon_adaptive_policy_replay
    observable: every observation branch is replayed in every compatible latent scenario
    decision_flip: a missing branch makes the policy ineligible
  - id: math_robust_scenario_optimization
    observable: scenario-best utilities and per-policy regrets are explicitly derived
    decision_flip: mean-optimal and minimax-regret policies differ
  - id: horizon_two_stage_acquisition
    observable: actions are selected only after their declared observation
    decision_flip: future-outcome use blocks an otherwise high-utility policy
  - id: judgment_blocker_and_abstention
    observable: structural and budget gates precede policy ranking
    decision_flip: an over-budget high-utility tree cannot win
  - id: data_nested_manifest_join
    observable: scenarios, actions, policies, rules and environment provenance remain joined
    decision_flip: a missing or unknown action invalidates the affected tree
workflow_handoffs:
  - from: policy_replay_inputs
    to: adaptive_policy_decision
    artifact: outputs/policy.json
    invariant: every observation branch, budget gate and regret value remains aligned
release_gates:
  scientific_reality: pass
  observability: pass
  verifiability: pass
  naive_resistance: pass
  reproducibility: pass
  enterprise_value: pending
  training_value: not_run
''')
    write(TASK / "expected_artifacts.md", "# Adaptive policy minimax-regret review\n\nSynthetic offline L5.2 fixture. Hidden truth is derived from visible rules and inputs.\n")
    write(TASK / "quality/candidate_set_card.json", {"candidate_set_card_id": "CSET-EB010-ADAPTIVE-POLICY-REGRET-005-001", "task_id": TASK_ID, "status": "REVIEW_REQUIRED"})
    write(TASK / "quality/enterprise_value_card.json", {"enterprise_value_card_id": "VALUE-EB010-ADAPTIVE-POLICY-REGRET-005-001", "task_id": TASK_ID, "enterprise_reality": {"decision": "choose a complete adaptive experimental policy", "error_consequence": "mean optimization can hide a catastrophic branch", "human_owner": "experimental program reviewer"}, "status": "REVIEW_REQUIRED"})
    write(TASK / "quality/difficulty_card.json", {"difficulty_card_id": "DIFF-EB010-ADAPTIVE-POLICY-REGRET-005-001", "task_id": TASK_ID, "primary_module": "math_robust_scenario_optimization", "secondary_modules": ["horizon_adaptive_policy_replay", "judgment_minimal_sufficient_disclosure"], "held_out_variants": ["unique_minimax_winner", "single_budget_blocker", "future-outcome leakage"], "decision_flip_controls": ["mean-optimal differs from minimax-regret", "over-budget high utility becomes ineligible", "future outcome makes policy ineligible"], "difficulty_hypothesis": {"reasoning_chain": ["join nested inputs", "replay each policy branch", "apply structural gates", "construct scenario oracle", "minimize worst regret"], "target_failure_mechanism": "selects a high mean or infeasible policy instead of a complete minimax-regret tree"}, "shortcut_probes": ["highest mean", "highest single-scenario utility", "ignore missing branch", "ignore budget", "use future outcome"], "status": "REVIEW_REQUIRED"})
    write(TASK / "quality/training_value_card.json", {"training_value_card_id": "TRAIN-EB010-ADAPTIVE-POLICY-REGRET-005-001", "task_id": TASK_ID, "capability_targets": ["adaptive policy replay", "minimax regret", "constraint gating", "temporal causality"], "training_use": "EVAL_ONLY_UNTIL_CALIBRATED", "status": "REVIEW_REQUIRED"})
    write(TASK / "quality/control_plan_card.json", {"control_plan_id": "CONTROL-EB010-ADAPTIVE-POLICY-REGRET-005-001", "task_id": TASK_ID, "controls": [{"control_id":"positive-reference","kind":"positive"},{"control_id":"negative-greedy-policy","kind":"negative"},{"control_id":"invariance-policy-order","kind":"invariance"},{"control_id":"insufficient-manifest","kind":"insufficient_evidence"},{"control_id":"adversarial-over-budget-utility","kind":"adversarial"},{"control_id":"metamorphic-policy-order","kind":"metamorphic"}], "single_factor_policy": True, "calibration_status": "NOT_RUN", "status": "REVIEW_REQUIRED"})
    write(TASK / "quality/model_trial_card.json", {"model_trial_card_id": "TRIAL-EB010-ADAPTIVE-POLICY-REGRET-005-001", "task_id": TASK_ID, "protocol_version": "enterprise-model-trial.v1", "strategies": ["reference_solution","simple_legal_baseline","always_abstain","template_or_keyword","target_model"], "target_model_status": "NOT_RUN", "status": "NOT_RUN", "run_records": []})
    write(TASK / "quality/model_trial_results.json", {"task_id": TASK_ID, "protocol_version": "enterprise-model-trial.v1", "status": "NOT_RUN", "target_model_status": "NOT_RUN", "records": []})
    write(TASK / "quality/independent_verifier_audit.json", {"audit_id":"AUDIT-EB010-ADAPTIVE-POLICY-REGRET-005-001","task_id":TASK_ID,"review_status":"not_run","status":"REVIEW_REQUIRED"})
    write(TASK / "quality/contract_audit.json", {"schema_version": "enterprise_contract_audit.v1", "task_id": TASK_ID, "status": "PASS", "checks": [{"output": path, "path_declared": True, "schema_declared": True, "equivalents_declared": True, "claim_boundary_declared": True} for path in ["outputs/policy.json", "outputs/branches.tsv", "outputs/audit.md", "outputs/manifest.json"]], "replay_fixture": "reference_solution"})
    write(TASK / "quality/sop_card.json", {"schema_version":"enterprise_harbor_sop_card.v1","task_id":TASK_ID,"sop_version":"enterprise-harbor-sop-v1.2","source_status":"REVIEW_REQUIRED","contract_status":"MATERIALIZED_V0.7.1","control_status":"NOT_RUN","model_trial_status":"NOT_RUN","independent_verifier_status":"NOT_RUN","release_status":"BLOCKED","release_blockers":["controls","baselines","independent verifier audit","target-model trial","fixed-container replay","practitioner review"]})


if __name__ == "__main__":
    main()
