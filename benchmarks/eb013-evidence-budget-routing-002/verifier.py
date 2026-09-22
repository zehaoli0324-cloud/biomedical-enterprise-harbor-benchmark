from __future__ import annotations
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
    if plan.get("network_used") is not False or plan.get("stop_condition")!="adaptive_route_selected": errors.append("plan environment or stop mismatch")
    if decision.get("decision") not in {"execute_adaptive_route","route_selected"}: errors.append("decision mismatch")
    if decision.get("worst_case_max_critical_residual")!=exp["worst_case_max_critical_residual"] or decision.get("worst_case_cost")!=exp["worst_case_cost"]: errors.append("objective mismatch")
    if decision.get("policies")!=exp["policies"]: errors.append("policies mismatch")
    rows=(submission/"route.tsv").read_text().splitlines();
    if len(rows)!=1+sum(len(policy["states"]) for policy in exp["policies"]): errors.append("route coverage mismatch")
    prov=json.loads((submission/"provenance.json").read_text()); hashes=prov.get("input_sha256",{})
    if hashes!=exp["hashes"] or prov.get("rules_version")!=exp["rules_version"] or prov.get("network")!="off" or prov.get("deterministic") is not True: errors.append("provenance mismatch")
    audit=(submission/"audit.md").read_text().lower()
    for term in ("observation","stage 1","stage 2","dependency","budget","future","human review","not experimental proof"):
        if term not in audit: errors.append("audit missing "+term)
    return not errors,errors
if __name__=="__main__":
 p=argparse.ArgumentParser();p.add_argument("--submission",type=Path,required=True);p.add_argument("--data",type=Path,required=True);p.add_argument("--reference",type=Path,required=True);a=p.parse_args();ok,e=verify(a.submission,a.data,a.reference);print(json.dumps({"passed":ok,"errors":e}));raise SystemExit(0 if ok else 1)
