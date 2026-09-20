from pathlib import Path

import pytest

from benchmark_runner.docker_backend import build_docker_command
from benchmark_runner.files import RunnerError
from benchmark_runner.runner import prepare_trial


ROOT = Path(__file__).resolve().parents[2]
TASK = ROOT / "benchmarks/literature-screening-m1-001"


def test_docker_command_has_default_hardening(tmp_path: Path):
    trial = prepare_trial(TASK, tmp_path, "trial-docker-command")
    command = build_docker_command(trial, ["python", "adapter.py"], "benchmark-agent:test", 120)
    assert "--network" in command and command[command.index("--network") + 1] == "none"
    assert "--read-only" in command
    assert "--cap-drop=ALL" in command
    assert "no-new-privileges:true" in command
    assert "--memory" in command and command[command.index("--memory") + 1] == "512m"
    assert "/workspace" in command
    assert "verifier_only" not in " ".join(command)
    mount_text = " ".join(command)
    assert ",ro" in mount_text
    assert "dst=/workspace/outputs,rw" in mount_text


def test_docker_command_rejects_network_policy(tmp_path: Path):
    trial = prepare_trial(TASK, tmp_path, "trial-docker-network")
    with pytest.raises(RunnerError, match="network"):
        build_docker_command(trial, ["python", "adapter.py"], "benchmark-agent:test", 120, network="host")
