import importlib.util
import json
from pathlib import Path

from benchmark_runner.sequential_feedback import FeedbackController

ROOT = Path(__file__).resolve().parents[1]
TASK = ROOT / "benchmarks/eb014-sequential-evidence-feedback-002"


def test_feedback_requires_observed_dependencies(tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / "outputs").mkdir()
    (workspace / "data").mkdir()
    for path in (TASK / "data").glob("*.json"):
        (workspace / "data" / path.name).write_bytes(path.read_bytes())
    controller = FeedbackController(TASK, workspace)
    rejected = controller.submit({"round": 1, "action_id": "compare_context", "question_id": "Q", "rationale": "", "expected_information": ""})
    assert rejected["accepted"] is False
    assert "dependency" in rejected["error"]
    accepted = controller.submit({"round": 1, "action_id": "audit_quality", "question_id": "Q", "rationale": "", "expected_information": "quality"})
    assert accepted["accepted"] is True
    assert accepted["outcome"] == "quality_ok"


def test_feedback_is_deterministic_and_budgeted(tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / "outputs").mkdir()
    (workspace / "data").mkdir()
    for path in (TASK / "data").glob("*.json"):
        (workspace / "data" / path.name).write_bytes(path.read_bytes())
    controller = FeedbackController(TASK, workspace)
    for round_no, action in enumerate(("audit_quality", "compare_context", "independent_replicate", "orthogonal_assay"), 1):
        result = controller.submit({"round": round_no, "action_id": action, "question_id": "Q", "rationale": "", "expected_information": "state"})
        assert result["accepted"] is True
    assert controller.spent == 7
    assert controller.submit({"round": 5, "action_id": "stop", "question_id": "Q", "rationale": "", "expected_information": "stop"})["remaining_budget"] == 1
