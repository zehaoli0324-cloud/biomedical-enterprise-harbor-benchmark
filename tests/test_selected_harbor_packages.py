from __future__ import annotations

import importlib.util
import subprocess
import sys
import tomllib
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
TASK_IDS = (
    "eb014-adaptive-evidence-ladder-003",
    "eb015-real-source-replacement-gate-001",
    "eb014-sequential-evidence-feedback-002",
    "eb006-research-completion-011",
)


def load_verifier(task: Path):
    spec = importlib.util.spec_from_file_location(f"{task.name}_harbor_verifier", task / "verifier.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("task_id", TASK_IDS)
def test_harbor_package_structure_and_frozen_copies(task_id):
    task = ROOT / "benchmarks" / task_id
    required = (
        "task.toml",
        "environment/Dockerfile",
        "environment/instruction.md",
        "solution/solve.sh",
        "solution/solve.py",
        "tests/Dockerfile",
        "tests/test.sh",
        "tests/test_task.py",
        "tests/verifier.py",
    )
    assert all((task / name).is_file() for name in required)
    config = tomllib.loads((task / "task.toml").read_text())
    assert config["task"]["name"] == f"terminal-bench-science/{task_id}"
    assert config["verifier"]["environment_mode"] == "separate"
    assert config["verifier"]["environment"]["network_mode"] == "no-network"
    assert (task / "instruction.md").read_bytes() == (task / "environment/instruction.md").read_bytes()
    assert (task / "verifier.py").read_bytes() == (task / "tests/verifier.py").read_bytes()
    for source in (task / "data").iterdir():
        if source.is_file():
            assert source.read_bytes() == (task / "environment/data" / source.name).read_bytes()
            assert source.read_bytes() == (task / "tests/verification_data" / source.name).read_bytes()


@pytest.mark.parametrize("task_id", TASK_IDS)
def test_harbor_oracle_passes_original_verifier(task_id, tmp_path):
    task = ROOT / "benchmarks" / task_id
    outputs = tmp_path / task_id / "outputs"
    subprocess.run(
        [
            sys.executable,
            str(task / "solution/solve.py"),
            "--data",
            str(task / "data"),
            "--out",
            str(outputs),
        ],
        check=True,
    )
    verifier = load_verifier(task)
    passed, errors = verifier.verify(outputs, task / "data", task / "verifier_only/reference.json")
    assert passed, errors
