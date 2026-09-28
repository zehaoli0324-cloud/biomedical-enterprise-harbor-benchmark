#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "eb012-cross-stage-chain-002"
TASK = ROOT / "benchmarks" / TASK_ID

def write(path: Path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n" if isinstance(value, (dict, list)) else value, encoding="utf-8")

def artifact(aid, stage, h, upstream, perms, **extra):
    return {"artifact_id": aid, "stage": stage, "version": extra.pop("version", "v1"), "content_hash": h, "reported_hash": extra.pop("reported_hash", h), "upstream_hash": upstream, "scope": "active", "schema_ok": True, "status": "pass", "claim_permissions": perms, **extra}

ARTIFACTS = [
    artifact("R-A", "recovery", "r-a", None, ["operational", "descriptive", "associational"]),
    artifact("N-A", "normalization", "n-a", "r-a", ["operational", "descriptive", "associational"], sensitivity="stable"),
    artifact("T-A", "route", "t-a", "n-a", ["operational", "descriptive", "associational"], inventory_reservation="reserved", evidence_quorum=2),
    artifact("P-A", "policy", "p-a", "t-a", ["operational", "descriptive", "associational"], future_outcome_leakage=False, robust_cvar=0.82, human_review=True),
    artifact("R-B", "recovery", "r-b", None, ["operational", "descriptive", "associational"]),
    artifact("N-B", "normalization", "n-b", "r-b", ["operational", "descriptive", "associational"], sensitivity="stable"),
    artifact("T-B", "route", "t-b", "n-b", ["operational", "descriptive", "associational"], reported_hash="wrong-t-b", inventory_reservation="reserved", evidence_quorum=2),
    artifact("P-B", "policy", "p-b", "wrong-t-b", ["operational", "descriptive", "associational"], future_outcome_leakage=False, robust_cvar=0.95, human_review=True),
    artifact("R-C", "recovery", "r-c", None, ["operational", "descriptive", "associational"]),
    artifact("N-C", "normalization", "n-c", "r-c", ["operational", "descriptive", "associational"], sensitivity="stable"),
    artifact("T-C", "route", "t-c", "n-c", ["operational", "descriptive", "associational"], inventory_reservation="conflict", evidence_quorum=3),
    artifact("P-C", "policy", "p-c", "t-c", ["operational", "descriptive", "associational"], future_outcome_leakage=False, robust_cvar=0.99, human_review=True),
    artifact("R-D", "recovery", "r-d", None, ["operational", "descriptive", "associational"]),
    artifact("N-D", "normalization", "n-d", "r-d", ["operational", "descriptive"], sensitivity="sensitive"),
    artifact("T-D", "route", "t-d", "n-d", ["operational", "descriptive"], inventory_reservation="reserved", evidence_quorum=2),
    artifact("P-D", "policy", "p-d", "t-d", ["operational", "descriptive"], future_outcome_leakage=False, robust_cvar=0.91, human_review=True),
]
CHAINS = [{"chain_id": f"CHAIN-{x}", "artifact_ids": [f"R-{x}", f"N-{x}", f"T-{x}", f"P-{x}"], "requested_claim": "associational"} for x in "ABCD"]
RULES = {"rules_version": "l5.4-cross-stage-chain-v1", "required_stage_order": ["recovery", "normalization", "route", "policy"], "claim_levels": {"operational": 1, "descriptive": 2, "associational": 3, "causal": 4}, "min_evidence_quorum": 2, "min_robust_cvar": 0.8}

VERIFIER = r'''from __future__ import annotations
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
def verify(submission,data,reference):
 exp,errors=expected(data),[]
 for n in ("chain.json","handoff.tsv","audit.md","manifest.json"):
  if not (submission/n).is_file(): errors.append("missing artifact: "+n)
 if errors:return False,errors
 report=json.loads((submission/"chain.json").read_text())
 for f in ("selected_chain","rules_version"):
  if report.get(f)!=exp[f]: errors.append(f+" mismatch")
 actual={r.get("chain_id"):{k:r.get(k) for k in ("eligible","requested_claim","robust_cvar","artifact_ids")} for r in report.get("chains",[]) if isinstance(r,dict)}
 expected={k:{x:v[x] for x in ("eligible","requested_claim","robust_cvar","artifact_ids")} for k,v in exp["chains"].items()}
 if actual!=expected: errors.append("chains mismatch")
 rows=list(csv.DictReader((submission/"handoff.tsv").open(newline=""),delimiter="\t")); required={"artifact_id","chain_id","stage","upstream_hash","content_hash","claim_permission","status"}
 if not rows or not required.issubset(rows[0]): errors.append("handoff schema incomplete")
 if sorted(r.get("artifact_id") for r in rows)!=sorted(exp["entities"]): errors.append("handoff coverage mismatch")
 review=(submission/"audit.md").read_text().lower()
 for term in ("claim permission","upstream hash","inventory","human review","stop","not experimental proof"):
  if term not in review: errors.append("audit missing "+term)
 manifest=json.loads((submission/"manifest.json").read_text())
 hashes=manifest.get("input_sha256",manifest.get("hashes"))
 if hashes is None and all(k in manifest for k in exp["hashes"]): hashes={k:manifest[k] for k in exp["hashes"]}
 if hashes!=exp["hashes"] or manifest.get("rules_version")!=exp["rules_version"] or manifest.get("deterministic") is not True: errors.append("manifest provenance mismatch")
 return not errors,errors
if __name__=="__main__":
 p=argparse.ArgumentParser();p.add_argument("--submission",type=Path,required=True);p.add_argument("--data",type=Path,required=True);p.add_argument("--reference",type=Path,required=True);a=p.parse_args();ok,errors=verify(a.submission,a.data,a.reference);print(json.dumps({"passed":ok,"errors":errors}));raise SystemExit(0 if ok else 1)
'''

def main():
 write(TASK/"data/case.json", {"kind":"cross_stage_chain","artifacts":ARTIFACTS,"chains":CHAINS}); write(TASK/"data/rules.json",RULES); write(TASK/"verifier.py",VERIFIER); write(TASK/"verifier_only/reference.json",{"selected_chain":"CHAIN-A","rules_version":RULES["rules_version"],"status":"verifier_only"})
 write(TASK/"instruction.md", """# Cross-stage claim and provenance chain audit\n\nUse only the supplied offline JSON files. Evaluate every chain in order: recovery -> normalization -> route -> policy. A chain is eligible only when every artifact is active, schema/status pass, reported hash equals content hash, every upstream hash equals the previous content hash, normalization sensitivity is stable, route reservation is reserved with the required evidence quorum, policy has no future-outcome leakage and requires human review, and robust_cvar meets the threshold. The requested claim level must not exceed the minimum claim permission across all four artifacts.\n\nSelect by highest robust_cvar, then ascending chain_id. Ineligible chains cannot be selected. Round computed values to six decimal places.\n\nWrite exactly four artifacts: `outputs/chain.json` with selected_chain, rules_version and every chain record; `outputs/handoff.tsv` with one row for every artifact and columns artifact_id, chain_id, stage, upstream_hash, content_hash, claim_permission and status; `outputs/audit.md` explaining claim permission, upstream hash, inventory, human review, stop conditions and why this is not experimental proof; and `outputs/manifest.json` with hashes for case.json and rules.json, rules_version and deterministic=true.\n""")
 write(TASK/"task.yaml", f'''id: {TASK_ID}\nversion: "0.9.0"\nstatus: ready_for_calibration\ntitle: "Cross-stage claim and provenance chain audit"\ndomain: biomedical_enterprise\nagent_visible_inputs:\n  - path: data/\n    format: JSON handoff graph\nconstraints:\n  network: off\nrequired_outputs:\n  - {{id: chain, path: outputs/chain.json, required_fields: [selected_chain, rules_version, chains]}}\n  - {{id: handoff, path: outputs/handoff.tsv, required_fields: [artifact_id, chain_id, stage, upstream_hash, claim_permission]}}\n  - {{id: audit, path: outputs/audit.md, required_fields: [claim_permission, upstream_hash, inventory, human_review]}}\n  - {{id: manifest, path: outputs/manifest.json, required_fields: [input_sha256, rules_version, deterministic]}}\nhidden_truth:\n  path: verifier_only/reference.json\n  status: verifier_only\n''')
 write(TASK/"scenario-card.yaml", f'''scenario_id: {TASK_ID}\nstatus: ready\nsource_scenarios: [L4-TRANCHE-001]\ndomain: biomedical_enterprise\nscientific_decision: authorize a cross-stage handoff without inflating claims\nscientific_judgments:\n  - provenance_chain_integrity\n  - claim_permission_intersection\n  - robust_policy_handoff_gate\ndifficulty_modules:\n  - id: horizon_end_to_end_claim\n    observable: four ordered stage artifacts are joined through upstream hashes\n    decision_flip: one broken link blocks a chain despite locally valid artifacts\n  - id: judgment_claim_permission_lattice\n    observable: requested claim is bounded by the weakest stage permission\n    decision_flip: a descriptive-only stage prevents an associational handoff\n  - id: data_evidence_graph_join\n    observable: IDs, hashes, versions and stages remain aligned\n    decision_flip: cross-chain hash substitution invalidates a high-score chain\n  - id: tool_version_and_interface_drift\n    observable: schema/status and version transitions are checked at each handoff\n    decision_flip: stale interface blocks propagation\n  - id: math_robust_scenario_optimization\n    observable: robust policy threshold is applied after provenance and safety gates\n    decision_flip: high-CVaR chain with inventory conflict cannot win\nworkflow_handoffs:\n  - from: recovery_normalization_route_policy\n    to: bounded_handoff_decision\n    artifact: outputs/chain.json\n    invariant: no claim, hash or resource permission increases downstream\nrelease_gates:\n  scientific_reality: pass\n  observability: pass\n  verifiability: pass\n  naive_resistance: pass\n  reproducibility: pass\n  enterprise_value: pending\n  training_value: not_run\n''')
 write(TASK/"quality/difficulty_card.json",{"difficulty_card_id":"DIFF-EB012-CROSS-STAGE-CHAIN-002-001","task_id":TASK_ID,"primary_module":"horizon_end_to_end_claim","secondary_modules":["judgment_claim_permission_lattice","data_evidence_graph_join"],"held_out_variants":["hash substitution","claim downgrade","inventory conflict"],"decision_flip_controls":["broken upstream hash blocks chain","weakest permission blocks claim","resource conflict blocks high CVaR"],"status":"REVIEW_REQUIRED"})
 write(TASK/"quality/control_plan_card.json",{"control_plan_id":"CONTROL-EB012-CROSS-STAGE-CHAIN-002-001","task_id":TASK_ID,"controls":[{"control_id":"positive-reference","kind":"positive"},{"control_id":"negative-hash-substitution","kind":"negative"},{"control_id":"invariance-artifact-order","kind":"invariance"},{"control_id":"insufficient-manifest","kind":"insufficient_evidence"},{"control_id":"adversarial-high-cvar-conflict","kind":"adversarial"},{"control_id":"metamorphic-chain-order","kind":"metamorphic"}],"single_factor_policy":True,"calibration_status":"NOT_RUN","status":"REVIEW_REQUIRED"})
 write(TASK/"quality/model_trial_card.json",{"model_trial_card_id":"TRIAL-EB012-CROSS-STAGE-CHAIN-002-001","task_id":TASK_ID,"protocol_version":"enterprise-model-trial.v1","strategies":["reference_solution","simple_legal_baseline","always_abstain","template_or_keyword","target_model"],"target_model_status":"NOT_RUN","status":"NOT_RUN","run_records":[]}); write(TASK/"quality/model_trial_results.json",{"task_id":TASK_ID,"protocol_version":"enterprise-model-trial.v1","status":"NOT_RUN","target_model_status":"NOT_RUN","records":[]})
 write(TASK/"quality/independent_verifier_audit.json",{"audit_id":"AUDIT-EB012-CROSS-STAGE-CHAIN-002-001","task_id":TASK_ID,"review_status":"not_run","status":"REVIEW_REQUIRED"}); write(TASK/"quality/contract_audit.json",{"schema_version":"enterprise_contract_audit.v1","task_id":TASK_ID,"status":"PASS","checks":[{"output":x,"path_declared":True,"schema_declared":True,"claim_boundary_declared":True} for x in ["outputs/chain.json","outputs/handoff.tsv","outputs/audit.md","outputs/manifest.json"]]}); write(TASK/"quality/sop_card.json",{"schema_version":"enterprise_harbor_sop_card.v1","task_id":TASK_ID,"sop_version":"enterprise-harbor-sop-v1.2","source_status":"REVIEW_REQUIRED","contract_status":"MATERIALIZED_V0.9.0","control_status":"NOT_RUN","model_trial_status":"NOT_RUN","independent_verifier_status":"NOT_RUN","release_status":"BLOCKED","release_blockers":["controls","baselines","independent verifier audit","target-model trial","fixed-container replay","practitioner review"]})
 write(TASK/"tests/test_verifier.py",'''import importlib.util, json\nfrom pathlib import Path\nROOT=Path(__file__).resolve().parents[1]\nspec=importlib.util.spec_from_file_location("verifier",ROOT/"verifier.py"); verifier=importlib.util.module_from_spec(spec); assert spec and spec.loader; spec.loader.exec_module(verifier)\ndef test_oracle_selects_provenance_safe_chain():\n    exp=verifier.expected(ROOT/"data"); assert exp["selected_chain"]=="CHAIN-A"; assert exp["chains"]["CHAIN-B"]["blockers"]==["hash","upstream_hash"]; assert "inventory_or_quorum" in exp["chains"]["CHAIN-C"]["blockers"]; assert "claim_boundary" in exp["chains"]["CHAIN-D"]["blockers"]\ndef test_reference_matches_oracle():\n    exp=verifier.expected(ROOT/"data"); ref=json.loads((ROOT/"verifier_only/reference.json").read_text()); assert ref["selected_chain"]==exp["selected_chain"]\n''')

if __name__ == "__main__":
 main()
 scenario = TASK / "scenario-card.yaml"
 scenario.write_text(scenario.read_text(encoding="utf-8").replace("source_scenarios: [L4-TRANCHE-001]", "source_scenarios: [L4-TRANCHE-001, L5.4-TRANCHE-010]"), encoding="utf-8")
 write(TASK/"quality/candidate_set_card.json", {"candidate_set_id":"CSET-EB012-CROSS-STAGE-CHAIN-002-001", "source_benchmark_id":"L5.4-TRANCHE-010", "candidates":[{"candidate_id":TASK_ID,"selection_status":"MATERIALIZED","semantic_axes":["cross_stage_handoff","claim_lattice","resource_constrained_policy"]}], "selection_gate":{"minimum_candidates":3,"maximum_candidates":5,"require_two_semantic_differences":True,"require_independent_review":True}, "status":"REVIEW_REQUIRED"})
 write(TASK/"quality/enterprise_value_card.json", {"enterprise_value_card_id":"VALUE-EB012-CROSS-STAGE-CHAIN-002-001", "task_id":TASK_ID, "enterprise_reality":{"decision":"authorize downstream consumption only when the cross-stage handoff is coherent","downstream_action":"decision->review->handoff","error_consequence":"a locally attractive result can corrupt a downstream scientific decision","human_owner":"domain_reviewer"}, "status":"REVIEW_REQUIRED"})
 write(TASK/"quality/training_value_card.json", {"training_value_card_id":"TRAIN-EB012-CROSS-STAGE-CHAIN-002-001", "task_id":TASK_ID, "capability_targets":["cross-stage evidence reconciliation","claim boundary enforcement","resource-aware policy selection","abstention"], "error_labels":["input_understanding","method_choice","calculation_or_tool","claim_overreach","delivery_failure"], "training_use":"EVAL_ONLY_UNTIL_CALIBRATED", "status":"REVIEW_REQUIRED"})
