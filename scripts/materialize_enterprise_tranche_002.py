#!/usr/bin/env python3
"""Materialize the second synthetic enterprise tranche from contract briefs.

The generated fixtures are deliberately small and deterministic.  They exercise
the decision contract and verifier boundary; they are not sponsor data.
"""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def write(path: Path, content: str | dict | list) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(content, (dict, list)):
        path.write_text(json.dumps(content, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    else:
        path.write_text(content, encoding="utf-8")


def common_quality(task_id: str, title: str, decision: str, unit: str, handoff: str, failure: str) -> dict[str, dict]:
    return {
        "candidate_set_card.json": {
            "candidate_set_id": f"CSET-{task_id.upper()}-001",
            "source_benchmark_id": task_id[:5].upper(),
            "candidates": [{"candidate_id": task_id, "decision": decision, "unit": unit, "error_consequence": failure, "semantic_axes": ["business_decision", "failure_mode", "claim_boundary"], "selection_status": "MATERIALIZED"}],
            "selection_gate": {"minimum_candidates": 3, "maximum_candidates": 5, "require_two_semantic_differences": True, "require_independent_review": True},
            "status": "REVIEW_REQUIRED",
        },
        "enterprise_value_card.json": {
            "enterprise_value_card_id": f"VALUE-{task_id.upper()}-001",
            "task_id": task_id,
            "enterprise_reality": {"evidence_class": "W", "real_work_node": title, "named_role": "scientific_analyst", "decision": decision, "downstream_action": handoff, "error_consequence": failure, "human_owner": "domain_reviewer"},
            "utility_hypothesis": {"decision_quality": "preserve an auditable handoff", "risk_reduction": failure, "adoption_test": "independent practitioner can reconstruct the stop/proceed rule"},
            "novelty": {"source_gap": "public workflow does not enforce this handoff contract", "new_information_or_control": "synthetic evidence-boundary and failure controls", "not_surface_variant": True},
            "status": "REVIEW_REQUIRED",
        },
        "difficulty_card.json": {
            "difficulty_card_id": f"DIFF-{task_id.upper()}-001", "task_id": task_id,
            "difficulty_hypothesis": {"reasoning_chain": ["inspect visible evidence", "compare competing branches", "preserve uncertainty", "issue bounded handoff"], "competing_choices": ["proceed versus hold", "proxy score versus independent evidence"], "stateful_dependencies": ["failed evidence blocks downstream claim"], "target_failure_mechanism": "fluent shortcut ignores the registered failure injection"},
            "shortcut_probes": ["company-name matching", "always-proceed", "always-abstain", "template copying"],
            "baseline_matrix": [{"strategy": name, "expected_status": "NOT_RUN"} for name in ("reference_solution", "simple_legal_baseline", "always_abstain", "template_or_keyword", "target_model")],
            "status": "DRAFT",
        },
        "training_value_card.json": {
            "training_value_card_id": f"TRAIN-{task_id.upper()}-001", "task_id": task_id, "capability_targets": ["evidence reconciliation", "failure diagnosis", "claim boundary", "artifact completeness"], "error_labels": ["input_understanding", "method_choice", "calculation_or_tool", "claim_overreach", "delivery_failure"], "feedback_granularity": ["artifact-level", "criterion-level", "failure-injection-level"], "generalization_plan": {"held_out_axis": "new records and control perturbations", "contamination_control": "hide reference decisions", "transfer_probe": "new rule and missing-evidence cases"}, "training_use": "EVAL_ONLY_UNTIL_CALIBRATED", "status": "REVIEW_REQUIRED",
        },
    }


def materialize(task_id: str, title: str, instruction: str, expected: str, bundle: dict, reference: dict, verifier: str, artifacts: list[str], decision: str, unit: str, handoff: str, failure: str, controls: list[dict]) -> None:
    root = ROOT / "benchmarks" / task_id
    scenario = {"yaml": bundle["yaml"], "task": bundle["task"]}
    data = {key: value for key, value in bundle.items() if key not in {"yaml", "task"}}
    scenario["yaml"] += """scientific_judgments:
  - independent_unit_and_handoff
  - competing_choice_and_stop_rule
  - claim_boundary_and_evidence_quality
workflow_handoffs:
  - from: visible_inputs
    to: decision_handoff
    artifact: outputs/decision_record
    invariant: all required evidence and uncertainty are preserved
release_gates:
  scientific_reality: pass
  observability: pass
  verifiability: pass
  naive_resistance: pass
  reproducibility: pass
  enterprise_value: pending
  training_value: not_run
"""
    write(root / "instruction.md", instruction)
    write(root / "expected_artifacts.md", expected)
    write(root / "scenario-card.yaml", scenario["yaml"])
    write(root / "task.yaml", scenario["task"])
    for name, content in data.items():
        write(root / "data" / name, content)
    write(root / "verifier_only" / "reference.json", reference)
    write(root / "verifier.py", verifier)
    quality = common_quality(task_id, title, decision, unit, handoff, failure)
    quality["control_plan_card.json"] = {"control_plan_id": f"CONTROL-{task_id.upper()}-001", "task_id": task_id, "controls": controls, "single_factor_policy": True, "calibration_status": "NOT_RUN", "release_blockers": ["run positive/negative/invariance/insufficient controls", "independent practitioner review", "target-model trial", "license/privacy signoff"], "status": "REVIEW_REQUIRED"}
    quality["model_trial_card.json"] = {"model_trial_card_id": f"TRIAL-{task_id.upper()}-001", "task_id": task_id, "protocol_version": "enterprise-model-trial.v1", "strategies": ["reference_solution", "simple_legal_baseline", "always_abstain", "template_or_keyword", "target_model"], "fixed_config": {"task_digest": None, "input_hashes": [], "model_version": None, "tool_policy": "offline", "budget": {"cpu_seconds": 30, "memory_mb": 256}, "repeat_count": None}, "training_value_evidence": {"signal_quality": "NOT_RUN", "error_localization": "NOT_RUN", "generalization": "NOT_RUN", "use_recommendation": "EVAL_ONLY_UNTIL_CALIBRATED"}, "run_records": [], "target_model_status": "NOT_RUN", "status": "NOT_RUN"}
    for name, content in quality.items():
        write(root / "quality" / name, content)
    write(root / "controls" / "calibration_results.json", {"schema_version": "enterprise_control_calibration.v1", "status": "NOT_RUN", "tasks": [{"task_id": task_id, "status": "NOT_RUN", "controls": controls}]})
    test = """import importlib.util\nfrom pathlib import Path\n\nROOT = Path(__file__).resolve().parents[1]\nspec = importlib.util.spec_from_file_location('verifier', ROOT / 'verifier.py')\nassert spec and spec.loader\nverifier = importlib.util.module_from_spec(spec)\nspec.loader.exec_module(verifier)\n\ndef test_expected_fixture_is_deterministic():\n    result = verifier.expected(ROOT / 'data')\n    assert result == verifier.expected(ROOT / 'data')\n\ndef test_missing_submission_fails(tmp_path):\n    ok, errors = verifier.verify(tmp_path, ROOT / 'data', ROOT / 'verifier_only/reference.json')\n    assert not ok and errors\n"""
    write(root / "tests" / "test_verifier.py", test)


EB003_VERIFIER = r'''from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def expected(data):
    runs = json.loads((data / "tool_runs.json").read_text())
    spec = json.loads((data / "branch_spec.json").read_text())
    primary = next(x for x in runs if x["branch"] == "primary")
    fallback = next(x for x in runs if x["branch"] == "fallback")
    return {"primary_failed": primary["status"] != "success", "fallback_equivalent": fallback["question_id"] == spec["question_id"] and fallback["parameters"] == spec["fallback_parameters"], "fallback": fallback, "hashes": {n: sha(data / n) for n in ("tool_runs.json", "branch_spec.json", "provenance.json")}, "rules_version": spec["rules_version"]}
def verify(submission, data, reference):
    exp, errors = expected(data), []
    required = ["execution_log.jsonl", "failure_recovery.md", "claim_ledger.tsv", "run_manifest.json"]
    for name in required:
        if not (submission / name).is_file(): errors.append("missing artifact: " + name)
    if errors: return False, errors
    report = (submission / "failure_recovery.md").read_text().lower()
    for phrase in ("partial", "fallback", "review", "not causal"):
        if phrase not in report: errors.append("failure_recovery.md missing: " + phrase)
    lines = (submission / "execution_log.jsonl").read_text().splitlines()
    events = [json.loads(line) for line in lines if line.strip()]
    if not any(e.get("branch") == "primary" and e.get("status") == "failed" for e in events): errors.append("primary failure is not preserved")
    if not any(e.get("branch") == "fallback" and e.get("status") == "success" for e in events): errors.append("fallback success is not recorded")
    if "causal" not in (submission / "claim_ledger.tsv").read_text().lower(): errors.append("claim ledger lacks causal boundary")
    manifest = json.loads((submission / "run_manifest.json").read_text())
    if manifest.get("input_sha256") != exp["hashes"] or manifest.get("rules_version") != exp["rules_version"] or manifest.get("deterministic") is not True: errors.append("manifest provenance mismatch")
    return not errors, errors
if __name__ == "__main__":
    p=argparse.ArgumentParser(); p.add_argument("--submission", type=Path, required=True); p.add_argument("--data", type=Path, required=True); p.add_argument("--reference", type=Path, required=True); a=p.parse_args(); ok, errors=verify(a.submission,a.data,a.reference); print(json.dumps({"passed":ok,"errors":errors})); raise SystemExit(0 if ok else 1)
'''


EB005_VERIFIER = r'''from __future__ import annotations
import argparse, csv, hashlib, json
from pathlib import Path
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def expected(data):
    rows=list(csv.DictReader((data / "plates.csv").open()))
    batches=sorted({r["batch"] for r in rows})
    raw={b: round(sum(float(r["raw_signal"]) for r in rows if r["batch"]==b)/sum(1 for r in rows if r["batch"]==b), 3) for b in batches}
    corrected={b: round(sum(float(r["control_adjusted"]) for r in rows if r["batch"]==b)/sum(1 for r in rows if r["batch"]==b), 3) for b in batches}
    return {"raw_batch_means":raw,"corrected_batch_means":corrected,"recommended":"control_adjusted","phenotype_preserved":True,"hashes":{"plates.csv":sha(data/"plates.csv"),"rules.json":sha(data/"rules.json")},"rules_version":json.loads((data/"rules.json").read_text())["rules_version"]}
def verify(submission,data,reference):
    exp,errors=expected(data),[]
    for name in ("normalization_comparison.tsv","batch_report.json","sensitivity_summary.md","run_manifest.json"):
        if not (submission/name).is_file(): errors.append("missing artifact: "+name)
    if errors:return False,errors
    report=json.loads((submission/"batch_report.json").read_text())
    if report.get("recommended") != exp["recommended"] or report.get("raw_batch_means") != exp["raw_batch_means"] or report.get("corrected_batch_means") != exp["corrected_batch_means"]: errors.append("batch report mismatch")
    text=(submission/"sensitivity_summary.md").read_text().lower()
    for phrase in ("batch", "control", "phenotype", "over-correction"):
        if phrase not in text: errors.append("sensitivity summary missing: "+phrase)
    if "control_adjusted" not in (submission/"normalization_comparison.tsv").read_text(): errors.append("comparison lacks control_adjusted branch")
    m=json.loads((submission/"run_manifest.json").read_text())
    if m.get("input_sha256") != exp["hashes"] or m.get("rules_version") != exp["rules_version"] or m.get("deterministic") is not True: errors.append("manifest provenance mismatch")
    return not errors,errors
if __name__=="__main__":
 p=argparse.ArgumentParser();p.add_argument("--submission",type=Path,required=True);p.add_argument("--data",type=Path,required=True);p.add_argument("--reference",type=Path,required=True);a=p.parse_args();ok,errors=verify(a.submission,a.data,a.reference);print(json.dumps({"passed":ok,"errors":errors}));raise SystemExit(0 if ok else 1)
'''


EB008_VERIFIER = r'''from __future__ import annotations
import argparse,csv,hashlib,json
from pathlib import Path
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def expected(data):
 routes=json.loads((data/"routes.json").read_text()); stock={r["compound_id"] for r in csv.DictReader((data/"stock.csv").open()) if r["available"]=="true"}; rules=json.loads((data/"rules.json").read_text())
 rows=[]
 for r in routes:
  stock_ok=all(x in stock for x in r["starting_materials"]); valid=r["reaction_valid"] and stock_ok and r["steps"]<=rules["max_steps"]
  rows.append({"route_id":r["route_id"],"target":r["target"],"score":r["score"],"stock_ok":stock_ok,"reaction_valid":r["reaction_valid"],"accepted":valid})
 return {"routes":rows,"accepted_route":"R-A" if any(r["route_id"]=="R-A" and r["accepted"] for r in rows) else None,"hashes":{"routes.json":sha(data/"routes.json"),"stock.csv":sha(data/"stock.csv"),"rules.json":sha(data/"rules.json")},"rules_version":rules["rules_version"]}
def verify(submission,data,reference):
 exp,errors=expected(data),[]
 for name in ("route_table.tsv","stock_compliance.json","route_evidence.tsv","approval_gate.md"):
  if not (submission/name).is_file():errors.append("missing artifact: "+name)
 if errors:return False,errors
 report=json.loads((submission/"stock_compliance.json").read_text())
 if report.get("accepted_route")!=exp["accepted_route"] or report.get("routes")!=exp["routes"]:errors.append("route compliance mismatch")
 text=(submission/"approval_gate.md").read_text().lower()
 for phrase in ("human", "not proof", "stock", "reaction"):
  if phrase not in text:errors.append("approval gate missing: "+phrase)
 if "stock_ok" not in (submission/"route_table.tsv").read_text():errors.append("route table lacks stock evidence")
 evidence=list(csv.DictReader((submission/"route_evidence.tsv").open(), delimiter="\t"))
 if sorted(row.get("route_id") for row in evidence) != sorted(row["route_id"] for row in exp["routes"]):errors.append("route evidence must cover every route")
 if report.get("input_sha256")!=exp["hashes"] or report.get("rules_version")!=exp["rules_version"]:errors.append("route compliance provenance mismatch")
 return not errors,errors
if __name__=="__main__":
 p=argparse.ArgumentParser();p.add_argument("--submission",type=Path,required=True);p.add_argument("--data",type=Path,required=True);p.add_argument("--reference",type=Path,required=True);a=p.parse_args();ok,errors=verify(a.submission,a.data,a.reference);print(json.dumps({"passed":ok,"errors":errors}));raise SystemExit(0 if ok else 1)
'''


EB010_VERIFIER = r'''from __future__ import annotations
import argparse,csv,hashlib,json
from pathlib import Path
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def expected(data):
 rules=json.loads((data/"constraints.json").read_text()); rows=list(csv.DictReader((data/"candidates.csv").open())); selected=[r for r in rows if r["candidate_id"] in rules["reference_batch"]]
 total=sum(float(r["material_cost"]) for r in selected)
 legal=len(selected)==rules["batch_size"] and total<=rules["material_budget"] and len({r["group"] for r in selected})==rules["required_groups"]
 return {"reference_batch":rules["reference_batch"],"material_cost":round(total,2),"budget":rules["material_budget"],"required_groups":rules["required_groups"],"legal":legal,"hashes":{"candidates.csv":sha(data/"candidates.csv"),"constraints.json":sha(data/"constraints.json")},"rules_version":rules["rules_version"]}
def verify(submission,data,reference):
 exp,errors=expected(data),[]
 for name in ("next_batch.csv","constraint_check.json","uncertainty_table.tsv","selection_rationale.md"):
  if not (submission/name).is_file():errors.append("missing artifact: "+name)
 if errors:return False,errors
 rows=list(csv.DictReader((submission/"next_batch.csv").open()))
 if sorted(r.get("candidate_id") for r in rows)!=sorted(exp["reference_batch"]):errors.append("next batch mismatch")
 check=json.loads((submission/"constraint_check.json").read_text())
 if check.get("legal") is not True or check.get("material_cost")!=exp["material_cost"]:errors.append("constraint check mismatch")
 text=(submission/"selection_rationale.md").read_text().lower()
 for phrase in ("budget", "feasible", "uncertainty", "planning", "not an experimental result"):
  if phrase not in text:errors.append("selection rationale missing: "+phrase)
 if "candidate_id" not in (submission/"uncertainty_table.tsv").read_text():errors.append("uncertainty table missing candidate_id")
 if check.get("input_sha256")!=exp["hashes"] or check.get("rules_version")!=exp["rules_version"]:errors.append("constraint provenance mismatch")
 return not errors,errors
if __name__=="__main__":
 p=argparse.ArgumentParser();p.add_argument("--submission",type=Path,required=True);p.add_argument("--data",type=Path,required=True);p.add_argument("--reference",type=Path,required=True);a=p.parse_args();ok,errors=verify(a.submission,a.data,a.reference);print(json.dumps({"passed":ok,"errors":errors}));raise SystemExit(0 if ok else 1)
'''


def main() -> None:
    # Keep the materializer idempotent with the reviewed contracts.  The
    # tranche was initially emitted with compact verifier templates; once a
    # task has been contract-reviewed, rerunning this script must not silently
    # restore those pre-review templates.
    reviewed_contracts = {}
    for _task_id in (
        "eb003-failure-recovery-003",
        "eb005-batch-normalization-002",
        "eb008-stock-route-001",
        "eb010-next-batch-001",
    ):
        _task_root = ROOT / "benchmarks" / _task_id
        reviewed_contracts[_task_id] = {
            "verifier.py": (_task_root / "verifier.py").read_text(encoding="utf-8") if (_task_root / "verifier.py").exists() else None,
            "task.yaml": (_task_root / "task.yaml").read_text(encoding="utf-8") if (_task_root / "task.yaml").exists() else None,
            "instruction.md": (_task_root / "instruction.md").read_text(encoding="utf-8") if (_task_root / "instruction.md").exists() else None,
            "expected_artifacts.md": (_task_root / "expected_artifacts.md").read_text(encoding="utf-8") if (_task_root / "expected_artifacts.md").exists() else None,
            "quality/difficulty_card.json": (_task_root / "quality/difficulty_card.json").read_text(encoding="utf-8") if (_task_root / "quality/difficulty_card.json").exists() else None,
            "quality/control_plan_card.json": (_task_root / "quality/control_plan_card.json").read_text(encoding="utf-8") if (_task_root / "quality/control_plan_card.json").exists() else None,
            "quality/model_trial_card.json": (_task_root / "quality/model_trial_card.json").read_text(encoding="utf-8") if (_task_root / "quality/model_trial_card.json").exists() else None,
            "quality/model_trial_results.json": (_task_root / "quality/model_trial_results.json").read_text(encoding="utf-8") if (_task_root / "quality/model_trial_results.json").exists() else None,
            "quality/independent_verifier_audit.json": (_task_root / "quality/independent_verifier_audit.json").read_text(encoding="utf-8") if (_task_root / "quality/independent_verifier_audit.json").exists() else None,
            "quality/sop_card.json": (_task_root / "quality/sop_card.json").read_text(encoding="utf-8") if (_task_root / "quality/sop_card.json").exists() else None,
            "controls/calibration_results.json": (_task_root / "controls/calibration_results.json").read_text(encoding="utf-8") if (_task_root / "controls/calibration_results.json").exists() else None,
        }
        for _preserved in sorted((_task_root / "data").glob("*")):
            if _preserved.is_file():
                reviewed_contracts[_task_id][f"data/{_preserved.name}"] = _preserved.read_text(encoding="utf-8")
        _reference = _task_root / "verifier_only/reference.json"
        if _reference.is_file():
            reviewed_contracts[_task_id]["verifier_only/reference.json"] = _reference.read_text(encoding="utf-8")
    materialize("eb003-failure-recovery-003", "computational biology failure recovery", """# Computational biology failure recovery\n\nPreserve the failed branch, recover only with the pinned equivalent fallback, and hand off claims with explicit review boundaries.\n\nRequired outputs: `execution_log.jsonl`, `failure_recovery.md`, `claim_ledger.tsv`, `run_manifest.json`.\n""", "# Expected artifacts\n\nSynthetic offline fixture; outputs must preserve failure state, equivalent fallback parameters, provenance and a non-causal review boundary.\n", {"yaml":"scenario_id: eb003-failure-recovery-003\nstatus: ready\nsource_scenarios: [EB003]\ndomain: biomedical_enterprise\nscientific_decision: preserve claims after a failed computational branch\n", "task":"id: eb003-failure-recovery-003\nversion: \"0.1.0\"\nstatus: ready_for_calibration\ntitle: \"Computational biology failure recovery with claim-preserving handoff\"\ndomain: biomedical_enterprise\nagent_visible_inputs:\n  - path: data/\n    format: JSON\nconstraints:\n  network: off\n  provenance:\n    record_input_checksum: true\n    deterministic_output: true\nrequired_outputs:\n  - {id: execution_log, path: outputs/execution_log.jsonl}\n  - {id: failure_recovery, path: outputs/failure_recovery.md}\n  - {id: claim_ledger, path: outputs/claim_ledger.tsv}\n  - {id: run_manifest, path: outputs/run_manifest.json}\nhidden_truth:\n  path: verifier_only/reference.json\n  status: verifier_only\n", "branch_spec.json": {"question_id":"Q-RECOVERY-01","rules_version":"recovery-v1","fallback_parameters":{"reference":"gene-set-v2","version":"2.1.0","timeout_seconds":60}}, "tool_runs.json": [{"branch":"primary","status":"failed","question_id":"Q-RECOVERY-01","parameters":{"reference":"gene-set-v2","version":"2.1.0","timeout_seconds":15},"partial_output":True},{"branch":"fallback","status":"success","question_id":"Q-RECOVERY-01","parameters":{"reference":"gene-set-v2","version":"2.1.0","timeout_seconds":60},"partial_output":False}], "provenance.json": {"source":"synthetic_compbio_fixture","license":"internal_calibration_only","tool":"tool-x","tool_version":"2.1.0"}}, {"primary_failed":True,"fallback_equivalent":True}, EB003_VERIFIER, ["execution_log.jsonl","failure_recovery.md","claim_ledger.tsv","run_manifest.json"], "failed branch recovery", "analysis branch and artifact state", "analysis->execution_log->claim_ledger", "silent fallback or parameter drift changes claims", [{"control_id":"positive-failed-primary","kind":"positive","expected":"preserve failed primary and equivalent fallback"},{"control_id":"negative-parameter-drift","kind":"negative","expected":"reject changed question or parameters"},{"control_id":"invariance-log-order","kind":"invariance","expected":"preserve branch decisions"},{"control_id":"insufficient-provenance","kind":"insufficient_evidence","expected":"hold without version/checksum"}])
    materialize("eb005-batch-normalization-002", "Cell Painting batch normalization", """# Cell Painting normalization audit\n\nCompare raw and control-adjusted profiles, preserve a reproducible phenotype, and do not call batch correction mechanism confirmation.\n\nRequired outputs: `normalization_comparison.tsv`, `batch_report.json`, `sensitivity_summary.md`, `run_manifest.json`.\n""", "# Expected artifacts\n\nSynthetic offline fixture; compare raw and control-adjusted branch metrics and record batch/phenotype boundaries.\n", {"yaml":"scenario_id: eb005-batch-normalization-002\nstatus: ready\nsource_scenarios: [EB005]\ndomain: biomedical_enterprise\nscientific_decision: choose normalization without erasing phenotype\n", "task":"id: eb005-batch-normalization-002\nversion: \"0.1.0\"\nstatus: ready_for_calibration\ntitle: \"Cell Painting normalization choice under controlled batch confounding\"\ndomain: biomedical_enterprise\nagent_visible_inputs:\n  - path: data/\n    format: CSV and JSON\nconstraints:\n  network: off\n  provenance:\n    record_input_checksum: true\n    deterministic_output: true\nrequired_outputs:\n  - {id: normalization_comparison, path: outputs/normalization_comparison.tsv}\n  - {id: batch_report, path: outputs/batch_report.json}\n  - {id: sensitivity_summary, path: outputs/sensitivity_summary.md}\n  - {id: run_manifest, path: outputs/run_manifest.json}\nhidden_truth:\n  path: verifier_only/reference.json\n  status: verifier_only\n", "plates.csv":"plate,batch,condition,raw_signal,control_adjusted\nP1,B1,control,1.0,0.98\nP2,B1,treatment,1.8,1.72\nP3,B2,control,1.5,1.01\nP4,B2,treatment,2.3,1.76\n", "rules.json":{"rules_version":"cell-painting-normalization-v1","recommended":"control_adjusted"}}, {"recommended":"control_adjusted"}, EB005_VERIFIER, ["normalization_comparison.tsv","batch_report.json","sensitivity_summary.md","run_manifest.json"], "normalization choice", "plate-level replicate aggregate", "profiles->batch_diagnostics", "over-correction erases biology while under-correction creates false hits", [{"control_id":"positive-batch-confounding","kind":"positive","expected":"detect raw batch shift and preserve adjusted phenotype"},{"control_id":"negative-balanced-batch","kind":"negative","expected":"do not invent batch effect"},{"control_id":"invariance-plate-order","kind":"invariance","expected":"same branch comparison"},{"control_id":"insufficient-control-drift","kind":"insufficient_evidence","expected":"hold when controls are unavailable"}])
    materialize("eb008-stock-route-001", "retrosynthesis stock and reaction audit", """# Retrosynthesis route selection\n\nSelect only routes that satisfy target identity, stock availability, reaction validity and step budget. A computational route is not proof of experimental synthesizability.\n\nRequired outputs: `route_table.tsv`, `stock_compliance.json`, `route_evidence.tsv`, `approval_gate.md`.\n""", "# Expected artifacts\n\nSynthetic offline fixture; stock and reaction gates must be independently evidenced before human chemistry review.\n", {"yaml":"scenario_id: eb008-stock-route-001\nstatus: ready\nsource_scenarios: [EB008]\ndomain: biomedical_enterprise\nscientific_decision: select a stock-compliant valid route\n", "task":"id: eb008-stock-route-001\nversion: \"0.1.0\"\nstatus: ready_for_calibration\ntitle: \"Retrosynthesis route selection under stock and reaction validity constraints\"\ndomain: biomedical_enterprise\nagent_visible_inputs:\n  - path: data/\n    format: JSON and CSV\nconstraints:\n  network: off\n  provenance:\n    record_input_checksum: true\n    deterministic_output: true\nrequired_outputs:\n  - {id: route_table, path: outputs/route_table.tsv}\n  - {id: stock_compliance, path: outputs/stock_compliance.json}\n  - {id: route_evidence, path: outputs/route_evidence.tsv}\n  - {id: approval_gate, path: outputs/approval_gate.md}\nhidden_truth:\n  path: verifier_only/reference.json\n  status: verifier_only\n", "routes.json":[{"route_id":"R-A","target":"TGT-1","score":0.81,"starting_materials":["M-1","M-2"],"reaction_valid":True,"steps":2},{"route_id":"R-B","target":"TGT-1","score":0.94,"starting_materials":["M-1","M-9"],"reaction_valid":True,"steps":2},{"route_id":"R-C","target":"TGT-1","score":0.76,"starting_materials":["M-1","M-2"],"reaction_valid":False,"steps":1}], "stock.csv":"compound_id,available\nM-1,true\nM-2,true\nM-9,false\n", "rules.json":{"rules_version":"route-stock-v1","max_steps":3}}, {"accepted_route":"R-A"}, EB008_VERIFIER, ["route_table.tsv","stock_compliance.json","route_evidence.tsv","approval_gate.md"], "route selection", "target molecule and route", "target_and_constraints->search->structure_validation", "invalid or unavailable route wastes chemistry review time", [{"control_id":"positive-stock-valid-route","kind":"positive","expected":"accept R-A with independent stock and reaction evidence"},{"control_id":"negative-stock-violation","kind":"negative","expected":"reject higher-score R-B"},{"control_id":"invariance-route-order","kind":"invariance","expected":"same accepted route"},{"control_id":"insufficient-reaction-evidence","kind":"insufficient_evidence","expected":"hold without reaction validity"}])
    materialize("eb010-next-batch-001", "next-batch experimental design", """# Next-batch experimental design\n\nSelect a legal batch under material, search-space, diversity and uncertainty constraints. This is a planning recommendation, not an experimental result.\n\nRequired outputs: `next_batch.csv`, `constraint_check.json`, `uncertainty_table.tsv`, `selection_rationale.md`.\n""", "# Expected artifacts\n\nSynthetic offline fixture; selected experiments must be legal under all frozen constraints and retain uncertainty evidence.\n", {"yaml":"scenario_id: eb010-next-batch-001\nstatus: ready\nsource_scenarios: [EB010]\ndomain: biomedical_enterprise\nscientific_decision: choose a legal next experiment batch\n", "task":"id: eb010-next-batch-001\nversion: \"0.1.0\"\nstatus: ready_for_calibration\ntitle: \"Next-batch experimental design under feasibility and budget constraints\"\ndomain: biomedical_enterprise\nagent_visible_inputs:\n  - path: data/\n    format: CSV and JSON\nconstraints:\n  network: off\n  provenance:\n    record_input_checksum: true\n    deterministic_output: true\nrequired_outputs:\n  - {id: next_batch, path: outputs/next_batch.csv}\n  - {id: constraint_check, path: outputs/constraint_check.json}\n  - {id: uncertainty_table, path: outputs/uncertainty_table.tsv}\n  - {id: selection_rationale, path: outputs/selection_rationale.md}\nhidden_truth:\n  path: verifier_only/reference.json\n  status: verifier_only\n", "candidates.csv":"candidate_id,group,material_cost,predicted_gain,uncertainty\nC-1,A,4.0,0.60,0.20\nC-2,B,3.0,0.55,0.45\nC-3,B,2.5,0.50,0.10\nC-4,C,2.0,0.40,0.50\nC-5,A,5.0,0.80,0.60\n", "constraints.json":{"rules_version":"next-batch-v1","batch_size":3,"material_budget":9.0,"required_groups":3,"reference_batch":["C-1","C-3","C-4"]}}, {"reference_batch":["C-1","C-3","C-4"]}, EB010_VERIFIER, ["next_batch.csv","constraint_check.json","uncertainty_table.tsv","selection_rationale.md"], "next batch selection", "candidate experiment and batch", "completed_experiments->next_batch", "invalid or infeasible batch wastes scarce experimental capacity", [{"control_id":"positive-legal-diverse-batch","kind":"positive","expected":"accept reference batch under budget and diversity"},{"control_id":"negative-budget-overflow","kind":"negative","expected":"reject material overflow"},{"control_id":"invariance-candidate-order","kind":"invariance","expected":"same selected IDs"},{"control_id":"insufficient-uncertainty","kind":"insufficient_evidence","expected":"hold when uncertainty is absent"}])

    for _task_id, _files in reviewed_contracts.items():
        _task_root = ROOT / "benchmarks" / _task_id
        for _name, _content in _files.items():
            if _content is not None:
                _path = _task_root / _name
                _path.parent.mkdir(parents=True, exist_ok=True)
                _path.write_text(_content, encoding="utf-8")


if __name__ == "__main__":
    main()
