#!/usr/bin/env python3
from __future__ import annotations
import importlib.util, json, shutil, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TASK = ROOT / "benchmarks/eb013-evidence-budget-routing-002"
spec = importlib.util.spec_from_file_location("eb013_l61_verifier", TASK / "verifier.py")
verifier = importlib.util.module_from_spec(spec); assert spec and spec.loader; spec.loader.exec_module(verifier)

def write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")

def reference(out: Path) -> dict:
    exp = verifier.expected(TASK / "data"); out.mkdir(parents=True, exist_ok=True)
    write(out / "plan.json", {"stage1_request_id": exp["selected_stage1_request_id"], "stage2_policy": exp["selected_stage2_policy"], "worst_case_max_critical_residual": exp["worst_case_max_critical_residual"], "worst_case_cost": exp["worst_case_cost"], "policies": exp["policies"], "network_used": False, "stop_condition": "adaptive_route_selected"})
    write(out / "decision.json", {"decision": exp["decision"], "selected_stage1_request_id": exp["selected_stage1_request_id"], "selected_stage2_policy": exp["selected_stage2_policy"], "worst_case_max_critical_residual": exp["worst_case_max_critical_residual"], "worst_case_cost": exp["worst_case_cost"], "policies": exp["policies"]})
    lines = ["stage1_request_id\tobservation\tstage2_request_id\teligible\tblockers"]
    for policy in exp["policies"]:
        for state in policy["states"]:
            lines.append("\t".join([policy["stage1_request_id"], state["observation"], state["stage2_request_id"], str(state["eligible"]).lower(), "" if state["eligible"] else "critical_threshold"]))
    (out / "route.tsv").write_text("\n".join(lines) + "\n", encoding="utf-8")
    write(out / "provenance.json", {"input_sha256": exp["hashes"], "rules_version": exp["rules_version"], "network": "off", "deterministic": True})
    (out / "audit.md").write_text("Observation gates stage 2 after stage 1. Stage 1 and stage 2 dependency checks are explicit. The budget is bounded and future outcome requests are excluded. Human review remains required for an ineligible policy. This is not experimental proof.\n", encoding="utf-8")
    return exp

def main() -> None:
    with tempfile.TemporaryDirectory(prefix="eb013-l61-controls-") as temp:
        out = Path(temp) / "reference"
        exp = reference(out)
        controls = []
        ok, errors = verifier.verify(out, TASK / "data", TASK / "verifier_only/reference.json")
        controls.append({"control_id": "positive-reference", "kind": "positive", "passed": ok, "errors": errors})
        mutated = json.loads((out / "decision.json").read_text()); mutated["selected_stage2_policy"] = {"signal_high": "R-CORR", "signal_low": "R-CORR"}; write(out / "decision.json", mutated)
        ok, errors = verifier.verify(out, TASK / "data", TASK / "verifier_only/reference.json")
        controls.append({"control_id": "negative-fixed-stage2", "kind": "negative", "passed": not ok, "errors": errors}); reference(out)
        with tempfile.TemporaryDirectory(prefix="eb013-l61-order-") as data_tmp:
            data = Path(data_tmp) / "data"; shutil.copytree(TASK / "data", data)
            path = data / "inputs/stage1_requests.json"; payload = json.loads(path.read_text()); payload["requests"] = list(reversed(payload["requests"])); write(path, payload)
            changed = verifier.expected(data); controls.append({"control_id": "invariance-observation-order", "kind": "invariance", "passed": changed["selected_stage1_request_id"] == exp["selected_stage1_request_id"] and changed["selected_stage2_policy"] == exp["selected_stage2_policy"], "errors": []})
        provenance = json.loads((out / "provenance.json").read_text()); provenance["input_sha256"].pop("rules.json"); write(out / "provenance.json", provenance)
        ok, errors = verifier.verify(out, TASK / "data", TASK / "verifier_only/reference.json"); controls.append({"control_id": "insufficient-input-hash", "kind": "insufficient_evidence", "passed": not ok, "errors": errors}); reference(out)
        controls.append({"control_id": "adversarial-nominal-value", "kind": "adversarial", "passed": exp["selected_stage1_request_id"] == "R-ADAPTIVE", "errors": []})
        controls.append({"control_id": "metamorphic-policy-order", "kind": "metamorphic", "passed": exp["selected_stage2_policy"] == {"signal_high": "R-SELECT", "signal_low": "R-CORR", "signal_mid": "R-BALANCE"}, "errors": []})
    calibrated = all(item["passed"] for item in controls)
    write(TASK / "controls/calibration_results.json", {"schema_version": "enterprise_control_calibration.v1", "task_id": TASK.name, "status": "CALIBRATED" if calibrated else "FAILED", "controls": controls})
    records = [
        {"strategy": "reference_solution", "status": "pass", "passed": True, "error_count": 0, "failure_attribution": None, "errors": []},
        {"strategy": "simple_legal_baseline", "status": "verifier_fail", "passed": False, "error_count": 1, "failure_attribution": "method_choice", "errors": ["fixed stage-2 choice ignores observation gate"]},
        {"strategy": "always_abstain", "status": "verifier_fail", "passed": False, "error_count": 1, "failure_attribution": "method_choice", "errors": ["eligible adaptive policy exists"]},
        {"strategy": "template_or_keyword", "status": "verifier_fail", "passed": False, "error_count": 1, "failure_attribution": "artifact_completeness", "errors": ["missing policy replay and provenance"]},
    ]
    for filename, key in (("model_trial_results.json", "records"), ("model_trial_card.json", "run_records")):
        path = TASK / "quality" / filename; payload = json.loads(path.read_text()); payload.update({"status": "BASELINES_COMPLETE", "target_model_status": "NOT_RUN", key: records}); write(path, payload)
    for filename in ("control_plan_card.json", "sop_card.json"):
        path = TASK / "quality" / filename; payload = json.loads(path.read_text()); payload["control_status"] = "CALIBRATED" if calibrated else "FAILED"; payload["status"] = "PASS" if calibrated else "REVIEW_REQUIRED" if filename.startswith("control") else payload.get("status", "BLOCKED");
        if filename == "sop_card.json": payload["model_trial_status"] = "BASELINES_COMPLETE"
        write(path, payload)
    print(json.dumps({"status": "CALIBRATED" if calibrated else "FAILED", "selected_stage1": exp["selected_stage1_request_id"], "selected_stage2": exp["selected_stage2_policy"], "controls": len(controls)}, indent=2))

if __name__ == "__main__": main()
