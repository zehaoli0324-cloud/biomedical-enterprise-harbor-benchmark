import json
from pathlib import Path

from benchmark_runner.feedback_broker import process_request_once


ROOT = Path(__file__).resolve().parents[2]
TASK = ROOT / "benchmarks/eb014-sequential-evidence-feedback-002"


def make_workspace(tmp_path: Path) -> Path:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / "data").mkdir()
    for path in (TASK / "data").glob("*.json"):
        (workspace / "data" / path.name).write_bytes(path.read_bytes())
    (workspace / "outputs").mkdir()
    return workspace


def test_broker_processes_request_without_mounting_hidden_task(tmp_path):
    workspace = make_workspace(tmp_path)
    request = {
        "round": 1,
        "action_id": "audit_quality",
        "question_id": "Q-QUALITY",
        "rationale": "audit first",
        "expected_information": "quality status",
    }
    (workspace / "outputs/experiment_request.json").write_text(json.dumps(request) + "\n")
    response = process_request_once(TASK, workspace)
    assert response["accepted"] is True
    assert response["outcome"] == "quality_issue"
    assert not (workspace / "verifier_only").exists()
    assert not (workspace / "outputs/experiment_request.json").exists()
    assert json.loads((workspace / "outputs/feedback_history/round-001-request.json").read_text()) == request
    assert json.loads((workspace / "outputs/experiment_feedback.json").read_text())["round"] == 1


def test_broker_preserves_public_rejection_and_does_not_consume_budget(tmp_path):
    workspace = make_workspace(tmp_path)
    request = {"round": 2, "action_id": "audit_quality", "question_id": "Q", "rationale": "", "expected_information": "quality"}
    (workspace / "outputs/experiment_request.json").write_text(json.dumps(request) + "\n")
    response = process_request_once(TASK, workspace)
    assert response["accepted"] is False
    assert response["error"] == "round must be the next contiguous integer"
    assert not (workspace / "outputs/feedback_history/round-002-response.json").exists()
