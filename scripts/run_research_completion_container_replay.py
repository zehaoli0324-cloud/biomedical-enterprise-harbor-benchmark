#!/usr/bin/env python3
"""Run the deterministic EB006 solution inside a no-network Docker replay."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import tempfile
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(task_id: str, work: Path, timeout: int, base_image: str | None) -> dict:
    task = ROOT / "benchmarks" / task_id
    image = f"{task_id}:fixed-replay-20260924"
    output = work / "outputs"
    output.mkdir(parents=True)
    build_context = task / "environment"
    dockerfile = build_context / "Dockerfile"
    temporary_dockerfile = None
    if base_image:
        temporary_dockerfile = work / "Dockerfile.override"
        temporary_dockerfile.write_text(
            dockerfile.read_text(encoding="utf-8").replace("FROM python:3.11-slim", f"FROM {base_image}", 1),
            encoding="utf-8",
        )
        dockerfile_arg = str(temporary_dockerfile)
    else:
        dockerfile_arg = str(dockerfile)
    build = subprocess.run(
        ["docker", "build", "--pull=false", "-f", dockerfile_arg, "-t", image, str(build_context)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if build.returncode:
        raise RuntimeError(f"docker build failed for {task_id}: {build.stderr[-2000:]}")
    command = [
        "docker", "run", "--rm", "--network", "none",
        "--cpus", "1", "--memory", "1024m",
        "--mount", f"type=bind,src={task / 'data'},dst=/root/data,readonly",
        "--mount", f"type=bind,src={task / 'solution'},dst=/root/solution,readonly",
        "--mount", f"type=bind,src={output},dst=/root/outputs",
        image,
        "python", "/root/solution/solve.py", "--data", "/root/data", "--out", "/root/outputs",
    ]
    started = time.time()
    process = subprocess.run(command, capture_output=True, text=True, timeout=timeout, check=False)
    result = {
        "task_id": task_id,
        "image": image,
        "network": "none",
        "command_exit_code": process.returncode,
        "elapsed_seconds": round(time.time() - started, 3),
        "stdout": process.stdout[-4000:],
        "stderr": process.stderr[-4000:],
        "outputs": sorted(path.relative_to(output).as_posix() for path in output.rglob("*") if path.is_file()),
    }
    if process.returncode:
        return result | {"status": "CONTAINER_FAIL"}
    verifier = subprocess.run(
        [
            "python3", str(task / "verifier.py"), "--submission", str(output),
            "--data", str(task / "data"), "--reference", str(task / "verifier_only/reference.json"),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    result.update({"verifier_exit_code": verifier.returncode, "verifier_stdout": verifier.stdout[-4000:], "verifier_stderr": verifier.stderr[-4000:]})
    result["status"] = "PASS_PROTOCOL_REPLAY" if verifier.returncode == 0 else "VERIFIER_FAIL"
    result["output_sha256"] = {path.relative_to(output).as_posix(): sha(path) for path in output.rglob("*") if path.is_file()}
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("task", nargs="+", choices=["eb006-research-completion-009", "eb006-research-completion-010", "eb006-research-completion-011"])
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--timeout", type=int, default=60)
    parser.add_argument("--base-image", help="Use a locally cached Python-compatible base image instead of python:3.11-slim")
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".eb006-container-replay-", dir=ROOT) as temporary:
        records = []
        for task_id in args.task:
            try:
                records.append(run(task_id, Path(temporary) / task_id, args.timeout, args.base_image))
            except (RuntimeError, subprocess.TimeoutExpired) as exc:
                records.append({"task_id": task_id, "status": "BLOCKED_ENVIRONMENT", "error": str(exc)})
    if all(item["status"] == "PASS_PROTOCOL_REPLAY" for item in records):
        status = "PASS"
    elif any(item["status"] == "BLOCKED_ENVIRONMENT" for item in records):
        status = "BLOCKED_ENVIRONMENT"
    else:
        status = "FAIL"
    report = {"schema_version": "research_completion_fixed_container_replay.v1", "base_image_override": args.base_image, "isolation": {"docker_network": "none", "cpus": 1, "memory_mb": 1024}, "records": records, "status": status}
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "tasks": args.task}, ensure_ascii=False))
    if report["status"] == "FAIL":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
