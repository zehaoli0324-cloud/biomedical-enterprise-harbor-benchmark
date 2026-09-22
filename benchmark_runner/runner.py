from __future__ import annotations

import json
import os
import shlex
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from .files import (
    RunnerError,
    clean_environment,
    copy_agent_visible_inputs,
    ensure_trial_root_is_external,
    read_task_id,
    utc_trial_id,
    visible_file_hashes,
    write_json,
)
from .docker_backend import build_docker_command
from .models import PreparedTrial, TrialResult


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def prepare_trial(task_dir: str | Path, out_dir: str | Path, trial_id: str | None = None) -> PreparedTrial:
    task_path = Path(task_dir).resolve()
    output_root = Path(out_dir).resolve()
    ensure_trial_root_is_external(task_path, output_root)
    task_id = read_task_id(task_path)
    resolved_trial_id = trial_id or utc_trial_id()
    trial_dir = output_root / resolved_trial_id
    if trial_dir.exists():
        raise RunnerError(f"trial output already exists: {trial_dir}")
    workspace = trial_dir / "agent_workspace"
    workspace.mkdir(parents=True, exist_ok=False)
    copy_agent_visible_inputs(task_path, workspace)
    prompt_path = trial_dir / "prompt.md"
    prompt_path.write_text((workspace / "instruction.md").read_text(encoding="utf-8"), encoding="utf-8")
    manifest_path = trial_dir / "manifest.json"
    manifest = {
        "schema_version": "benchmark_runner.trial.v1",
        "task_id": task_id,
        "trial_id": resolved_trial_id,
        "task_dir": str(task_path),
        "trial_dir": str(trial_dir),
        "workspace": str(workspace),
        "agent_visible_paths": ["instruction.md", "data/", "outputs/"],
        "hidden_paths_not_mounted": ["verifier_only/", "verifier.py", "tests/"],
        "network_policy": "off_requested",
        "isolation_mode": "process_cwd_only",
        "network_enforcement": "caller_or_container_required",
        "prepared_at": _now(),
        "input_hashes": visible_file_hashes(workspace),
        "status": "prepared",
    }
    write_json(manifest_path, manifest)
    return PreparedTrial(
        task_dir=task_path,
        trial_dir=trial_dir,
        workspace=workspace,
        outputs=workspace / "outputs",
        task_id=task_id,
        trial_id=resolved_trial_id,
        prompt_path=prompt_path,
        manifest_path=manifest_path,
    )


def _load_manifest(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _update_manifest(path: Path, **updates: object) -> dict[str, object]:
    manifest = _load_manifest(path)
    manifest.update(updates)
    write_json(path, manifest)
    return manifest


def _transcript_from_process(trial: PreparedTrial, command: list[str], result: subprocess.CompletedProcess[str] | None, error: str | None = None) -> None:
    events: list[dict[str, object]] = [
        {"type": "runner_start", "timestamp": _now(), "command": command},
    ]
    if result is not None:
        for stream, content in (("stdout", result.stdout), ("stderr", result.stderr)):
            for line_number, line in enumerate(content.splitlines(), start=1):
                events.append({"type": "process_output", "stream": stream, "line": line_number, "text": line})
        events.append({"type": "runner_exit", "timestamp": _now(), "returncode": result.returncode})
    else:
        events.append({"type": "runner_error", "timestamp": _now(), "error": error or "unknown"})
    (trial.trial_dir / "transcript.jsonl").write_text(
        "".join(json.dumps(event, ensure_ascii=False) + "\n" for event in events),
        encoding="utf-8",
    )


def _run_process(
    trial: PreparedTrial,
    command: list[str],
    timeout_seconds: int,
    passthrough_env: tuple[str, ...],
    backend: str = "process",
    docker_image: str | None = None,
    docker_network: str = "none",
    docker_cpus: float = 1.0,
    docker_memory: str = "512m",
    docker_pids_limit: int = 256,
    docker_user: str = "1000:1000",
) -> tuple[subprocess.CompletedProcess[str] | None, bool, str | None]:
    env = clean_environment()
    for name in passthrough_env:
        if not name or "=" in name:
            raise RunnerError(f"invalid environment variable name: {name!r}")
        if name not in os.environ:
            raise RunnerError(f"requested environment variable is not set: {name}")
        env[name] = os.environ[name]
    env.update(
        {
            "BENCHMARK_TASK_ID": trial.task_id,
            "BENCHMARK_HIDDEN_TASK_DIR": str(trial.task_dir),
            "BENCHMARK_TRIAL_ID": trial.trial_id,
            "BENCHMARK_WORKSPACE": str(trial.workspace),
            "BENCHMARK_OUTPUTS": str(trial.outputs),
            "BENCHMARK_PROMPT": str(trial.prompt_path),
            "BENCHMARK_EVENT_LOG": str(trial.workspace / "agent_events.jsonl"),
            "BENCHMARK_NETWORK_POLICY": "off_requested",
            "PYTHONUNBUFFERED": "1",
        }
    )
    if backend not in {"process", "docker"}:
        raise RunnerError("backend must be 'process' or 'docker'")
    if backend == "docker":
        if not docker_image:
            raise RunnerError("docker backend requires --docker-image")
        command = build_docker_command(
            trial,
            command,
            docker_image,
            timeout_seconds,
            passthrough_env,
            docker_network,
            docker_cpus,
            docker_memory,
            docker_pids_limit,
            docker_user,
        )
        env = clean_environment()
    started = time.monotonic()
    try:
        result = subprocess.run(
            command,
            cwd=trial.workspace if backend == "process" else trial.trial_dir,
            env=env,
            text=True,
            capture_output=True,
            timeout=timeout_seconds,
            check=False,
        )
        elapsed = round(time.monotonic() - started, 3)
        (trial.trial_dir / "stdout.log").write_text(result.stdout, encoding="utf-8")
        (trial.trial_dir / "stderr.log").write_text(result.stderr, encoding="utf-8")
        return result, False, str(elapsed)
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout or ""
        stderr = exc.stderr or ""
        if isinstance(stdout, bytes):
            stdout = stdout.decode("utf-8", errors="replace")
        if isinstance(stderr, bytes):
            stderr = stderr.decode("utf-8", errors="replace")
        (trial.trial_dir / "stdout.log").write_text(stdout, encoding="utf-8")
        (trial.trial_dir / "stderr.log").write_text(stderr, encoding="utf-8")
        return None, True, str(round(time.monotonic() - started, 3))
    except OSError as exc:
        (trial.trial_dir / "stdout.log").write_text("", encoding="utf-8")
        (trial.trial_dir / "stderr.log").write_text(str(exc), encoding="utf-8")
        return None, False, str(exc)


def _run_verifier(trial: PreparedTrial) -> tuple[str, float | None, int]:
    verifier = trial.task_dir / "verifier.py"
    reference_candidates = (
        trial.task_dir / "verifier_only" / "reference_labels.json",
        trial.task_dir / "verifier_only" / "reference.json",
    )
    reference = next((path for path in reference_candidates if path.is_file()), None)
    if not verifier.is_file() or reference is None:
        raise RunnerError("task needs verifier.py and verifier_only/reference_labels.json or reference.json")
    command = [
        sys.executable,
        str(verifier),
        "--submission",
        str(trial.outputs),
        "--data",
        str(trial.task_dir / "data"),
        "--reference",
        str(reference),
    ]
    started = time.monotonic()
    result = subprocess.run(command, cwd=trial.task_dir, text=True, capture_output=True, check=False)
    elapsed = round(time.monotonic() - started, 3)
    (trial.trial_dir / "verifier_stdout.log").write_text(result.stdout, encoding="utf-8")
    (trial.trial_dir / "verifier_stderr.log").write_text(result.stderr, encoding="utf-8")
    verifier_result: dict[str, object]
    try:
        verifier_result = json.loads(result.stdout)
    except json.JSONDecodeError:
        verifier_result = {
            "status": "infrastructure_error",
            "score": 0,
            "errors": ["verifier did not return a JSON object"],
            "raw_stdout": result.stdout[-2000:],
        }
    if "status" not in verifier_result and isinstance(verifier_result.get("passed"), bool):
        verifier_result["status"] = "pass" if verifier_result["passed"] else "fail"
    verifier_result["runner_verifier_exit_code"] = result.returncode
    verifier_result["runner_verifier_seconds"] = elapsed
    write_json(trial.trial_dir / "verifier_result.json", verifier_result)
    status = str(verifier_result.get("status", "infrastructure_error"))
    score = verifier_result.get("score")
    return status, float(score) if isinstance(score, (int, float)) else None, result.returncode


def run_trial(
    task_dir: str | Path,
    out_dir: str | Path,
    command: str,
    trial_id: str | None = None,
    timeout_seconds: int = 120,
    passthrough_env: tuple[str, ...] = (),
    backend: str = "process",
    docker_image: str | None = None,
    docker_network: str = "none",
    docker_cpus: float = 1.0,
    docker_memory: str = "512m",
    docker_pids_limit: int = 256,
    docker_user: str = "1000:1000",
) -> TrialResult:
    if timeout_seconds < 1:
        raise RunnerError("timeout_seconds must be positive")
    trial = prepare_trial(task_dir, out_dir, trial_id)
    command_parts = shlex.split(command)
    if not command_parts:
        raise RunnerError("agent command cannot be empty")
    if backend not in {"process", "docker"}:
        raise RunnerError("backend must be 'process' or 'docker'")
    _update_manifest(
        trial.manifest_path,
        agent_command=command_parts,
        passed_environment=list(passthrough_env),
        started_at=_now(),
        timeout_seconds=timeout_seconds,
        status="running",
        execution_backend=backend,
        docker_image=docker_image if backend == "docker" else None,
        docker_network=docker_network if backend == "docker" else None,
        docker_cpus=docker_cpus if backend == "docker" else None,
        docker_memory=docker_memory if backend == "docker" else None,
        docker_pids_limit=docker_pids_limit if backend == "docker" else None,
        docker_user=docker_user if backend == "docker" else None,
        isolation_mode="docker_hardened_baseline" if backend == "docker" else "process_cwd_only",
        network_enforcement="docker_network_namespace" if backend == "docker" else "caller_or_container_required",
    )
    process_result, timed_out, process_info = _run_process(
        trial,
        command_parts,
        timeout_seconds,
        passthrough_env,
        backend,
        docker_image,
        docker_network,
        docker_cpus,
        docker_memory,
        docker_pids_limit,
        docker_user,
    )
    _transcript_from_process(trial, command_parts, process_result, process_info if process_result is None else None)
    event_log = trial.workspace / "agent_events.jsonl"
    if event_log.is_file():
        shutil.copy2(event_log, trial.trial_dir / "agent_events.jsonl")
    if timed_out:
        output_hashes = visible_file_hashes(trial.outputs)
        if output_hashes:
            verifier_status, verifier_score, verifier_exit_code = _run_verifier(trial)
            _update_manifest(
                trial.manifest_path,
                status="timeout",
                finished_at=_now(),
                timed_out=True,
                timeout_artifact_verification="pass" if verifier_exit_code == 0 and verifier_status == "pass" else "fail",
                verifier_status=verifier_status,
                verifier_score=verifier_score,
                verifier_exit_code=verifier_exit_code,
                visible_output_hashes=output_hashes,
            )
            return TrialResult(
                trial.task_id,
                trial.trial_id,
                trial.trial_dir,
                "timeout",
                None,
                verifier_status,
                verifier_score,
                True,
                trial.manifest_path,
            )
        _update_manifest(
            trial.manifest_path,
            status="timeout",
            finished_at=_now(),
            timed_out=True,
            timeout_artifact_verification="not_run_no_outputs",
        )
        return TrialResult(trial.task_id, trial.trial_id, trial.trial_dir, "timeout", None, None, None, True, trial.manifest_path)
    if process_result is None:
        _update_manifest(trial.manifest_path, status="agent_error", finished_at=_now(), timed_out=False)
        return TrialResult(trial.task_id, trial.trial_id, trial.trial_dir, "agent_error", None, None, None, False, trial.manifest_path)

    verifier_status, verifier_score, verifier_exit_code = _run_verifier(trial)
    if process_result.returncode != 0:
        status = "agent_error"
    elif verifier_exit_code != 0 or verifier_status != "pass":
        status = "verifier_fail"
    else:
        status = "pass"
    _update_manifest(
        trial.manifest_path,
        status=status,
        finished_at=_now(),
        agent_exit_code=process_result.returncode,
        verifier_status=verifier_status,
        verifier_score=verifier_score,
        verifier_exit_code=verifier_exit_code,
        visible_output_hashes=visible_file_hashes(trial.outputs),
    )
    return TrialResult(
        trial.task_id,
        trial.trial_id,
        trial.trial_dir,
        status,
        process_result.returncode,
        verifier_status,
        verifier_score,
        False,
        trial.manifest_path,
    )
