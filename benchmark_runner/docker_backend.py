from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

from .files import RunnerError
from .models import PreparedTrial


def docker_executable() -> str:
    executable = shutil.which("docker")
    if not executable:
        raise RunnerError("docker executable was not found on PATH")
    return executable


def check_docker() -> str:
    executable = docker_executable()
    result = subprocess.run(
        [executable, "info", "--format", "{{.ServerVersion}}"],
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        detail = (result.stderr or result.stdout).strip().splitlines()
        raise RunnerError(f"docker daemon is unavailable: {detail[-1] if detail else 'unknown error'}")
    return result.stdout.strip()


def _safe_mount_path(path: Path) -> str:
    if not path.is_absolute():
        raise RunnerError(f"Docker mount path must be absolute: {path}")
    return str(path.resolve())


def build_docker_command(
    trial: PreparedTrial,
    command: list[str],
    image: str,
    timeout_seconds: int,
    passthrough_env: tuple[str, ...] = (),
    network: str = "none",
    cpus: float = 1.0,
    memory: str = "512m",
    pids_limit: int = 256,
    user: str = "1000:1000",
) -> list[str]:
    if not image or any(char.isspace() for char in image):
        raise RunnerError("docker image must be a non-empty image reference without whitespace")
    if network not in {"none", "bridge"}:
        raise RunnerError("docker network must be 'none' or 'bridge'")
    if cpus <= 0 or pids_limit < 1 or timeout_seconds < 1:
        raise RunnerError("docker cpu, pids limit, and timeout must be positive")
    if not command:
        raise RunnerError("docker agent command cannot be empty")

    docker = docker_executable()
    event_log = trial.workspace / "agent_events.jsonl"
    event_log.touch(exist_ok=True)
    docker_command = [
        docker,
        "run",
        "--rm",
        "--init",
        "--network",
        network,
        "--read-only",
        "--tmpfs",
        "/tmp:rw,nosuid,nodev,size=64m",
        "--cap-drop=ALL",
        "--security-opt",
        "no-new-privileges:true",
        "--pids-limit",
        str(pids_limit),
        "--cpus",
        str(cpus),
        "--memory",
        memory,
        "--user",
        user,
        "--workdir",
        "/workspace",
        "--label",
        f"benchmark.task_id={trial.task_id}",
        "--label",
        f"benchmark.trial_id={trial.trial_id}",
        "--mount",
        f"type=bind,src={_safe_mount_path(trial.workspace / 'data')},dst=/workspace/data,ro",
        "--mount",
        f"type=bind,src={_safe_mount_path(trial.workspace / 'instruction.md')},dst=/workspace/instruction.md,ro",
        "--mount",
        f"type=bind,src={_safe_mount_path(trial.workspace / 'outputs')},dst=/workspace/outputs,rw",
        "--mount",
        f"type=bind,src={_safe_mount_path(event_log)},dst=/workspace/agent_events.jsonl,rw",
    ]
    base_environment = {
        "BENCHMARK_TASK_ID": trial.task_id,
        "BENCHMARK_TRIAL_ID": trial.trial_id,
        "BENCHMARK_WORKSPACE": "/workspace",
        "BENCHMARK_OUTPUTS": "/workspace/outputs",
        "BENCHMARK_PROMPT": "/workspace/instruction.md",
        "BENCHMARK_EVENT_LOG": "/workspace/agent_events.jsonl",
        "BENCHMARK_NETWORK_POLICY": network,
        "PYTHONUNBUFFERED": "1",
    }
    for name, value in base_environment.items():
        docker_command.extend(["--env", f"{name}={value}"])
    for name in passthrough_env:
        if not name or "=" in name:
            raise RunnerError(f"invalid environment variable name: {name!r}")
        if name not in os.environ:
            raise RunnerError(f"requested environment variable is not set: {name}")
        docker_command.extend(["--env", name])
    docker_command.append(image)
    docker_command.extend(command)
    return docker_command
