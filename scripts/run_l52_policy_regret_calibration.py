#!/usr/bin/env python3
"""Run controls and author baselines for the L5.2 policy-regret task."""

from __future__ import annotations
import csv, importlib.util, json, shutil, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "eb010-adaptive-policy-regret-005"
TASK = ROOT / "benchmarks" / TASK_ID

def load():
    spec=importlib.util.spec_from_file_location("policy_regret_verifier",TASK/"verifier.py"); module=importlib.util.module_from_spec(spec); assert spec and spec.loader; spec.loader.exec_module(module); return module

def reference(verifier, output, data):
    exp=verifier.expected(data); output.mkdir(parents=True,exist_ok=True)
    (output/"policy.json").write_text(json.dumps({"selected_policy":exp["selected_policy"],"rules_version":exp["rules_version"],"claim_boundary":"planning_only_not_experimental_proof","human_review_required":True,"policies":exp["policies"]}))
    fields=["policy_id","scenario_id","observation","action","total_cost","utility","regret","eligible","blockers"]
    with (output/"branches.tsv").open("w",newline="") as handle:
        writer=csv.DictWriter(handle,fieldnames=fields,delimiter="\t"); writer.writeheader()
        for pid,policy in exp["policies"].items():
            for sid,branch in policy["branches"].items(): writer.writerow({"policy_id":pid,"scenario_id":sid,**branch,"eligible":str(policy["eligible"]).lower(),"blockers":";".join(policy["blockers"])})
    (output/"manifest.json").write_text(json.dumps({"input_sha256":exp["hashes"],"rules_version":exp["rules_version"],"deterministic":True}))
    (output/"audit.md").write_text("Minimax regret, budget, future outcome, branch completeness and human review are explicit. This is not experimental proof.\n")

def main():
    verifier=load(); controls=[]
    with tempfile.TemporaryDirectory(prefix="l52-controls-") as temp:
        root=Path(temp); positive=root/"positive"; reference(verifier,positive,TASK/"data")
        passed,errors=verifier.verify(positive,TASK/"data",TASK/"verifier_only/reference.json"); controls.append({"control_id":"positive-reference","kind":"positive","passed":passed,"errors":errors})
        cross_artifact=root/"cross-artifact"; shutil.copytree(positive,cross_artifact); lines=(cross_artifact/"branches.tsv").read_text().splitlines(); header=lines[0].split("\t"); values=lines[1].split("\t"); values[header.index("utility") ]="999.0"; lines[1]="\t".join(values); (cross_artifact/"branches.tsv").write_text("\n".join(lines)+"\n")
        passed,errors=verifier.verify(cross_artifact,TASK/"data",TASK/"verifier_only/reference.json"); controls.append({"control_id":"negative-cross-artifact-utility","kind":"negative","passed":not passed,"errors":errors})
        negative=root/"negative"; shutil.copytree(positive,negative); report=json.loads((negative/"policy.json").read_text()); report["selected_policy"]="P-GREEDY"; (negative/"policy.json").write_text(json.dumps(report)); passed,errors=verifier.verify(negative,TASK/"data",TASK/"verifier_only/reference.json"); controls.append({"control_id":"negative-greedy-policy","kind":"negative","passed":not passed,"errors":errors})
        invariant=root/"invariant"; shutil.copytree(positive,invariant); rows=list(csv.DictReader((invariant/"branches.tsv").open(newline=""),delimiter="\t")); rows.reverse();
        with (invariant/"branches.tsv").open("w",newline="") as handle: writer=csv.DictWriter(handle,fieldnames=list(rows[0]),delimiter="\t"); writer.writeheader(); writer.writerows(rows)
        passed,errors=verifier.verify(invariant,TASK/"data",TASK/"verifier_only/reference.json"); controls.append({"control_id":"invariance-policy-order","kind":"invariance","passed":passed,"errors":errors})
        missing=root/"missing"; shutil.copytree(positive,missing); manifest=json.loads((missing/"manifest.json").read_text()); manifest["input_sha256"].pop("inputs/actions.json"); (missing/"manifest.json").write_text(json.dumps(manifest)); passed,errors=verifier.verify(missing,TASK/"data",TASK/"verifier_only/reference.json"); controls.append({"control_id":"insufficient-manifest","kind":"insufficient_evidence","passed":not passed,"errors":errors})
        exp=verifier.expected(TASK/"data"); controls.append({"control_id":"adversarial-over-budget-utility","kind":"adversarial","passed":not exp["policies"]["P-OVERRUN"]["eligible"] and exp["selected_policy"]=="P-ROBUST"})
        reordered=root/"reordered"; shutil.copytree(TASK/"data",reordered); policies=json.loads((reordered/"inputs/policies.json").read_text()); policies.reverse(); (reordered/"inputs/policies.json").write_text(json.dumps(policies)); controls.append({"control_id":"metamorphic-policy-order","kind":"metamorphic","passed":verifier.expected(reordered)["selected_policy"]=="P-ROBUST"})
    calibration={"schema_version":"enterprise_control_calibration.v1","task_id":TASK_ID,"status":"CALIBRATED" if all(row["passed"] for row in controls) else "FAILED","controls":controls}; (TASK/"controls/calibration_results.json").parent.mkdir(exist_ok=True); (TASK/"controls/calibration_results.json").write_text(json.dumps(calibration,indent=2)+"\n")
    records=[]
    for strategy in ("reference_solution","simple_legal_baseline","always_abstain","template_or_keyword"):
        with tempfile.TemporaryDirectory(prefix="l52-baseline-") as temp:
            output=Path(temp)/"outputs"; reference(verifier,output,TASK/"data")
            if strategy=="simple_legal_baseline": report=json.loads((output/"policy.json").read_text()); report["selected_policy"]="P-GREEDY"; (output/"policy.json").write_text(json.dumps(report))
            elif strategy=="always_abstain": shutil.rmtree(output); output.mkdir()
            elif strategy=="template_or_keyword": report=json.loads((output/"policy.json").read_text()); report["policies"]={"P-ROBUST":report["policies"]["P-ROBUST"]}; (output/"policy.json").write_text(json.dumps(report))
            passed,errors=verifier.verify(output,TASK/"data",TASK/"verifier_only/reference.json"); records.append({"strategy":strategy,"status":"pass" if passed else "verifier_fail","passed":passed,"error_count":len(errors),"failure_attribution":None if passed else ("artifact_completeness" if strategy=="always_abstain" else "method_choice"),"errors":errors})
    results={"task_id":TASK_ID,"protocol_version":"enterprise-model-trial.v1","status":"BASELINES_COMPLETE","target_model_status":"NOT_RUN","records":records}; (TASK/"quality/model_trial_results.json").write_text(json.dumps(results,indent=2)+"\n")
    card=json.loads((TASK/"quality/model_trial_card.json").read_text()); card.update({"status":"BASELINES_COMPLETE","target_model_status":"NOT_RUN","run_records":records}); (TASK/"quality/model_trial_card.json").write_text(json.dumps(card,indent=2)+"\n")
    plan=json.loads((TASK/"quality/control_plan_card.json").read_text()); plan.update({"calibration_status":calibration["status"],"status":calibration["status"]}); (TASK/"quality/control_plan_card.json").write_text(json.dumps(plan,indent=2)+"\n")
    sop=json.loads((TASK/"quality/sop_card.json").read_text()); sop.update({"control_status":calibration["status"],"model_trial_status":"BASELINES_COMPLETE"}); (TASK/"quality/sop_card.json").write_text(json.dumps(sop,indent=2)+"\n")
    print(json.dumps({"calibration":calibration,"baselines":results},indent=2)); return 0 if calibration["status"]=="CALIBRATED" and records[0]["passed"] and all(not row["passed"] for row in records[1:]) else 1

if __name__=="__main__": raise SystemExit(main())
