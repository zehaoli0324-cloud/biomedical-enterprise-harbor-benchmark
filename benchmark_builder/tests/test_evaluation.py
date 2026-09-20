import json
from pathlib import Path

from benchmark_builder.compiler import spec_digest
from benchmark_builder.config import load_spec
from benchmark_builder.evaluation import build_iteration_plan, evaluate_submission, evaluation_protocol


ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "config/examples/crispr-resistance-e2e-001.toml"


def _packet(spec, score=4.0):
    criteria = {
        criterion.criterion_id: {
            "score": score,
            "confidence": 0.9,
            "evidence": [f"outputs/{criterion.criterion_id}.tsv"],
            "rationale": "Evidence is present and traceable.",
        }
        for criterion in spec.evaluation.criteria
    }
    gates = {gate: True for gate in spec.evaluation.hard_gates}
    return {
        "task_id": spec.task_id,
        "spec_digest": spec_digest(spec),
        "submission_id": "trial-001",
        "judges": [
            {"judge_id": judge.judge_id, "criteria": criteria, "hard_gates": gates}
            for judge in spec.evaluation.judges
        ],
    }


def test_protocol_contains_rubric_and_digest():
    spec = load_spec(CONFIG)
    protocol = evaluation_protocol(spec)
    assert protocol["spec_digest"] == spec_digest(spec)
    assert len(protocol["criteria"]) == 8
    assert len(protocol["judge_roles"]) == 3


def test_evaluation_accepts_consistent_judges(tmp_path: Path):
    spec = load_spec(CONFIG)
    packet_path = tmp_path / "judgments.json"
    packet_path.write_text(json.dumps(_packet(spec)), encoding="utf-8")
    report = evaluate_submission(spec, packet_path)
    assert report["status"] == "accepted"
    assert report["overall_score"] == 4.0
    assert report["overall_agreement"] == 1.0
    plan = build_iteration_plan(spec, report)
    assert plan["status"] == "ready_for_freeze"
    assert plan["next_action"]["type"] == "freeze"


def test_evaluation_requires_revision_for_failed_gate(tmp_path: Path):
    spec = load_spec(CONFIG)
    packet = _packet(spec)
    packet["judges"][0]["hard_gates"]["observability"] = False
    packet_path = tmp_path / "judgments.json"
    packet_path.write_text(json.dumps(packet), encoding="utf-8")
    report = evaluate_submission(spec, packet_path)
    assert report["status"] == "revise_required"
    assert "observability" in report["failed_gates"]
    plan = build_iteration_plan(spec, report)
    assert plan["status"] == "iteration_required"
    assert plan["next_action"]["type"] == "repair_release_gate"


def test_iteration_blocks_regression(tmp_path: Path):
    spec = load_spec(CONFIG)
    previous_packet = _packet(spec, score=4.0)
    current_packet = _packet(spec, score=4.0)
    current_packet["judges"][0]["criteria"]["scientific_correctness"]["score"] = 2.0
    previous_path = tmp_path / "previous.json"
    current_path = tmp_path / "current.json"
    previous_path.write_text(json.dumps(previous_packet), encoding="utf-8")
    current_path.write_text(json.dumps(current_packet), encoding="utf-8")
    previous_report = evaluate_submission(spec, previous_path)
    current_report = evaluate_submission(spec, current_path)
    plan = build_iteration_plan(spec, current_report, previous_report)
    assert plan["status"] == "rollback_required"
    assert plan["next_action"]["type"] == "rollback"
