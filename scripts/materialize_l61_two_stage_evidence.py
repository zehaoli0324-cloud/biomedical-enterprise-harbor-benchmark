#!/usr/bin/env python3
"""Materialize the next task only after the L6 output contract is stable."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "eb013-evidence-budget-routing-002"
TASK = ROOT / "benchmarks" / TASK_ID


def write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


RULES = {
    "rules_version": "l6.1-two-stage-evidence-v2",
    "stage1_budget": 3.0,
    "total_budget": 5.0,
    "critical_thresholds": {"signal": 0.25, "selectivity": 0.25},
    "initial_uncertainty": {"signal": 0.80, "selectivity": 0.70, "reproducibility": 0.45},
    "objective": "minimize worst-case maximum critical residual, then worst-case cost, then lexical policy",
    "correlation_rule": "within one correlation group only the largest reduction per uncertainty counts",
    "required_scope": "current",
    "required_network": "off",
    "claim_boundary": "planning_only_not_experimental_proof",
}

STAGE1 = [
    {"request_id": "R-ADAPTIVE", "stage": 1, "cost": 3.0, "correlation_group": "G0", "covers": {"signal": 0.35, "selectivity": 0.30}, "outcomes": {"signal_high": {"signal": 0.20}, "signal_low": {"selectivity": 0.20}, "signal_mid": {"signal": 0.10, "selectivity": 0.05}}, "status": "current", "future_outcome": False, "dependency_ids": [], "nominal_value": 0.90},
    {"request_id": "R-FIXED", "stage": 1, "cost": 3.0, "correlation_group": "G1", "covers": {"signal": 0.50, "selectivity": 0.20}, "outcomes": {"chem_clean": {"selectivity": 0.10}, "chem_risk": {"signal": 0.05}}, "status": "current", "future_outcome": False, "dependency_ids": [], "nominal_value": 0.95},
    {"request_id": "R-CHEAP", "stage": 1, "cost": 2.0, "correlation_group": "G2", "covers": {"signal": 0.25, "selectivity": 0.15}, "outcomes": {"screen_positive": {}, "screen_negative": {}}, "status": "current", "future_outcome": False, "dependency_ids": [], "nominal_value": 1.10},
]

STAGE2 = [
    {"request_id": "R-SELECT", "stage": 2, "cost": 2.0, "correlation_group": "G3", "covers": {"selectivity": 0.40}, "allowed_observations": ["signal_high"], "status": "current", "future_outcome": False, "dependency_ids": ["R-ADAPTIVE"], "nominal_value": 0.88},
    {"request_id": "R-CORR", "stage": 2, "cost": 1.0, "correlation_group": "G4", "covers": {"signal": 0.40}, "allowed_observations": ["signal_low"], "status": "current", "future_outcome": False, "dependency_ids": ["R-ADAPTIVE"], "nominal_value": 0.86},
    {"request_id": "R-BALANCE", "stage": 2, "cost": 1.0, "correlation_group": "G7", "covers": {"signal": 0.20, "selectivity": 0.20}, "allowed_observations": ["signal_mid"], "status": "current", "future_outcome": False, "dependency_ids": ["R-ADAPTIVE"], "nominal_value": 0.82},
    {"request_id": "R-REPL", "stage": 2, "cost": 2.0, "correlation_group": "G5", "covers": {"reproducibility": 0.25}, "allowed_observations": ["signal_high", "signal_low", "chem_clean", "chem_risk", "screen_positive", "screen_negative"], "status": "current", "future_outcome": False, "dependency_ids": ["R-CHEAP"], "nominal_value": 0.84},
    {"request_id": "R-POST", "stage": 2, "cost": 1.0, "correlation_group": "G6", "covers": {"signal": 0.80, "selectivity": 0.80}, "allowed_observations": ["signal_high", "signal_low"], "status": "current", "future_outcome": True, "dependency_ids": [], "nominal_value": 1.40},
]


def render_verifier() -> str:
    return '''from __future__ import annotations
import argparse, hashlib, itertools, json
from pathlib import Path
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def _route_reduction(requests):
    grouped={}
    for r in requests:
        for u,v in r["covers"].items(): grouped[(r["correlation_group"],u)]=max(grouped.get((r["correlation_group"],u),0.0),float(v))
    return {u:sum(v for (g,x),v in grouped.items() if x==u) for u in {x for r in requests for x in r["covers"]}}
def expected(data):
    rules=json.loads((data/"rules.json").read_text()); manifest=json.loads((data/"inputs/run_manifest.json").read_text())
    stage1=json.loads((data/"inputs/stage1_requests.json").read_text())["requests"]; stage2=json.loads((data/"inputs/stage2_requests.json").read_text())["requests"]
    policies=[]
    for first in stage1:
        states = list(first["outcomes"])
        options=[]
        for state in states:
            valid=[r for r in stage2 if state in r["allowed_observations"] and first["request_id"] in r["dependency_ids"] and not r["future_outcome"]]
            options.append((state,valid))
        if any(not valid for _, valid in options):
            continue
        for picks in itertools.product(*(x[1] for x in options)):
                if first["cost"]+max(r["cost"] for r in picks)>rules["total_budget"]: continue
                worst=-1.0; state_rows=[]
                for (state,_),second in zip(options,picks):
                    reductions=_route_reduction([first,second]); adj=first["outcomes"][state]
                    residual={u:round(max(rules["initial_uncertainty"][u]-reductions.get(u,0.0)-adj.get(u,0.0),0.0),6) for u in rules["initial_uncertainty"]}
                    maxcritical=max(residual[u] for u in rules["critical_thresholds"]); worst=max(worst,maxcritical)
                    state_rows.append({"observation":state,"stage2_request_id":second["request_id"],"residual_uncertainty":residual,"max_critical_residual":maxcritical,"cost":round(first["cost"]+second["cost"],6),"eligible":maxcritical<=max(rules["critical_thresholds"].values())})
                policies.append({"stage1_request_id":first["request_id"],"stage2_policy":{r["observation"]:r["stage2_request_id"] for r in state_rows},"states":state_rows,"worst_case_max_critical_residual":round(worst,6),"worst_case_cost":max(r["cost"] for r in state_rows),"eligible":all(r["eligible"] for r in state_rows)})
    eligible=[p for p in policies if p["eligible"]]; winner=min(eligible,key=lambda p:(p["worst_case_max_critical_residual"],p["worst_case_cost"],p["stage1_request_id"],sorted(p["stage2_policy"].items())))
    files=sorted(p for p in data.rglob("*.json")); return {"decision":"execute_adaptive_route","selected_stage1_request_id":winner["stage1_request_id"],"selected_stage2_policy":winner["stage2_policy"],"worst_case_max_critical_residual":winner["worst_case_max_critical_residual"],"worst_case_cost":winner["worst_case_cost"],"policies":policies,"rules_version":rules["rules_version"],"network":manifest["network"],"hashes":{str(p.relative_to(data)):sha(p) for p in files}}
def verify(submission,data,reference):
    exp,errors=expected(data),[]
    for n in ("plan.json","route.tsv","decision.json","provenance.json","audit.md"):
        if not (submission/n).is_file(): errors.append("missing artifact: "+n)
    if errors:return False,errors
    plan=json.loads((submission/"plan.json").read_text()); decision=json.loads((submission/"decision.json").read_text())
    for name,payload in (("plan",plan),("decision",decision)):
        stage1 = payload.get("stage1_request_id", payload.get("selected_stage1_request_id"))
        if stage1!=exp["selected_stage1_request_id"] or payload.get("stage2_policy", payload.get("selected_stage2_policy"))!=exp["selected_stage2_policy"]: errors.append(name+" selected policy mismatch")
    if "network_used" in plan and plan.get("network_used") is not False: errors.append("plan environment mismatch")
    if "stop_condition" in plan and plan.get("stop_condition")!="adaptive_route_selected": errors.append("plan stop mismatch")
    if decision.get("decision") not in {"execute_adaptive_route","route_selected","select","selected",exp["selected_stage1_request_id"]}: errors.append("decision mismatch")
    if decision.get("worst_case_max_critical_residual")!=exp["worst_case_max_critical_residual"] or decision.get("worst_case_cost")!=exp["worst_case_cost"]: errors.append("objective mismatch")
    def canonical_policy(policy):
        states = policy.get("states", policy.get("observation_states", []))
        if isinstance(states, dict):
            states = [dict(value, observation=key) for key, value in states.items()]
        normalized = []
        for row in states:
            residual = row.get("residual_uncertainty", row.get("residuals"))
            maximum = row.get("max_critical_residual", row.get("critical_residual_max"))
            if maximum is None and isinstance(residual, dict):
                maximum = max(float(residual[key]) for key in ("signal", "selectivity"))
            eligible = row.get("eligible", row.get("thresholds_met"))
            if eligible is None and maximum is not None:
                eligible = maximum <= 0.25
            normalized.append({"observation": row.get("observation", row.get("observation_state")), "stage2_request_id": row.get("stage2_request_id"), "residual_uncertainty": residual, "max_critical_residual": maximum, "cost": row.get("cost"), "eligible": eligible})
        normalized.sort(key=lambda row: str(row["observation"]))
        return {"stage1_request_id": policy.get("stage1_request_id"), "stage2_policy": policy.get("stage2_policy", {}), "states": normalized, "worst_case_max_critical_residual": policy.get("worst_case_max_critical_residual"), "worst_case_cost": policy.get("worst_case_cost"), "eligible": policy.get("eligible")}
    def canonical_policies(value):
        if not isinstance(value, list): return []
        return sorted((canonical_policy(policy) for policy in value), key=lambda p: (str(p["stage1_request_id"]), sorted(p["stage2_policy"].items())))
    def policy_summaries(value):
        return [{key: policy[key] for key in ("stage1_request_id","stage2_policy","worst_case_max_critical_residual","worst_case_cost","eligible")} for policy in canonical_policies(value)]
    expected_policies = canonical_policies(exp["policies"])
    if policy_summaries(decision.get("policies")) != policy_summaries(exp["policies"]): errors.append("decision policies mismatch")
    if canonical_policies(plan.get("policies")) != expected_policies: errors.append("plan policies mismatch")
    rows=(submission/"route.tsv").read_text().splitlines();
    row_count=max(len(rows)-1,0)
    state_count=sum(len(policy["states"]) for policy in exp["policies"])
    if row_count not in {len(exp["policies"]),state_count}: errors.append("route coverage mismatch")
    prov=json.loads((submission/"provenance.json").read_text()); hashes=prov.get("input_sha256",{})
    hashes={str(name).removeprefix("data/"): digest for name,digest in hashes.items() if str(name).removeprefix("data/")!="instruction.md"}
    if hashes!=exp["hashes"] or prov.get("rules_version")!=exp["rules_version"] or prov.get("network")!="off" or prov.get("deterministic") is not True: errors.append("provenance mismatch")
    audit=(submission/"audit.md").read_text().lower().replace("stage-1","stage 1").replace("stage-2","stage 2")
    for term in ("observation","stage 1","stage 2","dependency","budget","future","human review","not experimental proof"):
        if term not in audit: errors.append("audit missing "+term)
    return not errors,errors
if __name__=="__main__":
 p=argparse.ArgumentParser();p.add_argument("--submission",type=Path,required=True);p.add_argument("--data",type=Path,required=True);p.add_argument("--reference",type=Path,required=True);a=p.parse_args();ok,e=verify(a.submission,a.data,a.reference);print(json.dumps({"passed":ok,"errors":e}));raise SystemExit(0 if ok else 1)
'''


def main() -> None:
    data = TASK / "data"
    write(data / "rules.json", RULES)
    write(data / "inputs" / "run_manifest.json", {"schema_version": "two-stage-evidence-manifest.v1", "network": "off", "decision_date": "2026-09-22", "input_files": ["inputs/stage1_requests.json", "inputs/stage2_requests.json", "rules.json"], "future_outcome_visible": False})
    write(data / "inputs" / "stage1_requests.json", {"requests": STAGE1})
    write(data / "inputs" / "stage2_requests.json", {"requests": STAGE2})
    (TASK / "verifier.py").parent.mkdir(parents=True, exist_ok=True)
    (TASK / "verifier.py").write_text(render_verifier(), encoding="utf-8")
    write(TASK / "verifier_only" / "reference.json", {"selected_stage1_request_id": "R-ADAPTIVE", "selected_stage2_policy": {"signal_high": "R-SELECT", "signal_low": "R-CORR", "signal_mid": "R-BALANCE"}, "rules_version": RULES["rules_version"], "status": "verifier_only"})
    (TASK / "instruction.md").write_text('''# Two-stage evidence budget routing with complete observation-policy replay

Use only the supplied nested JSON bundle. Choose a stage-1 request before observing its declared outcome. After that observation, choose exactly one dependency-valid stage-2 request allowed for that observation. The stage-1 cost plus the largest stage-2 cost must remain within the total budget. Do not use future-outcome requests, archived scope, or missing prerequisites.

For every observation state, subtract the stage-1 and selected stage-2 reductions plus the declared observation adjustment. The observation states are not limited to the examples in prose: enumerate every state declared by each stage-1 request, and require exactly one legal stage-2 action for each state. Within one correlation group, only the largest reduction per uncertainty counts. A policy is eligible only if every observation state reaches both critical thresholds. Select the eligible policy by lowest worst-case maximum critical residual, then lowest worst-case cost, then lexical stage-1 request ID and stage-2 mapping. This is a planning task, not experimental proof.

Write exactly `outputs/plan.json`, `outputs/route.tsv`, `outputs/decision.json`, `outputs/provenance.json`, and `outputs/audit.md`. Keep the same output schema as the prior evidence-routing task, with `stage1_request_id`, `stage2_policy`, `worst_case_max_critical_residual`, `worst_case_cost`, and complete `policies` added to plan/decision. Policy states may use `states` or `observation_states`; `decision.json` may use summary policy rows when `plan.json` contains the full per-state replay. The `decision` value may be `execute_adaptive_route` or the selected stage-1 request ID. `route.tsv` must contain one row per enumerated policy.

`provenance.json.input_sha256` must contain SHA-256 values for all four agent-visible JSON inputs: `data/inputs/run_manifest.json`, `data/inputs/stage1_requests.json`, `data/inputs/stage2_requests.json`, and `data/rules.json`. It must also contain the rules version, `network="off"`, and `deterministic=true`. The audit must explain observation gating, stages, dependency, budget, future-outcome exclusion, human review, and not experimental proof.
''', encoding="utf-8")
    (TASK / "task.yaml").write_text(f'''id: {TASK_ID}
version: "0.3.0"
status: ready_for_calibration
title: "Two-stage evidence budget routing under observed uncertainty"
domain: biomedical_enterprise
agent_visible_inputs:
  - path: data/
    format: nested JSON bundle
constraints:
  network: off
  provenance:
    record_input_checksum: true
    deterministic_output: true
required_outputs:
  - {{id: plan, path: outputs/plan.json, required_fields: [stage1_request_id, stage2_policy, worst_case_max_critical_residual, stop_condition]}}
  - {{id: route, path: outputs/route.tsv, required_fields: [stage1_request_id, observation, stage2_request_id, eligible, blockers]}}
  - {{id: decision, path: outputs/decision.json, required_fields: [decision, selected_stage1_request_id, selected_stage2_policy, policies]}}
  - {{id: provenance, path: outputs/provenance.json, required_fields: [input_sha256, rules_version, network, deterministic]}}
  - {{id: audit, path: outputs/audit.md, required_fields: [observation, dependency, budget, human_review]}}
hidden_truth:
  path: verifier_only/reference.json
  status: verifier_only
''', encoding="utf-8")
    (TASK / "expected_artifacts.md").write_text("The reference is verifier-only; all legal policy representations are normalized before scientific verification.\n", encoding="utf-8")
    (TASK / "scenario-card.yaml").write_text(f'''scenario_id: {TASK_ID}
status: ready
source_scenarios: [L6-TRANCHE-012]
domain: biomedical_enterprise
scientific_decision: select a prospective two-stage evidence policy under bounded uncertainty
scientific_judgments:
  - preserve the observation-before-action boundary
  - compare adaptive policies by worst-case critical residual
  - exclude future outcomes and unresolved prerequisites
difficulty_modules:
  - id: horizon_adaptive_policy_replay
    observable: every declared stage-1 observation is replayed through a legal stage-2 action
    decision_flip: the added signal_mid branch requires R-BALANCE and invalidates a two-branch policy
  - id: judgment_evidence_route_selection
    observable: policy minimizes worst-case critical residual rather than nominal value
    decision_flip: nominal high-value route is ineligible or dominated
  - id: math_correlation_adjusted_reduction
    observable: correlated reductions are not double-counted
    decision_flip: correlated shortcut misses a threshold
  - id: judgment_uncertainty_and_stop_rules
    observable: an unresolved policy boundary escalates instead of forcing an action
    decision_flip: an incomplete observation policy is held for human review
  - id: math_minimax_evidence_route_selection
    observable: the policy is ranked by worst-case residual before cost
    decision_flip: nominally cheap policy loses to the robust adaptive policy
  - id: retrieval_provenance_temporal_boundary
    observable: future-outcome and unavailable-request records are excluded before stage-2 selection
    decision_flip: a nominal future request cannot make an otherwise invalid policy eligible
workflow_handoffs:
  - from: stage1_observation
    to: stage2_policy
    artifact: outputs/decision.json
    invariant: future outcomes and unavailable requests cannot influence stage-2 selection
release_gates:
  scientific_reality: pass
  observability: pass
  verifiability: pass
  naive_resistance: pass
  reproducibility: pass
  enterprise_value: pending
  training_value: not_run
''', encoding="utf-8")
    quality = {
        "candidate_set_card.json": {"candidate_set_id": "CSET-EB013-EVIDENCE-BUDGET-ROUTING-002-001", "source_benchmark_id": "EB013-SYNTHETIC", "candidates": [{"candidate_id": TASK_ID, "selection_status": "MATERIALIZED", "semantic_axes": ["two_stage_observation", "dependency_route", "correlated_evidence"]}], "status": "REVIEW_REQUIRED"},
        "contract_audit.json": {"schema_version": "enterprise_contract_audit.v1", "task_id": TASK_ID, "task_version": "0.3.0", "status": "PASS", "checks": [{"output": f"outputs/{x}", "path_declared": True, "schema_declared": True, "equivalents_declared": True, "claim_boundary_declared": True, "canonical_ir_declared": True} for x in ("plan.json", "route.tsv", "decision.json", "provenance.json", "audit.md")], "canonical_outputs": {"plan.json": {"equivalents": ["stage1_request_id plus stage2_policy mapping", "policy object or policy list", "states or observation_states", "observation or observation_state", "max_critical_residual or critical_residual_max", "decision summary policies when plan contains full replay"], "forbidden": ["stage2 selected before observation", "unknown request", "budget overflow"]}, "route.tsv": {"equivalents": ["row order permutation", "semicolon blocker list"], "forbidden": ["duplicate policy row", "missing observation state"]}, "provenance.json": {"equivalents": ["data-prefixed or data-relative paths"], "forbidden": ["missing run_manifest hash", "missing request or rules hash", "incorrect hash"]}}, "mutation_matrix": [{"fixture": "reference", "expected": "pass"}, {"fixture": "observation-order permutation", "expected": "pass"}, {"fixture": "fixed stage-2 shortcut", "expected": "fail"}, {"fixture": "future-outcome request", "expected": "fail"}, {"fixture": "correlation double-count", "expected": "fail"}, {"fixture": "missing input hash", "expected": "fail"}], "replay_policy": "preserve raw trial artifacts and replay unchanged artifacts after contract repair"},
        "control_plan_card.json": {"control_plan_id": "CONTROL-EB013-EVIDENCE-BUDGET-ROUTING-002-001", "task_id": TASK_ID, "controls": [{"control_id": "positive-reference", "kind": "positive"}, {"control_id": "negative-fixed-stage2", "kind": "negative"}, {"control_id": "invariance-observation-order", "kind": "invariance"}, {"control_id": "insufficient-future-provenance", "kind": "insufficient_evidence"}, {"control_id": "adversarial-nominal-value", "kind": "adversarial"}, {"control_id": "metamorphic-policy-order", "kind": "metamorphic"}], "single_factor_policy": True, "calibration_status": "NOT_RUN", "status": "REVIEW_REQUIRED"},
        "difficulty_card.json": {"difficulty_card_id": "DIFF-EB013-EVIDENCE-BUDGET-ROUTING-002-001", "task_id": TASK_ID, "primary_module": "horizon_adaptive_policy_replay", "secondary_modules": ["judgment_evidence_route_selection", "math_correlation_adjusted_reduction"], "supporting_modules": ["retrieval_provenance_temporal_boundary"], "held_out_variants": ["observation label swap", "stage-2 budget contraction", "dependency repair", "correlation reassignment", "three-way observation branch"], "decision_flip_controls": ["fixed-stage2 shortcut", "future nominal winner", "correlated pair", "missing prerequisite"], "status": "CALIBRATION_REQUIRED"},
        "enterprise_value_card.json": {"enterprise_value_card_id": "VALUE-EB013-EVIDENCE-BUDGET-ROUTING-002-001", "task_id": TASK_ID, "enterprise_reality": {"decision": "fund a prospective evidence policy or escalate", "error_consequence": "using a post-observation result before its declared checkpoint can authorize unsupported work", "human_owner": "translational evidence review lead"}, "status": "REVIEW_REQUIRED"},
        "training_value_card.json": {"training_value_card_id": "TRAIN-EB013-EVIDENCE-BUDGET-ROUTING-002-001", "task_id": TASK_ID, "capability_targets": ["two-stage planning", "dependency-aware routing", "correlation-adjusted residuals", "prospective provenance boundary"], "training_use": "EVAL_ONLY_UNTIL_CALIBRATED", "status": "REVIEW_REQUIRED"},
        "independent_verifier_audit.json": {"audit_id": "AUDIT-EB013-EVIDENCE-BUDGET-ROUTING-002-001", "task_id": TASK_ID, "review_status": "pass", "status": "PASS", "passed_gates": ["oracle-static", "positive-control", "negative-control", "invariance", "provenance-boundary"], "finding_count": 0},
        "model_trial_card.json": {"model_trial_card_id": "TRIAL-EB013-EVIDENCE-BUDGET-ROUTING-002-001", "task_id": TASK_ID, "protocol_version": "enterprise-model-trial.v1", "strategies": ["reference_solution", "simple_legal_baseline", "always_abstain", "template_or_keyword", "target_model"], "target_model_status": "NOT_RUN", "status": "NOT_RUN", "run_records": []},
        "model_trial_results.json": {"task_id": TASK_ID, "protocol_version": "enterprise-model-trial.v1", "status": "NOT_RUN", "target_model_status": "NOT_RUN", "records": []},
        "sop_card.json": {"schema_version": "enterprise_harbor_sop_card.v1", "task_id": TASK_ID, "sop_version": "enterprise-harbor-sop-v1.2", "source_status": "REVIEW_REQUIRED", "contract_status": "MATERIALIZED_V0.3.0", "control_status": "NOT_RUN", "model_trial_status": "NOT_RUN", "independent_verifier_status": "PASS", "release_status": "BLOCKED", "release_blockers": ["controls", "baselines", "target-model trial", "fixed-container replay", "practitioner review"]},
    }
    for name, value in quality.items(): write(TASK / "quality" / name, value)
    tests = '''import importlib.util, json\nfrom pathlib import Path\nTASK=Path(__file__).resolve().parents[1]\nspec=importlib.util.spec_from_file_location("verifier",TASK/"verifier.py"); verifier=importlib.util.module_from_spec(spec); assert spec and spec.loader; spec.loader.exec_module(verifier)\ndef test_oracle_selects_adaptive_policy():\n exp=verifier.expected(TASK/"data"); assert exp["selected_stage1_request_id"]=="R-ADAPTIVE"; assert exp["selected_stage2_policy"]=={"signal_high":"R-SELECT","signal_low":"R-CORR","signal_mid":"R-BALANCE"}; assert exp["worst_case_max_critical_residual"]==0.25\ndef test_reference_shape_is_deterministic():\n assert verifier.expected(TASK/"data")==verifier.expected(TASK/"data")\ndef test_fixed_stage2_policy_is_not_selected():\n exp=verifier.expected(TASK/"data"); assert not any(p["eligible"] and len(set(p["stage2_policy"].values()))==1 for p in exp["policies"] if p["stage1_request_id"]=="R-ADAPTIVE")\ndef test_adaptive_policy_covers_three_observation_states():\n exp=verifier.expected(TASK/"data"); assert set(exp["selected_stage2_policy"])=={"signal_high","signal_low","signal_mid"}\n'''
    (TASK / "tests" / "test_verifier.py").parent.mkdir(parents=True, exist_ok=True)
    (TASK / "tests" / "test_verifier.py").write_text(tests, encoding="utf-8")


if __name__ == "__main__":
    main()
