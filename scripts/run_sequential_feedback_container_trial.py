"""Run an EB014-style agent in a hardened container with a host feedback broker."""
from __future__ import annotations

import argparse
import json
import shlex
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from benchmark_runner.docker_backend import build_docker_command, check_docker  # noqa: E402
from benchmark_runner.files import clean_environment, visible_file_hashes, write_json  # noqa: E402
from benchmark_runner.runner import _run_verifier, _transcript_from_process, _update_manifest, prepare_trial  # noqa: E402


def run_trial(task: Path, out: Path, command: str, image: str, trial_id: str, timeout: int) -> dict:
    check_docker()
    trial = prepare_trial(task, out, trial_id)
    command_parts = shlex.split(command)
    docker_command = build_docker_command(
        trial,
        command_parts,
        image,
        timeout,
        network="none",
        extra_environment={"BENCHMARK_FEEDBACK_BROKER": "1"},
    )
    _update_manifest(
        trial.manifest_path,
        agent_command=command_parts,
        started_at=time.time(),
        timeout_seconds=timeout,
        status="running",
        execution_backend="docker",
        docker_image=image,
        docker_network="none",
        isolation_mode="docker_hardened_baseline_with_host_feedback_broker",
        network_enforcement="docker_network_namespace",
        feedback_broker="host_process_hidden_task_not_mounted",
    )
    stdout_handle = (trial.trial_dir / "stdout.log").open("w", encoding="utf-8")
    stderr_handle = (trial.trial_dir / "stderr.log").open("w", encoding="utf-8")
    started = time.monotonic()
    process = subprocess.Popen(docker_command, cwd=trial.trial_dir, env=clean_environment(), stdout=stdout_handle, stderr=stderr_handle, text=True)
    broker = subprocess.Popen(
        [sys.executable, str(ROOT / "benchmark_runner/feedback_broker.py"), "--task", str(task), "--workspace", str(trial.workspace), "--pid", str(process.pid)],
        cwd=ROOT,
        env=clean_environment(),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        text=True,
    )
    timed_out = False
    try:
        process.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        timed_out = True
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=10)
    try:
        broker.wait(timeout=10)
    except subprocess.TimeoutExpired:
        broker.terminate()
        broker.wait(timeout=5)
    stdout_handle.close()
    stderr_handle.close()
    if (trial.workspace / "agent_events.jsonl").is_file():
        (trial.trial_dir / "agent_events.jsonl").write_bytes((trial.workspace / "agent_events.jsonl").read_bytes())
    process_result = None if timed_out else subprocess.CompletedProcess(docker_command, process.returncode, "", "")
    _transcript_from_process(trial, docker_command, process_result, "timeout" if timed_out else None)
    output_hashes = visible_file_hashes(trial.outputs)
    verifier_status = verifier_score = verifier_exit_code = None
    if output_hashes:
        verifier_status, verifier_score, verifier_exit_code = _run_verifier(trial)
    status = "timeout" if timed_out else "pass" if process.returncode == 0 and verifier_status == "pass" else "agent_error" if process.returncode else "verifier_fail"
    _update_manifest(
        trial.manifest_path,
        status=status,
        finished_at=time.time(),
        agent_exit_code=process.returncode,
        timed_out=timed_out,
        verifier_status=verifier_status,
        verifier_score=verifier_score,
        verifier_exit_code=verifier_exit_code,
        visible_output_hashes=output_hashes,
        elapsed_seconds=round(time.monotonic() - started, 3),
    )
    result = {"trial_id": trial.trial_id, "trial_dir": str(trial.trial_dir), "status": status, "verifier_status": verifier_status, "broker_exit_code": broker.returncode, "timed_out": timed_out}
    write_json(trial.trial_dir / "container_trial_result.json", result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("task", type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--trial-id", required=True)
    parser.add_argument("--image", required=True)
    parser.add_argument("--command", required=True)
    parser.add_argument("--timeout", type=int, default=1800)
    args = parser.parse_args()
    result = run_trial(args.task.resolve(), args.out.resolve(), args.command, args.image, args.trial_id, args.timeout)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
