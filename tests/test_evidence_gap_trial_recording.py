import importlib
import shutil
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def prepared_trial(tmp_path, monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT / "scripts"))
    recorder = importlib.import_module("record_evidence_gap_trial")
    calibration = importlib.import_module("calibrate_evidence_gap_followup")
    original = ROOT / "benchmarks/eb014-evidence-gap-followup-001"
    task = tmp_path / original.name
    shutil.copytree(original, task)
    monkeypatch.setattr(recorder, "TASK", task)
    trial = tmp_path / "fake-trial"
    workspace = trial / "agent_workspace"
    shutil.copytree(task / "data", workspace / "data")
    shutil.copy2(task / "instruction.md", workspace / "instruction.md")
    calibration.reference(workspace / "outputs", task / "data", calibration.verifier())
    (workspace / "agent_events.jsonl").write_text(
        '{"type":"model_config","model":"test-fixture"}\n{"type":"turn.completed"}\n'
    )
    inputs = [workspace / "instruction.md", *sorted((workspace / "data").glob("*.json"))]
    recorder.write(trial / "manifest.json", {
        "task_id": task.name, "trial_id": "test-only", "status": "pass",
        "started_at": "2026-09-22T00:00:00+00:00", "finished_at": "2026-09-22T00:00:01+00:00",
        "agent_exit_code": 0, "isolation_mode": "test-only", "timeout_seconds": 10,
        "input_hashes": {p.relative_to(workspace).as_posix(): recorder.digest(p) for p in inputs},
        "visible_output_hashes": {p.name: recorder.digest(p) for p in (workspace / "outputs").iterdir()},
    })
    recorder.write(trial / "verifier_result.json", {"passed": True, "errors": []})
    return recorder, task, trial


def test_archive_and_no_overwrite(prepared_trial):
    recorder, task, trial = prepared_trial
    result = recorder.record(trial)
    assert result["classification"] == "RAW_PASS"
    assert result["artifact_content_changed"] is False
    archive = task / "quality/trials/test-only"
    assert (archive / "agent_events.jsonl").is_file()
    assert recorder.digest(archive / "outputs/research_plan.json") == result["artifact_sha256"]["research_plan.json"]
    with pytest.raises(ValueError, match="already archived"):
        recorder.record(trial)


def test_changed_artifact_refused(prepared_trial):
    recorder, task, trial = prepared_trial
    (trial / "agent_workspace/outputs/audit.md").write_text("changed")
    with pytest.raises(ValueError, match="artifact changed"):
        recorder.record(trial)


def test_changed_freeze_refused(prepared_trial):
    recorder, task, trial = prepared_trial
    (task / "instruction.md").write_text("changed")
    with pytest.raises(ValueError, match="Frozen task changed"):
        recorder.record(trial)
