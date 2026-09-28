#!/usr/bin/env python3
"""Materialize the L5.3 distributionally robust adaptive-policy benchmark."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "eb010-distributional-policy-stress-006"
TASK = ROOT / "benchmarks" / TASK_ID


def write(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(value, indent=2) + "\n" if isinstance(value, (dict, list)) else value
    path.write_text(text, encoding="utf-8")


SCENARIOS = [
    {"scenario_id": "S-W-A", "observation": "weak", "site": "A"},
    {"scenario_id": "S-W-B", "observation": "weak", "site": "B"},
    {"scenario_id": "S-M-A", "observation": "mixed", "site": "A"},
    {"scenario_id": "S-M-B", "observation": "mixed", "site": "B"},
    {"scenario_id": "S-S-A", "observation": "strong", "site": "A"},
    {"scenario_id": "S-S-B", "observation": "strong", "site": "B"},
]

ACTIONS = [
    {"action_id": "STOP", "cost": 0.0, "net_utility": {"S-W-A": 0.10, "S-W-B": 0.10, "S-M-A": 0.20, "S-M-B": 0.20, "S-S-A": 0.30, "S-S-B": 0.25}},
    {"action_id": "CONFIRM", "cost": 2.0, "net_utility": {"S-W-A": 0.80, "S-W-B": 0.70, "S-M-A": 0.90, "S-M-B": 0.75, "S-S-A": 0.65, "S-S-B": 0.60}},
    {"action_id": "EXPLOIT", "cost": 4.0, "net_utility": {"S-W-A": 0.10, "S-W-B": 0.00, "S-M-A": 1.60, "S-M-B": 1.20, "S-S-A": 1.90, "S-S-B": 1.40}},
    {"action_id": "DIVERSIFY", "cost": 3.0, "net_utility": {"S-W-A": 1.20, "S-W-B": 1.00, "S-M-A": 0.80, "S-M-B": 1.10, "S-S-A": 1.00, "S-S-B": 1.50}},
    {"action_id": "HEDGE", "cost": 3.5, "net_utility": {"S-W-A": 0.95, "S-W-B": 0.95, "S-M-A": 1.00, "S-M-B": 1.00, "S-S-A": 1.05, "S-S-B": 1.05}},
    {"action_id": "MAXIMIZE", "cost": 6.0, "net_utility": {"S-W-A": 2.50, "S-W-B": 2.50, "S-M-A": 2.50, "S-M-B": 2.50, "S-S-A": 2.50, "S-S-B": 2.50}},
]

POLICIES = [
    {"policy_id": "P-ADAPT", "scope": "active", "initial_cost": 2.0, "uses_future_outcome": False, "branches": {"weak": "DIVERSIFY", "mixed": "HEDGE", "strong": "EXPLOIT"}},
    {"policy_id": "P-NOMINAL", "scope": "active", "initial_cost": 2.0, "uses_future_outcome": False, "branches": {"weak": "CONFIRM", "mixed": "EXPLOIT", "strong": "EXPLOIT"}},
    {"policy_id": "P-BALANCED", "scope": "active", "initial_cost": 2.0, "uses_future_outcome": False, "branches": {"weak": "HEDGE", "mixed": "HEDGE", "strong": "DIVERSIFY"}},
    {"policy_id": "P-HEDGE", "scope": "active", "initial_cost": 2.0, "uses_future_outcome": False, "branches": {"weak": "HEDGE", "mixed": "HEDGE", "strong": "HEDGE"}},
    {"policy_id": "P-DIVERSE", "scope": "active", "initial_cost": 2.0, "uses_future_outcome": False, "branches": {"weak": "DIVERSIFY", "mixed": "DIVERSIFY", "strong": "DIVERSIFY"}},
    {"policy_id": "P-CONFIRM", "scope": "active", "initial_cost": 2.0, "uses_future_outcome": False, "branches": {"weak": "CONFIRM", "mixed": "CONFIRM", "strong": "CONFIRM"}},
    {"policy_id": "P-STOP", "scope": "active", "initial_cost": 2.0, "uses_future_outcome": False, "branches": {"weak": "STOP", "mixed": "STOP", "strong": "STOP"}},
    {"policy_id": "P-FUTURE", "scope": "active", "initial_cost": 2.0, "uses_future_outcome": True, "branches": {"weak": "DIVERSIFY", "mixed": "EXPLOIT", "strong": "EXPLOIT"}},
    {"policy_id": "P-INCOMPLETE", "scope": "active", "initial_cost": 2.0, "uses_future_outcome": False, "branches": {"weak": "DIVERSIFY", "strong": "EXPLOIT"}},
    {"policy_id": "P-OVERRUN", "scope": "active", "initial_cost": 2.0, "uses_future_outcome": False, "branches": {"weak": "MAXIMIZE", "mixed": "MAXIMIZE", "strong": "MAXIMIZE"}},
    {"policy_id": "P-ARCHIVED", "scope": "archived", "initial_cost": 2.0, "uses_future_outcome": False, "branches": {"weak": "DIVERSIFY", "mixed": "HEDGE", "strong": "EXPLOIT"}},
    {"policy_id": "P-UNKNOWN", "scope": "active", "initial_cost": 2.0, "uses_future_outcome": False, "branches": {"weak": "DIVERSIFY", "mixed": "UNLISTED", "strong": "EXPLOIT"}},
]

PROFILES = {
    "nominal": {"S-W-A": 1/6, "S-W-B": 1/6, "S-M-A": 1/6, "S-M-B": 1/6, "S-S-A": 1/6, "S-S-B": 1/6},
    "weak_shift": {"S-W-A": 0.35, "S-W-B": 0.25, "S-M-A": 0.10, "S-M-B": 0.10, "S-S-A": 0.10, "S-S-B": 0.10},
    "mixed_shift": {"S-W-A": 0.10, "S-W-B": 0.10, "S-M-A": 0.30, "S-M-B": 0.20, "S-S-A": 0.15, "S-S-B": 0.15},
    "strong_shift": {"S-W-A": 0.10, "S-W-B": 0.10, "S-M-A": 0.10, "S-M-B": 0.10, "S-S-A": 0.25, "S-S-B": 0.35},
    "site_b_shift": {"S-W-A": 0.00, "S-W-B": 0.30, "S-M-A": 0.00, "S-M-B": 0.30, "S-S-A": 0.00, "S-S-B": 0.40},
}

RULES = {
    "rules_version": "l5.3-distributional-stress-v1",
    "required_scope": "active",
    "required_observations": ["weak", "mixed", "strong"],
    "max_budget": 7.0,
    "cvar_alpha": 0.4,
    "nominal_profile": "nominal",
    "weight_profiles": PROFILES,
}


VERIFIER = r'''from __future__ import annotations
import argparse, csv, hashlib, json
from decimal import Decimal, InvalidOperation
from pathlib import Path

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def r6(value): return round(float(value) + 0.0, 6)

def lower_tail_cvar(utilities, weights, alpha):
    remaining, total = alpha, 0.0
    for sid, utility in sorted(utilities.items(), key=lambda item: (item[1], item[0])):
        take = min(weights[sid], remaining)
        total += take * utility
        remaining -= take
        if remaining <= 1e-12: break
    if remaining > 1e-9: raise ValueError("weight profile has insufficient mass")
    return r6(total / alpha)

def expected(data):
    rules=json.loads((data/"rules.json").read_text()); scenarios=json.loads((data/"inputs/scenarios.json").read_text())
    actions={row["action_id"]:row for row in json.loads((data/"inputs/actions.json").read_text())}; policies=json.loads((data/"inputs/policies.json").read_text())
    profiles=rules["weight_profiles"]; scenario_ids={row["scenario_id"] for row in scenarios}
    for name,weights in profiles.items():
        if set(weights)!=scenario_ids or abs(sum(weights.values())-1.0)>1e-9: raise ValueError("invalid weight profile: "+name)
    required=set(rules["required_observations"]); rows={}
    for policy in policies:
        blockers=[]
        if policy["scope"]!=rules["required_scope"]: blockers.append("scope")
        if set(policy["branches"])!=required: blockers.append("branch_completeness")
        if policy["uses_future_outcome"]: blockers.append("future_outcome_leakage")
        branches={}
        for scenario in scenarios:
            sid,observation=scenario["scenario_id"],scenario["observation"]; action_id=policy["branches"].get(observation); action=actions.get(action_id)
            if action is None:
                if action_id is not None: blockers.append("unknown_action")
                branches[sid]={"observation":observation,"site":scenario["site"],"action":action_id,"total_cost":None,"utility":None}
                continue
            total_cost=r6(policy["initial_cost"]+action["cost"])
            if total_cost>rules["max_budget"]: blockers.append("budget")
            branches[sid]={"observation":observation,"site":scenario["site"],"action":action_id,"total_cost":total_cost,"utility":r6(action["net_utility"][sid])}
        rows[policy["policy_id"]]={"eligible":not blockers,"blockers":sorted(set(blockers)),"branches":branches,"profiles":{}}
    eligible={pid:row for pid,row in rows.items() if row["eligible"]}
    for row in eligible.values():
        utilities={sid:branch["utility"] for sid,branch in row["branches"].items()}
        for name,weights in profiles.items():
            row["profiles"][name]={"expected_utility":r6(sum(weights[sid]*utilities[sid] for sid in weights)),"lower_tail_cvar":lower_tail_cvar(utilities,weights,rules["cvar_alpha"])}
    profile_best={name:max(row["profiles"][name]["expected_utility"] for row in eligible.values()) for name in profiles}
    profile_winners={name:min(pid for pid,row in eligible.items() if row["profiles"][name]["expected_utility"]==profile_best[name]) for name in profiles}
    for row in rows.values():
        if not row["eligible"]:
            row.update({"robust_cvar":None,"max_profile_regret":None,"nominal_expected_utility":None})
            continue
        regrets=[]
        for name,metrics in row["profiles"].items():
            metrics["regret"]=r6(profile_best[name]-metrics["expected_utility"]); regrets.append(metrics["regret"])
        row.update({"robust_cvar":min(item["lower_tail_cvar"] for item in row["profiles"].values()),"max_profile_regret":max(regrets),"nominal_expected_utility":row["profiles"][rules["nominal_profile"]]["expected_utility"]})
    def choose(profile_names):
        return min(eligible,key=lambda pid:(-min(rows[pid]["profiles"][name]["lower_tail_cvar"] for name in profile_names),rows[pid]["max_profile_regret"],-rows[pid]["nominal_expected_utility"],pid))
    selected=choose(list(profiles)); leave_one_out={name:choose([other for other in profiles if other!=name]) for name in profiles}
    hashes={str(path.relative_to(data)):sha(path) for path in sorted(data.rglob("*.json"))}
    return {"selected_policy":selected,"policies":rows,"profile_best_expected":profile_best,"profile_winners":profile_winners,"leave_one_profile_out_winners":leave_one_out,"rules_version":rules["rules_version"],"hashes":hashes}

def numeric_match(actual,wanted):
    if actual is None or wanted is None: return actual is None and wanted is None
    try: return abs(Decimal(str(actual))-Decimal(str(wanted)))<=Decimal("0.000001")
    except (InvalidOperation,TypeError,ValueError): return False

def numeric_map_match(actual,wanted):
    return isinstance(actual,dict) and set(actual)==set(wanted) and all(numeric_match(actual[key],value) for key,value in wanted.items())

def normalize_branches(actual,scenario_ids):
    if isinstance(actual,dict): return actual
    if isinstance(actual,list) and len(actual)==len(scenario_ids): return dict(zip(scenario_ids,actual))
    return {}

def verify(submission,data,reference):
    exp,errors=expected(data),[]
    for name in ("policy.json","branches.tsv","profiles.tsv","audit.md","manifest.json"):
        if not (submission/name).is_file(): errors.append("missing artifact: "+name)
    if errors:return False,errors
    report=json.loads((submission/"policy.json").read_text())
    fixed={"selected_policy":exp["selected_policy"],"rules_version":exp["rules_version"],"claim_boundary":"planning_only_not_experimental_proof","human_review_required":True,"profile_winners":exp["profile_winners"],"leave_one_profile_out_winners":exp["leave_one_profile_out_winners"]}
    for field,wanted in fixed.items():
        if report.get(field)!=wanted: errors.append(field+" mismatch")
    if not numeric_map_match(report.get("profile_best_expected"),exp["profile_best_expected"]): errors.append("profile_best_expected mismatch")
    submitted=report.get("policies",{})
    if not isinstance(submitted,dict) or set(submitted)!=set(exp["policies"]): errors.append("policy report must cover every policy exactly once")
    for pid,wanted in exp["policies"].items():
        row=submitted.get(pid,{}) if isinstance(submitted,dict) else {}
        for field in ("eligible","blockers"):
            if row.get(field)!=wanted[field]: errors.append(f"{pid} {field} mismatch")
        for field in ("robust_cvar","max_profile_regret","nominal_expected_utility"):
            if not numeric_match(row.get(field),wanted[field]): errors.append(f"{pid} {field} mismatch")
        branches=normalize_branches(row.get("branches"),list(wanted["branches"]))
        if set(branches)!=set(wanted["branches"]): errors.append(f"{pid} branches mismatch")
        else:
            for sid,expected_branch in wanted["branches"].items():
                branch=branches[sid]
                if not isinstance(branch,dict) or any(branch.get(field)!=expected_branch[field] for field in ("observation","site","action")) or any(not numeric_match(branch.get(field),expected_branch[field]) for field in ("total_cost","utility")): errors.append(f"{pid} branches mismatch")
        profiles=row.get("profiles")
        if not isinstance(profiles,dict) or set(profiles)!=set(wanted["profiles"]): errors.append(f"{pid} profiles mismatch")
        else:
            for name,expected_metrics in wanted["profiles"].items():
                if not numeric_map_match(profiles.get(name),expected_metrics): errors.append(f"{pid} profiles mismatch")
    branch_rows=list(csv.DictReader((submission/"branches.tsv").open(newline=""),delimiter="\t")); expected_pairs={(pid,sid) for pid,row in exp["policies"].items() for sid in row["branches"]}
    if len(branch_rows)!=len(expected_pairs) or {(row.get("policy_id"),row.get("scenario_id")) for row in branch_rows}!=expected_pairs: errors.append("branch evidence coverage mismatch")
    for row in branch_rows:
        policy=exp["policies"].get(row.get("policy_id"),{}); branch=policy.get("branches",{}).get(row.get("scenario_id"),{})
        values={"observation":branch.get("observation"),"site":branch.get("site"),"action":"" if branch.get("action") is None else str(branch.get("action")),"eligible":str(policy.get("eligible")).lower(),"blockers":";".join(policy.get("blockers",[]))}
        for field,wanted in values.items():
            if row.get(field)!=wanted: errors.append("branch evidence "+field+" mismatch")
        for field in ("total_cost","utility"):
            actual=row.get(field); wanted=branch.get(field)
            if (wanted is None and actual!="") or (wanted is not None and not numeric_match(actual,wanted)): errors.append("branch evidence "+field+" mismatch")
    profile_rows=list(csv.DictReader((submission/"profiles.tsv").open(newline=""),delimiter="\t")); expected_profile_pairs={(pid,name) for pid,row in exp["policies"].items() if row["eligible"] for name in row["profiles"]}
    if len(profile_rows)!=len(expected_profile_pairs) or {(row.get("policy_id"),row.get("profile")) for row in profile_rows}!=expected_profile_pairs: errors.append("profile evidence coverage mismatch")
    for row in profile_rows:
        metrics=exp["policies"].get(row.get("policy_id"),{}).get("profiles",{}).get(row.get("profile"),{})
        for field in ("expected_utility","lower_tail_cvar","regret"):
            if not numeric_match(row.get(field),metrics.get(field)): errors.append("profile evidence "+field+" mismatch")
    manifest=json.loads((submission/"manifest.json").read_text())
    if manifest.get("input_sha256")!=exp["hashes"] or manifest.get("rules_version")!=exp["rules_version"] or manifest.get("deterministic") is not True: errors.append("manifest provenance mismatch")
    audit=(submission/"audit.md").read_text().lower().replace("-"," ")
    for term in ("distribution shift","lower tail cvar","profile regret","leave one profile out","future outcome","budget","human review","not experimental proof"):
        if term not in audit: errors.append("audit missing "+term)
    return not errors,errors

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--submission",type=Path,required=True);p.add_argument("--data",type=Path,required=True);p.add_argument("--reference",type=Path,required=True);a=p.parse_args();ok,errors=verify(a.submission,a.data,a.reference);print(json.dumps({"passed":ok,"errors":errors}));raise SystemExit(0 if ok else 1)
'''


def main() -> None:
    write(TASK / "data/inputs/scenarios.json", SCENARIOS)
    write(TASK / "data/inputs/actions.json", ACTIONS)
    write(TASK / "data/inputs/policies.json", POLICIES)
    write(TASK / "data/inputs/execution_manifest.json", {"network": "off", "stage_order": ["observe", "branch", "stress", "select", "audit"], "future_outcome_visible": False})
    write(TASK / "data/rules.json", RULES)
    write(TASK / "verifier.py", VERIFIER)
    write(TASK / "verifier_only/reference.json", {"selected_policy": "P-ADAPT", "rules_version": RULES["rules_version"], "status": "verifier_only"})
    write(TASK / "instruction.md", '''# Distributionally robust adaptive-policy stress test

Use only the supplied offline JSON files. First apply hard eligibility gates: active scope, exactly one branch for every required observation, no future-outcome use, known actions, and every realized branch within budget. Ineligible policies cannot define a profile optimum.

For every eligible policy and weight profile, compute expected utility. Compute lower-tail CVaR at `cvar_alpha` by sorting scenario utilities ascending (scenario ID breaks exact utility ties), consuming profile probability mass until alpha, allowing a fractional final scenario, and dividing the accumulated weighted utility by alpha. For each profile, compute the best expected utility and every policy's regret from that best. A policy's robust CVaR is its minimum CVaR across profiles; its maximum profile regret is its largest profile regret.

Select by descending robust CVaR, ascending maximum profile regret, descending nominal expected utility, then ascending policy ID. Recompute the selection after leaving out each one weight profile; this is a stability report, not an eligibility gate.

Round every reported computed numeric value to six decimal places. JSON numeric values and TSV numeric cells are compared numerically, so trailing zeroes are optional.

Write exactly five artifacts under `outputs/`:

- `outputs/policy.json`: `selected_policy`, `rules_version`, `claim_boundary`=`planning_only_not_experimental_proof`, `human_review_required`=true, `profile_best_expected`, `profile_winners`, `leave_one_profile_out_winners`, and `policies` keyed by every policy ID. Each policy contains `eligible`, sorted unique `blockers`, `robust_cvar`, `max_profile_regret`, `nominal_expected_utility`, `branches`, and `profiles`. `branches` is an object keyed by scenario ID; each branch contains `observation`, `site`, `action`, `total_cost`, `utility`. `profiles` is an object keyed by profile name; each eligible profile contains `expected_utility`, `lower_tail_cvar`, `regret`. Ineligible policies use an empty profile object and null summary metrics. Blocker labels: `scope`, `branch_completeness`, `future_outcome_leakage`, `unknown_action`, `budget`.
- `outputs/branches.tsv`: every policy/scenario pair with columns `policy_id`, `scenario_id`, `observation`, `site`, `action`, `total_cost`, `utility`, `eligible`, `blockers`.
- `outputs/profiles.tsv`: every eligible policy/profile pair with columns `policy_id`, `profile`, `expected_utility`, `lower_tail_cvar`, `regret`.
- `outputs/manifest.json`: `input_sha256` maps every JSON path relative to `data/` to SHA-256; include `rules_version`, `deterministic`=true.
- `outputs/audit.md`: explain distribution shift, lower-tail CVaR, profile regret, leave-one-profile-out, future outcome and budget gates, human review, and why this is not experimental proof.
''')
    write(TASK / "task.yaml", f'''id: {TASK_ID}
version: "0.8.1"
status: ready_for_calibration
title: "Distributionally robust adaptive-policy stress test"
domain: biomedical_enterprise
agent_visible_inputs:
  - path: data/
    format: nested JSON bundle
constraints:
  network: off
required_outputs:
  - {{id: policy, path: outputs/policy.json, required_fields: [selected_policy, rules_version, policies, profile_best_expected, leave_one_profile_out_winners]}}
  - {{id: branches, path: outputs/branches.tsv, required_fields: [policy_id, scenario_id, observation, action, utility]}}
  - {{id: profiles, path: outputs/profiles.tsv, required_fields: [policy_id, profile, expected_utility, lower_tail_cvar, regret]}}
  - {{id: audit, path: outputs/audit.md, required_fields: [distribution_shift, lower_tail_cvar, profile_regret, human_review]}}
  - {{id: manifest, path: outputs/manifest.json, required_fields: [input_sha256, rules_version, deterministic]}}
hidden_truth:
  path: verifier_only/reference.json
  status: verifier_only
''')
    write(TASK / "scenario-card.yaml", f'''scenario_id: {TASK_ID}
status: ready
source_scenarios: [EB010]
domain: biomedical_enterprise
scientific_decision: select an adaptive policy robust to declared distribution shifts
scientific_judgments:
  - distribution_shift_boundary
  - lower_tail_risk_selection
  - temporal_hard_gate_before_optimization
difficulty_modules:
  - id: math_robust_scenario_optimization
    observable: expected utility, lower-tail CVaR and profile regret are recomputed for five distributions
    decision_flip: the nominal expected-utility winner is not the robust winner
  - id: math_sensitivity_frontier
    observable: leave-one-profile-out winners are reported for every ambiguity-set member
    decision_flip: removing a binding shift profile can change the selected policy
  - id: horizon_adaptive_policy_replay
    observable: all observation-conditioned branches are evaluated across six latent scenarios
    decision_flip: a missing branch makes the full policy ineligible
  - id: judgment_blocker_and_abstention
    observable: temporal, scope, action and budget gates precede every distributional score
    decision_flip: an apparently dominant but invalid policy cannot define the optimum
  - id: data_nested_manifest_join
    observable: scenarios, actions, policies, profiles and hashes remain joined across outputs
    decision_flip: a cross-artifact mismatch fails verification
workflow_handoffs:
  - from: adaptive_policy_inputs
    to: distributional_stress_decision
    artifact: outputs/policy.json
    invariant: hard gates, profile metrics and sensitivity winners remain aligned
release_gates:
  scientific_reality: pass
  observability: pass
  verifiability: pass
  naive_resistance: pass
  reproducibility: pass
  enterprise_value: pending
  training_value: not_run
''')
    write(TASK / "expected_artifacts.md", "# Distributionally robust policy stress test\n\nSynthetic offline L5.3 fixture. Hidden truth is fully derived from visible rules and inputs.\n")
    write(TASK / "quality/candidate_set_card.json", {"candidate_set_card_id": "CSET-EB010-DISTRIBUTIONAL-POLICY-STRESS-006-001", "task_id": TASK_ID, "status": "REVIEW_REQUIRED"})
    write(TASK / "quality/enterprise_value_card.json", {"enterprise_value_card_id": "VALUE-EB010-DISTRIBUTIONAL-POLICY-STRESS-006-001", "task_id": TASK_ID, "enterprise_reality": {"decision": "choose an adaptive experimental policy robust to plausible cohort shift", "error_consequence": "nominal optimization can select a policy with poor shifted-cohort tail behavior", "human_owner": "experimental program reviewer"}, "status": "REVIEW_REQUIRED"})
    write(TASK / "quality/difficulty_card.json", {"difficulty_card_id": "DIFF-EB010-DISTRIBUTIONAL-POLICY-STRESS-006-001", "task_id": TASK_ID, "primary_module": "math_robust_scenario_optimization", "secondary_modules": ["math_sensitivity_frontier", "horizon_adaptive_policy_replay"], "held_out_variants": ["nominal-versus-tail winner", "shift-profile stability", "future-outcome decoy"], "decision_flip_controls": ["nominal winner differs from robust winner", "leave-one-profile-out confirms the robust winner", "over-budget utility cannot define profile best"], "difficulty_hypothesis": {"reasoning_chain": ["join five inputs", "replay 72 branches", "apply hard gates", "integrate five distributions", "compute fractional lower-tail CVaR", "construct profile regrets", "repeat leave-one-profile-out selection"], "target_failure_mechanism": "optimizes the nominal mean or computes unweighted tail risk instead of distribution-specific CVaR"}, "shortcut_probes": ["nominal mean only", "unweighted worst scenarios", "ineligible policy in profile best", "omit sensitivity replay"], "status": "REVIEW_REQUIRED"})
    write(TASK / "quality/training_value_card.json", {"training_value_card_id": "TRAIN-EB010-DISTRIBUTIONAL-POLICY-STRESS-006-001", "task_id": TASK_ID, "capability_targets": ["distributionally robust optimization", "weighted lower-tail CVaR", "adaptive policy replay", "sensitivity analysis"], "training_use": "EVAL_ONLY_UNTIL_CALIBRATED", "status": "REVIEW_REQUIRED"})
    write(TASK / "quality/control_plan_card.json", {"control_plan_id": "CONTROL-EB010-DISTRIBUTIONAL-POLICY-STRESS-006-001", "task_id": TASK_ID, "controls": [{"control_id":"positive-reference","kind":"positive"},{"control_id":"negative-nominal-winner","kind":"negative"},{"control_id":"invariance-row-order","kind":"invariance"},{"control_id":"insufficient-manifest","kind":"insufficient_evidence"},{"control_id":"adversarial-over-budget","kind":"adversarial"},{"control_id":"metamorphic-profile-order","kind":"metamorphic"}], "single_factor_policy": True, "calibration_status": "NOT_RUN", "status": "REVIEW_REQUIRED"})
    write(TASK / "quality/model_trial_card.json", {"model_trial_card_id": "TRIAL-EB010-DISTRIBUTIONAL-POLICY-STRESS-006-001", "task_id": TASK_ID, "protocol_version": "enterprise-model-trial.v1", "strategies": ["reference_solution","simple_legal_baseline","always_abstain","template_or_keyword","target_model"], "target_model_status": "NOT_RUN", "status": "NOT_RUN", "run_records": []})
    write(TASK / "quality/model_trial_results.json", {"task_id": TASK_ID, "protocol_version": "enterprise-model-trial.v1", "status": "NOT_RUN", "target_model_status": "NOT_RUN", "records": []})
    write(TASK / "quality/independent_verifier_audit.json", {"audit_id":"AUDIT-EB010-DISTRIBUTIONAL-POLICY-STRESS-006-001","task_id":TASK_ID,"review_status":"not_run","status":"REVIEW_REQUIRED"})
    write(TASK / "quality/contract_audit.json", {"schema_version": "enterprise_contract_audit.v1", "task_id": TASK_ID, "status": "PASS", "checks": [{"output": path, "path_declared": True, "schema_declared": True, "equivalents_declared": True, "claim_boundary_declared": True} for path in ["outputs/policy.json", "outputs/branches.tsv", "outputs/profiles.tsv", "outputs/audit.md", "outputs/manifest.json"]], "replay_fixture": "reference_solution"})
    write(TASK / "quality/sop_card.json", {"schema_version":"enterprise_harbor_sop_card.v1","task_id":TASK_ID,"sop_version":"enterprise-harbor-sop-v1.2","source_status":"REVIEW_REQUIRED","contract_status":"MATERIALIZED_V0.8.1","control_status":"NOT_RUN","model_trial_status":"NOT_RUN","independent_verifier_status":"NOT_RUN","release_status":"BLOCKED","release_blockers":["controls","baselines","independent verifier audit","target-model trial","fixed-container replay","practitioner review"]})
    write(TASK / "tests/test_verifier.py", '''import csv, importlib.util, json, runpy\nfrom pathlib import Path\nROOT=Path(__file__).resolve().parents[1]\nspec=importlib.util.spec_from_file_location("verifier",ROOT/"verifier.py"); verifier=importlib.util.module_from_spec(spec); assert spec and spec.loader; spec.loader.exec_module(verifier)\n\ndef test_oracle_is_distributionally_robust():\n    exp=verifier.expected(ROOT/"data")\n    assert exp["selected_policy"]=="P-ADAPT"\n    assert exp["profile_winners"]["nominal"]=="P-NOMINAL"\n    assert set(exp["leave_one_profile_out_winners"].values())=={"P-ADAPT"}\n    assert exp["policies"]["P-OVERRUN"]["blockers"]==["budget"]\n    assert exp["policies"]["P-INCOMPLETE"]["blockers"]==["branch_completeness"]\n\ndef test_reference_declares_current_oracle():\n    exp=verifier.expected(ROOT/"data"); ref=json.loads((ROOT/"verifier_only/reference.json").read_text())\n    assert ref["selected_policy"]==exp["selected_policy"]\n\ndef test_equivalent_numeric_and_branch_representations_are_accepted(tmp_path):\n    helpers=runpy.run_path(str(ROOT.parents[1]/"scripts/run_l53_distributional_stress_calibration.py"))\n    out=tmp_path/"outputs"; helpers["write_reference"](verifier,out,ROOT/"data")\n    report=json.loads((out/"policy.json").read_text())\n    for policy in report["policies"].values(): policy["branches"]=list(policy["branches"].values())\n    report["profile_best_expected"]["nominal"] += 1e-10\n    (out/"policy.json").write_text(json.dumps(report))\n    rows=list(csv.DictReader((out/"branches.tsv").open(newline=""),delimiter="\\t"))\n    with (out/"branches.tsv").open("w",newline="") as handle:\n        writer=csv.DictWriter(handle,fieldnames=list(rows[0]),delimiter="\\t"); writer.writeheader()\n        for row in rows:\n            for field in ("total_cost","utility"):\n                if row[field]: row[field]=str(float(row[field]))\n            writer.writerow(row)\n    (out/"audit.md").write_text((out/"audit.md").read_text().replace("Future outcome","Future-outcome"))\n    passed,errors=verifier.verify(out,ROOT/"data",ROOT/"verifier_only/reference.json")\n    assert passed,errors\n''')


if __name__ == "__main__":
    main()
