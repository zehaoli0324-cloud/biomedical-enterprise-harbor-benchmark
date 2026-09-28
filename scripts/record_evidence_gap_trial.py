"""Archive EB014 raw trial evidence and unchanged-artifact replay."""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from datetime import datetime
from pathlib import Path

from calibrate_evidence_gap_followup import ROOT, TASK, read, verifier, write


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def record(trial):
    trial = trial.resolve()
    manifest = read(trial / "manifest.json")
    if manifest["task_id"] != TASK.name or not manifest.get("finished_at"):
        raise ValueError("A finished EB014 trial is required")
    freeze_path = TASK / "quality/pretrial_freeze.json"
    freeze = read(freeze_path)
    for name, value in freeze["sha256"].items():
        if digest(TASK / name) != value:
            raise ValueError("Frozen task changed: " + name)
    for name, value in freeze["authoring_sha256"].items():
        if digest(ROOT / name) != value:
            raise ValueError("Frozen authoring code changed: " + name)
    workspace = trial / "agent_workspace"
    for name, value in manifest["input_hashes"].items():
        if freeze["sha256"].get(name) != value or digest(workspace / name) != value:
            raise ValueError("Trial inputs changed: " + name)
    event_path = workspace / "agent_events.jsonl"
    events = [json.loads(line) for line in event_path.read_text().splitlines() if line.strip()] if event_path.exists() else []
    completed = any(e.get("type") == "turn.completed" for e in events)
    config = next((e for e in events if e.get("type") == "model_config"), {})
    raw = read(trial / "verifier_result.json") if (trial / "verifier_result.json").exists() else None
    outputs = workspace / "outputs"
    artifact_hashes = {p.name: digest(p) for p in sorted(outputs.glob("*")) if p.is_file()}
    for name, value in manifest.get("visible_output_hashes", {}).items():
        if artifact_hashes.get(name) != value:
            raise ValueError("Trial artifact changed: " + name)
    passed, errors = verifier().verify(outputs, TASK / "data")
    normal = completed and manifest.get("agent_exit_code") == 0 and not manifest.get("timed_out")
    if normal and raw is not None and raw.get("passed") != passed:
        raise ValueError("Frozen replay disagrees with raw verdict")
    classification = ("RAW_PASS" if passed else "VERIFIER_FAIL_REQUIRES_TRIAGE") if normal else (
        "TIMEOUT" if manifest.get("timed_out") or manifest.get("agent_exit_code") == 124 else "AGENT_ERROR")
    elapsed = (datetime.fromisoformat(manifest["finished_at"]) - datetime.fromisoformat(manifest["started_at"])).total_seconds()
    expected = verifier().expected(TASK / "data")
    decision = read(outputs / "research_plan.json") if (outputs / "research_plan.json").exists() else None
    evidence = {
        "task_id": TASK.name, "trial_id": manifest["trial_id"], "model": config.get("model"),
        "classification": classification, "runner_status": manifest["status"],
        "turn_completed": completed, "agent_exit_code": manifest.get("agent_exit_code"),
        "elapsed_seconds": elapsed, "timeout_seconds": manifest.get("timeout_seconds"),
        "started_at": manifest["started_at"], "finished_at": manifest["finished_at"],
        "raw_verifier_result": raw, "frozen_replay": {"passed": passed, "errors": errors},
        "artifact_sha256": artifact_hashes, "artifact_content_changed": False,
        "event_log_sha256": digest(event_path) if event_path.exists() else None,
        "freeze_sha256": digest(freeze_path), "isolation_mode": manifest.get("isolation_mode"),
        "trial_dir": str(trial), "submitted_plan": decision,
        "expected_plan": expected["research_plan.json"],
        "adapter_sha256": {name: digest(ROOT / "benchmark_runner/adapters" / name) for name in ("codex_complete_turn.py", "codex_gpt55.py")},
        "adapter_capture": "Post-run hashes; compare with the separately observed in-run hashes during analysis.",
        "target_model_defeated": False if classification == "RAW_PASS" else None,
        "limitations": ["One local process trial", "Not container-isolated", "No held-out model trial", "Human scientific review NOT_RUN"],
    }
    destination = TASK / "quality/trials" / manifest["trial_id"]
    if destination.exists():
        raise ValueError("Trial already archived")
    destination.mkdir(parents=True)
    if outputs.exists():
        shutil.copytree(outputs, destination / "outputs")
    for path in (trial / "manifest.json", trial / "verifier_result.json", event_path,
                 workspace / "agent_final.md", workspace / "adapter_stderr.log", freeze_path):
        if path.exists():
            shutil.copy2(path, destination / path.name)
    write(destination / "evidence.json", evidence)
    quality = TASK / "quality"
    write(quality / "target_trial_evidence.json", evidence)
    history_path = quality / "model_trial_results.json"
    history = read(history_path) if history_path.exists() else {"task_id": TASK.name, "records": []}
    history["records"].append(evidence)
    history["target_model_status"] = classification
    write(history_path, history)
    readiness = read(quality / "readiness.json")
    readiness.update(status="TARGET_TRIAL_COMPLETE", target_model_trial=classification, release_ready=False)
    write(quality / "readiness.json", readiness)
    return evidence


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("trial", type=Path)
    args = parser.parse_args()
    print(json.dumps(record(args.trial), indent=2))
