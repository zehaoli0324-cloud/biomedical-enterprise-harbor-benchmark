from __future__ import annotations
import argparse, csv, hashlib, io, itertools, json
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
            state_rows=[{"observation":state,"stage2_request_id":None,"residual_uncertainty":None,"max_critical_residual":None,"cost":None,"eligible":False} for state,_ in options]
            policies.append({"stage1_request_id":first["request_id"],"stage2_policy":{state:None for state,_ in options},"states":state_rows,"worst_case_max_critical_residual":None,"worst_case_cost":None,"eligible":False,"complete":False})
            continue
        for picks in itertools.product(*(x[1] for x in options)):
                if first["cost"]+max(r["cost"] for r in picks)>rules["total_budget"]: continue
                worst=-1.0; state_rows=[]
                for (state,_),second in zip(options,picks):
                    reductions=_route_reduction([first,second]); adj=first["outcomes"][state]
                    residual={u:round(max(rules["initial_uncertainty"][u]-reductions.get(u,0.0)-adj.get(u,0.0),0.0),6) for u in rules["initial_uncertainty"]}
                    maxcritical=max(residual[u] for u in rules["critical_thresholds"]); worst=max(worst,maxcritical)
                    state_rows.append({"observation":state,"stage2_request_id":second["request_id"],"residual_uncertainty":residual,"max_critical_residual":maxcritical,"cost":round(first["cost"]+second["cost"],6),"eligible":maxcritical<=max(rules["critical_thresholds"].values())})
                policies.append({"stage1_request_id":first["request_id"],"stage2_policy":{r["observation"]:r["stage2_request_id"] for r in state_rows},"states":state_rows,"worst_case_max_critical_residual":round(worst,6),"worst_case_cost":max(r["cost"] for r in state_rows),"eligible":all(r["eligible"] for r in state_rows),"complete":True})
    eligible=[p for p in policies if p["eligible"]]; winner=min(eligible,key=lambda p:(p["worst_case_max_critical_residual"],p["worst_case_cost"],p["stage1_request_id"],sorted(p["stage2_policy"].items())))
    files=sorted(p for p in data.rglob("*.json")); return {"decision":"execute_adaptive_route","selected_stage1_request_id":winner["stage1_request_id"],"selected_stage2_policy":winner["stage2_policy"],"worst_case_max_critical_residual":winner["worst_case_max_critical_residual"],"worst_case_cost":winner["worst_case_cost"],"policies":policies,"rules_version":rules["rules_version"],"network":manifest["network"],"hashes":{str(p.relative_to(data)):sha(p) for p in files}}
def verify(submission,data,reference):
    exp,errors=expected(data),[]
    for n in ("plan.json","route.tsv","decision.json","provenance.json","audit.md"):
        if not (submission/n).is_file(): errors.append("missing artifact: "+n)
    if errors:return False,errors
    parsed={}
    for name in ("plan.json","decision.json","provenance.json"):
        try:
            parsed[name]=json.loads((submission/name).read_text())
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            errors.append(f"invalid JSON: {name} ({exc.__class__.__name__})")
    if errors:return False,errors
    plan,decision=parsed["plan.json"],parsed["decision.json"]
    for name,payload in (("plan",plan),("decision",decision)):
        stage1 = payload.get("stage1_request_id", payload.get("selected_stage1_request_id"))
        if stage1!=exp["selected_stage1_request_id"] or payload.get("stage2_policy", payload.get("selected_stage2_policy"))!=exp["selected_stage2_policy"]: errors.append(name+" selected policy mismatch")
    if "network_used" in plan and plan.get("network_used") is not False: errors.append("plan environment mismatch")
    if "stop_condition" in plan and plan.get("stop_condition")!="adaptive_route_selected": errors.append("plan stop mismatch")
    if decision.get("decision") not in {"execute_adaptive_route","route_selected","select","selected",exp["selected_stage1_request_id"]}: errors.append("decision mismatch")
    if decision.get("worst_case_max_critical_residual")!=exp["worst_case_max_critical_residual"] or decision.get("worst_case_cost")!=exp["worst_case_cost"]: errors.append("objective mismatch")
    def canonical_policy(policy):
        states_present = "states" in policy or "observation_states" in policy
        states = policy.get("states", policy.get("observation_states", []))
        if isinstance(states, dict):
            states = [dict(value, observation=key) for key, value in states.items()]
        if states and all(isinstance(row, str) for row in states):
            states = []
            states_present = False
        normalized = []
        for row in states:
            residual = row.get("residual_uncertainty", row.get("residuals"))
            maximum = row.get("max_critical_residual", row.get("critical_residual_max"))
            if maximum is None and isinstance(residual, dict):
                maximum = max(float(residual[key]) for key in ("signal", "selectivity"))
            eligible = row.get("eligible", row.get("thresholds_met", row.get("critical_thresholds_met")))
            if eligible is None and maximum is not None:
                eligible = maximum <= 0.25
            normalized.append({"observation": row.get("observation", row.get("observation_state")), "stage2_request_id": row.get("stage2_request_id"), "residual_uncertainty": residual, "max_critical_residual": maximum, "cost": row.get("cost", row.get("total_cost")), "eligible": eligible})
        normalized.sort(key=lambda row: str(row["observation"]))
        stage2_policy = policy.get("stage2_policy", {})
        incomplete = bool(stage2_policy) and all(value is None for value in stage2_policy.values())
        return {"stage1_request_id": policy.get("stage1_request_id"), "stage2_policy": stage2_policy, "states": normalized, "states_present": states_present, "worst_case_max_critical_residual": None if incomplete else policy.get("worst_case_max_critical_residual"), "worst_case_cost": None if incomplete else policy.get("worst_case_cost"), "eligible": False if incomplete else policy.get("eligible"), "complete": False if incomplete else policy.get("complete", True)}
    def canonical_policies(value):
        if not isinstance(value, list): return []
        return sorted((canonical_policy(policy) for policy in value), key=lambda p: (str(p["stage1_request_id"]), sorted(p["stage2_policy"].items())))
    def policy_summaries(value):
        return [{key: policy[key] for key in ("stage1_request_id","stage2_policy","worst_case_max_critical_residual","worst_case_cost","eligible","complete")} for policy in canonical_policies(value)]
    def policies_equivalent(actual, expected):
        actual_rows, expected_rows = canonical_policies(actual), canonical_policies(expected)
        if policy_summaries(actual_rows) != policy_summaries(expected_rows):
            return False
        expected_by_id = {row["stage1_request_id"]: row for row in expected_rows}
        for row in actual_rows:
            expected_row = expected_by_id.get(row["stage1_request_id"])
            if expected_row["complete"] and row["states_present"] and row["states"] != expected_row["states"]:
                return False
        return True
    expected_policies = canonical_policies(exp["policies"])
    if not policies_equivalent(decision.get("policies"), exp["policies"]): errors.append("decision policies mismatch")
    if not policies_equivalent(plan.get("policies"), exp["policies"]): errors.append("plan policies mismatch")
    try:
        route_rows=list(csv.DictReader(io.StringIO((submission/"route.tsv").read_text()), delimiter="\t"))
    except (OSError, UnicodeDecodeError, csv.Error):
        route_rows=[]
    required_route_fields={"stage1_request_id","observation","stage2_request_id","eligible","blockers"}
    expected_route={(policy["stage1_request_id"], state["observation"]): state for policy in exp["policies"] for state in policy["states"]}
    actual_route={}
    for row in route_rows:
        key=(row.get("stage1_request_id",""), row.get("observation",""))
        if key in actual_route or not required_route_fields.issubset(row):
            errors.append("route schema mismatch")
            break
        actual_route[key]=row
    if set(actual_route)!=set(expected_route): errors.append("route coverage mismatch")
    elif not errors:
        for key, expected_state in expected_route.items():
            row=actual_route[key]
            expected_stage2=expected_state["stage2_request_id"] or ""
            expected_eligible=str(expected_state["eligible"]).lower()
            if row.get("stage2_request_id","")!=expected_stage2 or row.get("eligible","").lower()!=expected_eligible:
                errors.append("route state mismatch")
                break
    prov=parsed["provenance.json"]; hashes=prov.get("input_sha256",{})
    hashes={str(name).removeprefix("data/"): digest for name,digest in hashes.items() if str(name).removeprefix("data/")!="instruction.md"}
    if hashes!=exp["hashes"] or prov.get("rules_version")!=exp["rules_version"] or prov.get("network")!="off" or prov.get("deterministic") is not True: errors.append("provenance mismatch")
    audit=(submission/"audit.md").read_text().lower().replace("stage-1","stage 1").replace("stage-2","stage 2")
    for term in ("observation","stage 1","stage 2","dependency","budget","future","human review","not experimental proof"):
        if term not in audit: errors.append("audit missing "+term)
    return not errors,errors
if __name__=="__main__":
 p=argparse.ArgumentParser();p.add_argument("--submission",type=Path,required=True);p.add_argument("--data",type=Path,required=True);p.add_argument("--reference",type=Path,required=True);a=p.parse_args();ok,e=verify(a.submission,a.data,a.reference);print(json.dumps({"passed":ok,"errors":e}));raise SystemExit(0 if ok else 1)
