#!/usr/bin/env python3
"""Create a fail-closed preflight report for the EB006 trial handoff."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TASKS = tuple(f"eb006-research-completion-{number:03d}" for number in (9, 10, 11))
ARCHIVE = ROOT / "dist/eb006-research-completion-family-20260924.tar.gz"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_solution(task_id: str) -> dict:
    task = ROOT / "benchmarks" / task_id
    verifier_spec = importlib.util.spec_from_file_location(f"{task_id}_verifier", task / "verifier.py")
    verifier = importlib.util.module_from_spec(verifier_spec)
    assert verifier_spec.loader is not None
    verifier_spec.loader.exec_module(verifier)
    with tempfile.TemporaryDirectory(prefix=f"{task_id}-preflight-") as directory:
        output = Path(directory) / "outputs"
        solution = subprocess.run(
            ["python3", str(task / "solution/solve.py"), "--data", str(task / "data"), "--out", str(output)],
            capture_output=True,
            text=True,
            check=False,
        )
        if solution.returncode:
            return {"task_id": task_id, "status": "FAIL", "stage": "solution", "stderr": solution.stderr[-2000:]}
        passed, errors = verifier.verify(output, task / "data", task / "verifier_only/reference.json")
        return {"task_id": task_id, "status": "PASS" if passed else "FAIL", "stage": "verifier", "errors": errors}


def main() -> None:
    checks: dict[str, object] = {}
    checks["archive"] = {
        "path": str(ARCHIVE),
        "exists": ARCHIVE.is_file(),
        "sha256": sha(ARCHIVE) if ARCHIVE.is_file() else None,
    }
    checks["standard_solution_verifier"] = [run_solution(task_id) for task_id in TASKS]
    checks["sop_preflight"] = {}
    for task_id in TASKS:
        report = ROOT / "reports" / f"{task_id}-enterprise-sop-preflight.json"
        value = json.loads(report.read_text(encoding="utf-8")) if report.is_file() else {}
        checks["sop_preflight"][task_id] = {"status": value.get("status"), "release_status": value.get("release_status"), "release_blockers": value.get("release_blockers", [])}
    replay = ROOT / "reports/eb006-research-completion-fixed-container-replay-20260924.json"
    replay_value = json.loads(replay.read_text(encoding="utf-8")) if replay.is_file() else {}
    checks["fixed_container_replay"] = {"status": replay_value.get("status", "NOT_RUN"), "report": str(replay)}
    checks["target_model_trial"] = {task_id: json.loads((ROOT / "benchmarks" / task_id / "quality/readiness.json").read_text(encoding="utf-8")).get("target_model_trial", "NOT_RUN") for task_id in TASKS}
    all_standard = all(item["status"] == "PASS" for item in checks["standard_solution_verifier"])
    all_sop = all(item["status"] == "PASS" for item in checks["sop_preflight"].values())
    checks["handoff_status"] = "READY_FOR_TARGET_TRIAL" if all_standard and all_sop else "BLOCKED"
    checks["release_status"] = "BLOCKED"
    checks["release_blockers"] = ["fixed-container replay", "target-model trial for 010", "practitioner review", "real-data replacement"]
    output = ROOT / "reports/eb006-research-completion-trial-preflight-20260924.json"
    output.write_text(json.dumps({"schema_version": "research_completion_trial_preflight.v1", "task_ids": list(TASKS), "checks": checks}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"handoff_status": checks["handoff_status"], "report": str(output)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
