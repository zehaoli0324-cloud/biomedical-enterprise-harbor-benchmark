from __future__ import annotations
import argparse, csv, hashlib, json
from pathlib import Path
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def expected(data):
 case=json.loads((data/"case.json").read_text()); rules=json.loads((data/"rules.json").read_text()); arts={x["artifact_id"]:x for x in case["artifacts"]}; levels=rules["claim_levels"]; rows={}
 for chain in case["chains"]:
  selected=[arts.get(x) for x in chain["artifact_ids"]]; blockers=[]
  if any(x is None for x in selected): blockers.append("missing_artifact")
  if [x["stage"] for x in selected if x]!=rules["required_stage_order"]: blockers.append("stage_order")
  for i,x in enumerate(selected):
   if not x: continue
   if x["reported_hash"]!=x["content_hash"]: blockers.append("hash")
   if i and x["upstream_hash"]!=selected[i-1]["content_hash"]: blockers.append("upstream_hash")
   if x["scope"]!="active" or x["schema_ok"] is not True or x["status"]!="pass": blockers.append("schema_or_status")
  if all(selected):
   norm,route,policy=selected[1:]
   if norm.get("sensitivity")!="stable": blockers.append("sensitivity")
   if route.get("inventory_reservation")!="reserved" or route.get("evidence_quorum",0)<rules["min_evidence_quorum"]: blockers.append("inventory_or_quorum")
   if policy.get("future_outcome_leakage") is not False: blockers.append("future_outcome_leakage")
   if policy.get("human_review") is not True: blockers.append("human_review")
   if policy.get("robust_cvar",-1)<rules["min_robust_cvar"]: blockers.append("robust_threshold")
   if min(max(levels.get(p,0) for p in x["claim_permissions"]) for x in selected)<levels.get(chain["requested_claim"],99): blockers.append("claim_boundary")
  rows[chain["chain_id"]]={"eligible":not blockers,"blockers":sorted(set(blockers)),"requested_claim":chain["requested_claim"],"robust_cvar":selected[-1].get("robust_cvar") if selected else None,"artifact_ids":chain["artifact_ids"]}
 eligible={k:v for k,v in rows.items() if v["eligible"]}; selected=max(eligible,key=lambda k:(eligible[k]["robust_cvar"],k)) if eligible else "block"
 entities=[x["artifact_id"] for x in case["artifacts"]]; outcomes={x:str(any(x in r["artifact_ids"] and r["eligible"] for r in rows.values())).lower() for x in entities}
 return {"selected_chain":selected,"chains":rows,"entities":entities,"outcomes":outcomes,"hashes":{"case.json":sha(data/"case.json"),"rules.json":sha(data/"rules.json")},"rules_version":rules["rules_version"]}
def canonical_chains(report, exp):
 rows=report.get("chains")
 if not isinstance(rows,list): return None
 normalized={}
 for row in rows:
  if not isinstance(row,dict) or row.get("chain_id") not in exp["chains"]: return None
  normalized[row["chain_id"]]={k:row.get(k) for k in ("eligible","requested_claim","robust_cvar","artifact_ids")}
 return normalized if set(normalized)==set(exp["chains"]) else None
def verify(submission,data,reference):
 exp,errors=expected(data),[]
 for n in ("chain.json","handoff.tsv","audit.md","manifest.json"):
  if not (submission/n).is_file(): errors.append("missing artifact: "+n)
 if errors:return False,errors
 report=json.loads((submission/"chain.json").read_text())
 for f in ("selected_chain","rules_version"):
  if report.get(f)!=exp[f]: errors.append(f+" mismatch")
 expected_chains={k:{x:v[x] for x in ("eligible","requested_claim","robust_cvar","artifact_ids")} for k,v in exp["chains"].items()}
 if canonical_chains(report,exp)!=expected_chains: errors.append("chains mismatch")
 rows=list(csv.DictReader((submission/"handoff.tsv").open(newline=""),delimiter="\t")); required={"artifact_id","chain_id","stage","upstream_hash","content_hash","claim_permission","status"}
 if not rows or not required.issubset(rows[0]): errors.append("handoff schema incomplete")
 if sorted(r.get("artifact_id") for r in rows)!=sorted(exp["entities"]): errors.append("handoff coverage mismatch")
 artifacts={a["artifact_id"]:a for a in json.loads((data/"case.json").read_text())["artifacts"]}; chains=json.loads((data/"case.json").read_text())["chains"]
 for row in rows:
  artifact=artifacts.get(row.get("artifact_id"),{}); chain=next((item for item in chains if row.get("artifact_id") in item["artifact_ids"]),{})
  levels={"operational":1,"descriptive":2,"associational":3,"causal":4}; permissions=artifact.get("claim_permissions",[]); expected_permission=max(permissions,key=lambda p:levels[p]) if permissions else ""; chain_artifacts=[artifacts.get(x,{}) for x in chain.get("artifact_ids",[])]; chain_permission=min((max(a.get("claim_permissions",[]),key=lambda p:levels[p]) for a in chain_artifacts),key=lambda p:levels[p],default="")
  reported_permission=row.get("claim_permission","")
  if "|" in reported_permission:
   reported_permission=max((p for p in reported_permission.split("|") if p in levels),key=lambda p:levels[p],default="")
  expected_values={"chain_id":chain.get("chain_id",""),"stage":artifact.get("stage",""),"upstream_hash":artifact.get("upstream_hash") or "","content_hash":artifact.get("content_hash",""),"claim_permission":expected_permission,"status":artifact.get("status","")}
  for field,value in expected_values.items():
   actual=reported_permission if field=="claim_permission" else row.get(field)
   if field=="upstream_hash" and actual in ("null", "None"): actual=""
   if field=="claim_permission" and actual in (expected_permission, chain_permission): continue
   if actual!=str(value): errors.append("handoff "+field+" mismatch")
 review=(submission/"audit.md").read_text().lower()
 for variants in (("claim permission","claim-permission"),("upstream hash",),("inventory",),("human review",),("stop",),("not experimental proof","does not constitute experimental proof","not experimental-proof")):
  if not any(term in review for term in variants): errors.append("audit missing "+variants[0])
 manifest=json.loads((submission/"manifest.json").read_text())
 hashes=manifest.get("input_sha256",manifest.get("hashes"))
 if hashes is None and all(k in manifest for k in exp["hashes"]): hashes={k:manifest[k] for k in exp["hashes"]}
 if hashes is None and all(k in manifest for k in ("case_sha256", "rules_sha256")):
  hashes={"case.json":manifest["case_sha256"],"rules.json":manifest["rules_sha256"]}
 if hashes!=exp["hashes"] or manifest.get("rules_version")!=exp["rules_version"] or manifest.get("deterministic") is not True: errors.append("manifest provenance mismatch")
 return not errors,errors
if __name__=="__main__":
 p=argparse.ArgumentParser();p.add_argument("--submission",type=Path,required=True);p.add_argument("--data",type=Path,required=True);p.add_argument("--reference",type=Path,required=True);a=p.parse_args();ok,errors=verify(a.submission,a.data,a.reference);print(json.dumps({"passed":ok,"errors":errors}));raise SystemExit(0 if ok else 1)
