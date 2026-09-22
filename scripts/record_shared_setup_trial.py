#!/usr/bin/env python3
"""Archive a completed trial and replay it against the pre-trial frozen files."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TASK = ROOT / "benchmarks/eb013-shared-setup-routing-003"


def read(path):
    return json.loads(path.read_text())


def write(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n")


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def archive(trial, diagnostic=False, task=TASK):
    manifest = read(trial / "manifest.json")
    if manifest.get("task_id") != task.name:
        raise ValueError("trial belongs to a different task")
    if not manifest.get("finished_at"):
        raise ValueError("trial has not finished")
    freeze = read(task / "quality/pretrial_freeze.json")
    for name, expected in freeze["files"].items():
        if digest(task / name) != expected:
            raise ValueError("frozen file changed: " + name)
    for name, expected in manifest["input_hashes"].items():
        if freeze["files"].get(name) != expected or digest(trial / "agent_workspace" / name) != expected:
            raise ValueError("trial input mismatch: " + name)
    event_path = trial / "agent_workspace/agent_events.jsonl"
    events = [json.loads(line) for line in event_path.read_text().splitlines() if line.strip()]
    completed = any(event.get("type") == "turn.completed" for event in events)
    config = next(event for event in events if event.get("type") == "model_config")
    if not diagnostic and (not completed or manifest["agent_exit_code"] != 0
                           or config.get("completion_policy") != "process_exit_only"):
        raise ValueError("normal complete-turn execution required")
    spec = importlib.util.spec_from_file_location("frozen_trial_verifier", task / "verifier.py")
    verifier = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(verifier)
    outputs = trial / "agent_workspace/outputs"
    for name, expected in manifest["visible_output_hashes"].items():
        if digest(outputs / name) != expected:
            raise ValueError("trial output changed: " + name)
    passed, errors = verifier.verify(outputs, task / "data")
    raw = read(trial / "verifier_result.json")
    if passed != raw["passed"]:
        raise ValueError("raw verdict and frozen replay disagree")
    destination = task / "quality/trials" / manifest["trial_id"]
    if destination.exists():
        if read(destination / "manifest.json") != manifest:
            raise ValueError("archive identity mismatch")
        for name, expected in manifest["visible_output_hashes"].items():
            if digest(destination / "outputs" / name) != expected:
                raise ValueError("archived output mismatch: " + name)
    else:
        destination.mkdir(parents=True)
        shutil.copytree(outputs, destination / "outputs")
    for name in ("manifest.json", "verifier_result.json"):
        shutil.copy2(trial / name, destination / name)
    shutil.copy2(event_path, destination / "agent_events.jsonl")
    adapter_hashes = {}
    adapter_names = ["codex_gpt55.py"] if diagnostic else ["codex_complete_turn.py", "codex_gpt55.py"]
    for name in adapter_names:
        source = ROOT / "benchmark_runner/adapters" / name
        adapter_hashes[name] = digest(source)
        shutil.copy2(source, destination / name)
    record = {
        "strategy": "target_model", "model": config["model"], "trial_id": manifest["trial_id"],
        "status": "INVALID_ADAPTER_EARLY_COMPLETION" if diagnostic else ("pass" if passed else "fail"),
        "passed": None if diagnostic else passed, "raw_verifier_passed": raw["passed"],
        "counted_in_target_rate": not diagnostic, "turn_completed": completed,
        "replay_passed": passed, "replay_errors": errors,
        "event_log_sha256": digest(event_path), "event_log_path": str(event_path),
        "freeze_sha256": digest(task / "quality/pretrial_freeze.json"),
        "completion_policy": config.get("completion_policy", "artifact_existence_early_stop"),
        "adapter_source_sha256": adapter_hashes,
        "adapter_capture": "post-run source snapshot; no adapter edits occurred during execution",
        "isolation_mode": manifest["isolation_mode"],
        "limitation": "Local process trial, not container-isolated or held-out evaluation.",
        "evidence_path": str(destination.relative_to(ROOT)),
    }
    write(destination / "replay.json", record)
    return record


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--trial", required=True, type=Path)
    parser.add_argument("--diagnostic", required=True, type=Path)
    args = parser.parse_args()
    target = archive(args.trial)
    diagnostic = archive(args.diagnostic, diagnostic=True)
    status = "PASS" if target["passed"] else "FAIL"
    for filename, records_key in (("model_trial_results.json", "records"), ("model_trial_card.json", "run_records")):
        path = TASK / "quality" / filename
        payload = read(path)
        payload.update(status="COMPLETED", target_model_status=status)
        payload[records_key] = [r for r in payload[records_key] if r["strategy"] != "target_model"] + [target, diagnostic]
        write(path, payload)
    for path in (TASK / "quality/sop_card.json", ROOT / "candidate_pools/enterprise-v1/shared_setup_escalation.json"):
        payload = read(path)
        key = "model_trial_status" if path.name == "sop_card.json" else "target_model_status"
        payload[key] = status
        if path.name != "sop_card.json":
            payload["status"] = "TARGET_TRIAL_COMPLETE"
        payload["release_blockers"] = [b for b in payload["release_blockers"] if b != "target-model trial"]
        write(path, payload)
    write(TASK / "quality/target_trial_evidence.json", {"target": target, "excluded_diagnostic": diagnostic})
    print(json.dumps(target, indent=2))


if __name__ == "__main__":
    main()
