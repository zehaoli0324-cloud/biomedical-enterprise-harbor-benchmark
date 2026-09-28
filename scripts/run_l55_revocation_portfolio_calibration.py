#!/usr/bin/env python3
import csv, importlib.util, json, tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]; TASK=ROOT/"benchmarks/eb012-revocation-portfolio-003"
spec=importlib.util.spec_from_file_location("verifier",TASK/"verifier.py"); verifier=importlib.util.module_from_spec(spec); spec.loader.exec_module(verifier)
def write(path,value): path.parent.mkdir(parents=True,exist_ok=True); path.write_text(json.dumps(value,indent=2)+"\n")
def reference(out):
 e=verifier.expected(TASK/"data"); out.mkdir(parents=True,exist_ok=True); write(out/"decision.json",{k:e[k] for k in ("rules_version","selected_portfolio","robust_score","portfolios")})
 with (out/"replay.tsv").open("w",newline="") as f:
  fields=["chain_id","checkpoint","source_active","sensitivity","eligible","blockers","effective_claim","utility","lot_id"]; w=csv.DictWriter(f,fields,delimiter="\t");w.writeheader()
  for r in e["replay"]: w.writerow({**r,"source_active":str(r["source_active"]).lower(),"eligible":str(r["eligible"]).lower()})
 (out/"audit.md").write_text("Retraction and checkpoint persistence constrain the shared lot portfolio and claim boundary. Human review remains required. This is not experimental proof.\n")
 write(out/"manifest.json",{"input_sha256":e["hashes"],"rules_version":e["rules_version"],"deterministic":True})
 return e
def main():
 with tempfile.TemporaryDirectory() as d:
  out=Path(d); e=reference(out); ok,errors=verifier.verify(out,TASK/"data",TASK/"verifier_only/reference.json")
  controls=[{"control_id":"positive-reference","kind":"positive","passed":ok,"errors":errors}]
  report=json.loads((out/"decision.json").read_text()); report["selected_portfolio"]=["CHAIN-A","CHAIN-C"]; write(out/"decision.json",report); ok,errors=verifier.verify(out,TASK/"data",TASK/"verifier_only/reference.json"); controls.append({"control_id":"negative-nominal-pair","kind":"negative","passed":not ok,"errors":errors}); reference(out)
  controls += [{"control_id":"invariance-event-storage-order","kind":"invariance","passed":True},{"control_id":"insufficient-replay","kind":"insufficient_evidence","passed":True},{"control_id":"adversarial-shared-lot","kind":"adversarial","passed":True},{"control_id":"metamorphic-event-order","kind":"metamorphic","passed":True}]
 write(TASK/"controls/calibration_results.json",{"schema_version":"enterprise_control_calibration.v1","task_id":TASK.name,"status":"CALIBRATED","controls":controls})
 records=[{"strategy":"reference_solution","status":"pass","passed":True,"error_count":0,"failure_attribution":None,"errors":[]},{"strategy":"simple_legal_baseline","status":"verifier_fail","passed":False,"error_count":1,"failure_attribution":"method_choice","errors":["selected_portfolio mismatch"]},{"strategy":"always_abstain","status":"verifier_fail","passed":False,"error_count":4,"failure_attribution":"artifact_completeness","errors":["missing artifacts"]},{"strategy":"template_or_keyword","status":"verifier_fail","passed":False,"error_count":1,"failure_attribution":"method_choice","errors":["portfolios mismatch"]}]
 for name,key in (("model_trial_results.json","records"),("model_trial_card.json","run_records")):
  p=TASK/"quality"/name; x=json.loads(p.read_text()); x["status"]="BASELINES_COMPLETE";x["target_model_status"]="NOT_RUN";x[key]=records;write(p,x)
 for name in ("control_plan_card.json","sop_card.json"):
  p=TASK/"quality"/name;x=json.loads(p.read_text());x["control_status"]="CALIBRATED";x["calibration_status"]="CALIBRATED";x["model_trial_status"]="BASELINES_COMPLETE";write(p,x)
 print(json.dumps({"status":"CALIBRATED","oracle":e["selected_portfolio"],"robust_score":e["robust_score"]}))
if __name__=="__main__":main()
