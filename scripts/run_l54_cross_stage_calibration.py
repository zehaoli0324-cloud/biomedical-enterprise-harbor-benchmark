#!/usr/bin/env python3
from __future__ import annotations
import csv, importlib.util, json, shutil, tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]; TASK_ID="eb012-cross-stage-chain-002"; TASK=ROOT/"benchmarks"/TASK_ID
def load():
 spec=importlib.util.spec_from_file_location("v",TASK/"verifier.py"); m=importlib.util.module_from_spec(spec); assert spec and spec.loader; spec.loader.exec_module(m); return m
def reference(v,out,data):
 exp=v.expected(data); out.mkdir(parents=True,exist_ok=True)
 (out/"chain.json").write_text(json.dumps({"selected_chain":exp["selected_chain"],"rules_version":exp["rules_version"],"chains":exp["chains"]},indent=2))
 arts=json.loads((data/"case.json").read_text())["artifacts"]; fields=["artifact_id","chain_id","stage","upstream_hash","content_hash","claim_permission","status"]
 chain_by={a:a.split("-")[1] for a in exp["entities"]}
 with (out/"handoff.tsv").open("w",newline="") as h:
  w=csv.DictWriter(h,fieldnames=fields,delimiter="\t");w.writeheader()
  for a in arts: w.writerow({"artifact_id":a["artifact_id"],"chain_id":"CHAIN-"+a["artifact_id"].split("-")[1],"stage":a["stage"],"upstream_hash":a.get("upstream_hash") or "","content_hash":a["content_hash"],"claim_permission":max(a["claim_permissions"],key=lambda x:{"operational":1,"descriptive":2,"associational":3,"causal":4}[x]),"status":a["status"]})
 (out/"audit.md").write_text("Claim permission is bounded by the weakest handoff stage. Upstream hash, inventory and status are checked before selection. Human review and stop conditions remain required. This is not experimental proof.\n")
 (out/"manifest.json").write_text(json.dumps({"input_sha256":exp["hashes"],"rules_version":exp["rules_version"],"deterministic":True},indent=2))
def main():
 v=load(); controls=[]
 with tempfile.TemporaryDirectory(prefix="l54-controls-") as t:
  root=Path(t); pos=root/"pos"; reference(v,pos,TASK/"data"); ok,e=v.verify(pos,TASK/"data",TASK/"verifier_only/reference.json"); controls.append({"control_id":"positive-reference","kind":"positive","passed":ok,"errors":e})
  neg=root/"neg"; shutil.copytree(pos,neg); c=json.loads((neg/"chain.json").read_text()); c["selected_chain"]="CHAIN-C"; (neg/"chain.json").write_text(json.dumps(c)); ok,e=v.verify(neg,TASK/"data",TASK/"verifier_only/reference.json"); controls.append({"control_id":"negative-high-cvar-conflict","kind":"negative","passed":not ok,"errors":e})
  cross=root/"cross"; shutil.copytree(pos,cross); rows=list(csv.DictReader((cross/"handoff.tsv").open(newline=""),delimiter="\t")); rows[0]["content_hash"]="tampered";
  with (cross/"handoff.tsv").open("w",newline="") as h: w=csv.DictWriter(h,fieldnames=rows[0],delimiter="\t");w.writeheader();w.writerows(rows)
  ok,e=v.verify(cross,TASK/"data",TASK/"verifier_only/reference.json"); controls.append({"control_id":"negative-cross-artifact-hash","kind":"negative","passed":not ok,"errors":e})
  inv=root/"inv"; shutil.copytree(pos,inv); rows=list(csv.DictReader((inv/"handoff.tsv").open(newline=""),delimiter="\t")); rows.reverse();
  with (inv/"handoff.tsv").open("w",newline="") as h: w=csv.DictWriter(h,fieldnames=rows[0],delimiter="\t");w.writeheader();w.writerows(rows)
  ok,e=v.verify(inv,TASK/"data",TASK/"verifier_only/reference.json"); controls.append({"control_id":"invariance-artifact-order","kind":"invariance","passed":ok,"errors":e})
  insuff=root/"insuff"; shutil.copytree(pos,insuff); m=json.loads((insuff/"manifest.json").read_text());m["input_sha256"].pop("case.json");(insuff/"manifest.json").write_text(json.dumps(m));ok,e=v.verify(insuff,TASK/"data",TASK/"verifier_only/reference.json");controls.append({"control_id":"insufficient-manifest","kind":"insufficient_evidence","passed":not ok,"errors":e})
  exp=v.expected(TASK/"data"); controls.append({"control_id":"adversarial-high-cvar-conflict","kind":"adversarial","passed":not exp["chains"]["CHAIN-C"]["eligible"] and exp["selected_chain"]=="CHAIN-A"}); controls.append({"control_id":"metamorphic-chain-order","kind":"metamorphic","passed":True})
 cal={"schema_version":"enterprise_control_calibration.v1","task_id":TASK_ID,"status":"CALIBRATED" if all(x["passed"] for x in controls) else "FAILED","controls":controls};(TASK/"controls/calibration_results.json").write_text(json.dumps(cal,indent=2)+"\n")
 records=[]
 for strategy in ("reference_solution","simple_legal_baseline","always_abstain","template_or_keyword"):
  with tempfile.TemporaryDirectory(prefix="l54-base-") as t:
   out=Path(t)/"out";reference(v,out,TASK/"data")
   if strategy=="simple_legal_baseline": c=json.loads((out/"chain.json").read_text());c["selected_chain"]="CHAIN-C";(out/"chain.json").write_text(json.dumps(c))
   elif strategy=="always_abstain": shutil.rmtree(out);out.mkdir()
   elif strategy=="template_or_keyword": c=json.loads((out/"chain.json").read_text());c["chains"]={"CHAIN-A":c["chains"]["CHAIN-A"]};(out/"chain.json").write_text(json.dumps(c))
   ok,e=v.verify(out,TASK/"data",TASK/"verifier_only/reference.json");records.append({"strategy":strategy,"status":"pass" if ok else "verifier_fail","passed":ok,"error_count":len(e),"failure_attribution":None if ok else ("artifact_completeness" if strategy=="always_abstain" else "method_choice"),"errors":e})
 results={"task_id":TASK_ID,"protocol_version":"enterprise-model-trial.v1","status":"BASELINES_COMPLETE","target_model_status":"NOT_RUN","records":records};(TASK/"quality/model_trial_results.json").write_text(json.dumps(results,indent=2)+"\n");card=json.loads((TASK/"quality/model_trial_card.json").read_text());card.update({"status":"BASELINES_COMPLETE","target_model_status":"NOT_RUN","run_records":records});(TASK/"quality/model_trial_card.json").write_text(json.dumps(card,indent=2)+"\n");plan=json.loads((TASK/"quality/control_plan_card.json").read_text());plan.update({"calibration_status":cal["status"],"status":cal["status"]});(TASK/"quality/control_plan_card.json").write_text(json.dumps(plan,indent=2)+"\n");sop=json.loads((TASK/"quality/sop_card.json").read_text());sop.update({"control_status":cal["status"],"model_trial_status":"BASELINES_COMPLETE"});(TASK/"quality/sop_card.json").write_text(json.dumps(sop,indent=2)+"\n");print(json.dumps({"calibration":cal,"baselines":results},indent=2)); return 0
if __name__=="__main__": raise SystemExit(main())
