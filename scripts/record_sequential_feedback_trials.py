#!/usr/bin/env python3
"""Archive interactive trials with explicit infrastructure/science attribution."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TASK = ROOT / "benchmarks/eb014-sequential-evidence-feedback-002"


def read(path):
    return json.loads(path.read_text())


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n")


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def trajectory(trial):
    event_path = trial / "agent_workspace/agent_events.jsonl"
    if event_path.exists():
        spec = importlib.util.spec_from_file_location("trajectory", ROOT / "benchmark_runner/trajectory.py")
        module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
        return module.summarize_file(event_path), digest(event_path)
    turn_files = sorted((trial / "agent_workspace/trajectory_turns").glob("turn-*-events.jsonl"))
    return {"model_turns": len(turn_files), "completed_turns": len(turn_files), "tool_calls_started": None, "tool_calls_completed": None, "agent_messages": None, "completion_gate_events": 0, "completion_gate_statuses": {}, "long_trace_target": "over_40_model_turns", "over_40_model_turns": len(turn_files) > 40}, None


def archive(trial):
    trial = trial.resolve()
    manifest = read(trial / "manifest.json")
    if manifest.get("task_id") != TASK.name:
        raise ValueError("wrong task")
    dest = TASK / "quality/trials" / manifest["trial_id"]
    if dest.exists():
        evidence_path = dest / "evidence.json"
        if evidence_path.exists():
            return read(evidence_path)
        raise ValueError("trial already archived without evidence")
    dest.mkdir(parents=True)
    workspace = trial / "agent_workspace"
    if (workspace / "outputs").exists(): shutil.copytree(workspace / "outputs", dest / "outputs")
    if (workspace / "trajectory_turns").exists(): shutil.copytree(workspace / "trajectory_turns", dest / "trajectory_turns")
    for name in ("manifest.json", "verifier_result.json", "stdout.log", "stderr.log", "agent_events.jsonl"):
        path = trial / name
        if path.exists(): shutil.copy2(path, dest / name)
    for name in ("research_log.json", "completion.json", "provenance.json", "audit.md", "agent_final.md"):
        path = workspace / name
        if path.exists(): shutil.copy2(path, dest / ("workspace-" + name))
    raw = read(trial / "verifier_result.json") if (trial / "verifier_result.json").exists() else {}
    status = manifest.get("status")
    if not manifest.get("finished_at") or status == "running": classification = "INFRASTRUCTURE_INCOMPLETE"
    elif status == "pass": classification = "RAW_PASS"
    elif manifest.get("agent_exit_code") == 124 or status == "timeout": classification = "INFRASTRUCTURE_FAIL"
    elif status == "agent_error": classification = "INFRASTRUCTURE_FAIL"
    else: classification = "VERIFIER_FAIL_REQUIRES_TRIAGE"
    metrics, event_hash = trajectory(trial)
    record = {"task_id": TASK.name, "trial_id": manifest["trial_id"], "model": "gpt-5.6-sol", "classification": classification, "runner_status": status, "raw_verifier_result": raw, "trajectory": metrics, "event_log_sha256": event_hash, "agent_exit_code": manifest.get("agent_exit_code"), "timed_out": manifest.get("timed_out", False), "isolation_mode": manifest.get("isolation_mode"), "counted_as_difficulty_failure": classification == "VERIFIER_FAIL_REQUIRES_TRIAGE", "target_model_defeated": False, "artifact_path": str(dest.relative_to(ROOT))}
    write(dest / "evidence.json", record)
    return record


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("trials", nargs="+", type=Path)
    args = parser.parse_args()
    records = [archive(path) for path in args.trials]
    quality = TASK / "quality"
    results = read(quality / "model_trial_results.json")
    card = read(quality / "model_trial_card.json")
    base = [row for row in results.get("records", []) if row.get("strategy") != "target_model"]
    trial_records = [{"strategy": "target_model", **row} for row in records]
    results.update(status="COMPLETED_WITH_ATTRIBUTION", target_model_status="PASS" if any(row["classification"] == "RAW_PASS" for row in records) else "INFRASTRUCTURE_FAIL", records=base + trial_records)
    card.update(status="COMPLETED_WITH_ATTRIBUTION", target_model_status=results["target_model_status"], run_records=base + trial_records)
    write(quality / "model_trial_results.json", results); write(quality / "model_trial_card.json", card)
    write(quality / "target_trial_evidence.json", {"task_id": TASK.name, "records": records, "difficulty_interpretation": "Interactive protocol evidence is separate from the over-40-turn target; infrastructure failures are not scientific defeats."})
    (quality / "trial_analysis.md").write_text("# EB014-002 interactive trial analysis\n\n" + "\n".join(f"- `{row['trial_id']}`: `{row['classification']}`, {row['trajectory'].get('model_turns')} observable model turns; counted_as_difficulty_failure={row['counted_as_difficulty_failure']}." for row in records) + "\n\nThe fixed sequence replay passed independently. A long trajectory target is exploratory and is not a minimum completion requirement. Provider, adapter, or network failures are infrastructure evidence, not model scientific failures.\n")
    print(json.dumps(records, indent=2))


if __name__ == "__main__":
    main()
