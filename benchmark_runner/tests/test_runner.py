import json
import sys
from pathlib import Path

import benchmark_runner.runner as runner
from benchmark_runner.runner import prepare_trial, run_trial
from benchmark_runner.files import RunnerError


ROOT = Path(__file__).resolve().parents[2]
TASK = ROOT / "benchmarks/literature-screening-m1-001"


def test_prepare_hides_reference_and_copies_visible_inputs(tmp_path: Path):
    trial = prepare_trial(TASK, tmp_path, "trial-prepare")
    assert (trial.workspace / "instruction.md").is_file()
    assert (trial.workspace / "data/literature_records.tsv").is_file()
    assert not (trial.workspace / "verifier_only").exists()
    assert not (trial.workspace / "verifier.py").exists()
    manifest = json.loads(trial.manifest_path.read_text(encoding="utf-8"))
    assert manifest["agent_visible_paths"] == ["instruction.md", "data/", "outputs/"]
    assert manifest["isolation_mode"] == "process_cwd_only"


def test_prepare_rejects_output_inside_source_repository():
    try:
        prepare_trial(TASK, ROOT / "runs", "trial-repo-output")
    except RunnerError as exc:
        assert "outside the task Git repository" in str(exc)
    else:
        raise AssertionError("runner must reject process workspaces inside the source repository")


def test_run_archives_agent_process_and_verifier_result(tmp_path: Path):
    command = (
        f'{sys.executable} -c '
        '"from pathlib import Path; import os; '
        'Path(os.environ[\'BENCHMARK_OUTPUTS\']).joinpath(\'agent_marker.txt\').write_text(\'ok\')"'
    )
    result = run_trial(TASK, tmp_path, command, "trial-fail-no-submission", timeout_seconds=10)
    assert result.status == "verifier_fail"
    assert (result.trial_dir / "stdout.log").is_file()
    assert (result.trial_dir / "stderr.log").is_file()
    assert (result.trial_dir / "transcript.jsonl").is_file()
    assert (result.trial_dir / "verifier_result.json").is_file()
    manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))
    assert manifest["agent_exit_code"] == 0
    assert manifest["verifier_status"] == "fail"


def test_runner_accepts_reference_json_and_passed_verifier_shape(tmp_path: Path):
    task = ROOT / "benchmarks/eb001-split-leakage-001"
    command = f'{sys.executable} -c "pass"'
    result = run_trial(task, tmp_path, command, "trial-reference-json", timeout_seconds=10)
    assert result.status == "verifier_fail"
    verifier_result = json.loads((result.trial_dir / "verifier_result.json").read_text(encoding="utf-8"))
    assert verifier_result["passed"] is False
    assert verifier_result["status"] == "fail"
    manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))
    assert manifest["verifier_status"] == "fail"


def test_explicit_environment_passthrough_is_recorded_without_value(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("TRIAL_TEST_SECRET", "not-written-to-manifest")
    command = (
        f'{sys.executable} -c '
        '"from pathlib import Path; import os; '
        'Path(os.environ[\'BENCHMARK_OUTPUTS\']).joinpath(\'env.txt\').write_text(os.environ[\'TRIAL_TEST_SECRET\'])"'
    )
    result = run_trial(TASK, tmp_path, command, "trial-env", timeout_seconds=10, passthrough_env=("TRIAL_TEST_SECRET",))
    assert result.status == "verifier_fail"
    assert (result.trial_dir / "agent_workspace/outputs/env.txt").read_text(encoding="utf-8") == "not-written-to-manifest"
    manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))
    assert manifest["passed_environment"] == ["TRIAL_TEST_SECRET"]
    assert "not-written-to-manifest" not in result.manifest_path.read_text(encoding="utf-8")


def test_timeout_is_archived_without_running_verifier(tmp_path: Path):
    command = f'{sys.executable} -c "import time; time.sleep(2)"'
    result = run_trial(TASK, tmp_path, command, "trial-timeout", timeout_seconds=1)
    assert result.status == "timeout"
    assert result.timed_out is True
    assert not (result.trial_dir / "verifier_result.json").exists()
    manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))
    assert manifest["timeout_artifact_verification"] == "not_run_no_outputs"


def test_timeout_with_outputs_runs_verifier_but_remains_timeout(tmp_path: Path, monkeypatch):
    calls = []

    def fake_verifier(trial):
        calls.append(trial.outputs)
        return "pass", 1.0, 0

    monkeypatch.setattr(runner, "_run_verifier", fake_verifier)
    command = (
        f'{sys.executable} -c '
        '"from pathlib import Path; import os, time; '
        "output = Path(os.environ['BENCHMARK_OUTPUTS']); output.mkdir(exist_ok=True); "
        "output.joinpath('result.json').write_text('{}'); time.sleep(2)\""
    )
    result = run_trial(TASK, tmp_path, command, "trial-timeout-with-output", timeout_seconds=1)
    assert result.status == "timeout"
    assert result.timed_out is True
    assert result.verifier_status == "pass"
    assert calls == [result.trial_dir / "agent_workspace/outputs"]
    manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))
    assert manifest["timeout_artifact_verification"] == "pass"
    assert manifest["verifier_status"] == "pass"
    assert manifest["visible_output_hashes"]["result.json"]
