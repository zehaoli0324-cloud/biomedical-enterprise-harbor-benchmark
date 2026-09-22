from __future__ import annotations
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
