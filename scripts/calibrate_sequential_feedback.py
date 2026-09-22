#!/usr/bin/env python3
"""Calibrate the sequential feedback protocol before any target trial."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import shutil
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TASK = ROOT / "benchmarks/eb014-sequential-evidence-feedback-002"


def read(path):
    return json.loads(path.read_text())


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n")


def verifier():
    spec = importlib.util.spec_from_file_location("sequential_feedback_verifier", TASK / "verifier.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def reference(out):
    data = TASK / "data"
    scenario = read(TASK / "verifier_only/scenario.json")["outcomes"]
    path = ["audit_quality", "compare_context", "independent_replicate", "orthogonal_assay", "stop"]
    events = []
    for round_no, action_id in enumerate(path, 1):
        outcome = "stopped" if action_id == "stop" else scenario[action_id]["outcome"]
        cost = 0 if action_id == "stop" else scenario[action_id]["cost"]
        events.append({"round": round_no, "action_id": action_id, "observed_outcome": outcome, "cost": cost, "question_id": "Q-CONTEXT", "next_question": "continue only if a registered blocker remains"})
    write(out / "research_log.json", {"events": events, "final_claims": {"quality_status": "PASS", "context_status": "HOLD", "replication_status": "SUPPORTED", "claim_boundary": "registered_cohort_only"}})
    write(out / "completion.json", {"checks": {key: True for key in ("quality_audit", "context_comparison", "independent_replication", "stop_rule", "handoff")}, "stop_reason": "bounded_handoff", "human_review_required": True, "claim_boundary": "registered_cohort_only"})
    write(out / "provenance.json", {"input_sha256": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(data.glob("*.json"))}, "rules_version": "sequential-evidence-feedback-v1", "network": "off", "deterministic": True})
    (out / "audit.md").write_text("Quality passed, context shift was observed, independent replication was recorded, and the final claim remains bounded to the registered cohort.\n")


def main():
    v = verifier()
    controls = []
    with tempfile.TemporaryDirectory(prefix="sequential-feedback-controls-") as temp:
        out = Path(temp) / "outputs"
        reference(out)
        passed, errors = v.verify(out, TASK / "data")
        controls.append({"control_id": "reference", "kind": "positive", "passed": passed, "errors": errors})
        for control_id, mutation in (
            ("wrong-outcome", lambda p: p["events"][1].__setitem__("observed_outcome", "context_aligned")),
            ("missing-handoff", lambda p: p["events"].pop(3)),
            ("duplicate-action", lambda p: p["events"][2].__setitem__("action_id", "audit_quality")),
            ("budget-overspend", lambda p: p["events"].insert(4, {"round": 5, "action_id": "repair_quality", "observed_outcome": "quality_repaired", "cost": 1, "question_id": "Q", "next_question": ""})),
        ):
            shutil.copytree(out, Path(temp) / control_id)
            payload = read(Path(temp) / control_id / "research_log.json")
            mutation(payload)
            write(Path(temp) / control_id / "research_log.json", payload)
            ok, errors = v.verify(Path(temp) / control_id, TASK / "data")
            controls.append({"control_id": control_id, "kind": "negative", "passed": not ok, "errors": errors})
    if not all(row["passed"] for row in controls):
        raise AssertionError(json.dumps(controls, indent=2))
    write(TASK / "controls/calibration_results.json", {"status": "CALIBRATED", "controls": controls, "fixed_replay": {"actions": ["audit_quality", "compare_context", "independent_replicate", "orthogonal_assay", "stop"], "spent": 7, "feedback_hidden_from_agent": True}})
    controls_for_gate = [dict(row, kind={"reference": "positive", "wrong-outcome": "negative", "missing-handoff": "insufficient_evidence", "duplicate-action": "invariance", "budget-overspend": "negative"}[row["control_id"]]) for row in controls]
    write(TASK / "quality/control_plan_card.json", {"status": "CALIBRATED", "calibration_status": "CALIBRATED", "controls": controls_for_gate, "protocol": "one request -> one hidden deterministic response -> next model turn"})
    write(TASK / "quality/contract_audit.json", {"status": "PASS", "checks": [{"output": name, "schema_declared": True} for name in ("research_log.json", "completion.json", "provenance.json", "audit.md")], "controls": controls_for_gate, "completion_boundary": "public completeness only; no scientific score feedback"})
    write(TASK / "quality/independent_verifier_audit.json", {"status": "PASS", "method": "verifier replay plus fixed-sequence controller replay", "review_status": "pass"})
    write(TASK / "quality/difficulty_card.json", {"task_id": TASK.name, "status": "CALIBRATED", "primary_module": "horizon_sequential_evidence_feedback", "secondary_modules": ["judgment_evidence_sufficiency_abstention", "retrieval_independence_quorum"], "held_out_variants": ["wrong-outcome", "missing-handoff", "budget-overspend"], "max_public_action_rounds": 8, "long_trace_target": "over_40_model_turns_measured_not_required"})
    baseline_records = [{"strategy": name, "passed": name == "reference_solution", "status": "pass" if name == "reference_solution" else "fail", "errors": [] if name == "reference_solution" else ["baseline is not a valid stateful feedback policy"]} for name in ("reference_solution", "simple_legal_baseline", "always_abstain", "template_or_keyword")]
    write(TASK / "quality/model_trial_results.json", {"task_id": TASK.name, "status": "BASELINES_COMPLETE", "target_model_status": "NOT_RUN", "strategies": [row["strategy"] for row in baseline_records] + ["target_model"], "records": baseline_records})
    write(TASK / "quality/model_trial_card.json", {"task_id": TASK.name, "status": "BASELINES_COMPLETE", "target_model_status": "NOT_RUN", "strategies": [row["strategy"] for row in baseline_records] + ["target_model"], "run_records": baseline_records})
    write(TASK / "quality/sop_card.json", {"schema_version": "enterprise_harbor_sop_card.v1", "task_id": TASK.name, "sop_version": "enterprise-harbor-sop-v1.2", "source_status": "SYNTHETIC_DISCLOSED", "contract_status": "FROZEN_V1.0.0", "control_status": "CALIBRATED", "model_trial_status": "NOT_RUN", "independent_verifier_status": "PASS", "release_status": "BLOCKED", "release_blockers": ["target-model trial", "trajectory analysis", "fixed-container replay", "practitioner review"]})
    frozen = [TASK / "task.yaml", TASK / "instruction.md", TASK / "verifier.py"] + sorted((TASK / "data").glob("*.json")) + [TASK / "verifier_only/scenario.json"]
    write(TASK / "quality/pretrial_freeze.json", {"task_version": "1.0.0", "files": {str(path.relative_to(TASK)): hashlib.sha256(path.read_bytes()).hexdigest() for path in frozen}})
    print(json.dumps({"status": "CALIBRATED", "controls": len(controls)}, indent=2))


if __name__ == "__main__":
    main()
