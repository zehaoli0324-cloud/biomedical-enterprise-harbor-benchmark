#!/usr/bin/env python3
"""Bounded submission-return loop using the existing full-turn Codex adapter."""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from benchmark_runner.research_gate import check, digest, save


def run_loop(command_factory, workspace, prompt, event_log, attempts_root, max_attempts, timeout):
    deadline = time.monotonic() + timeout
    original_prompt = prompt.read_text()
    original_inputs = {str(p.relative_to(workspace)): digest(p) for p in (workspace / "data").rglob("*") if p.is_file()}
    feedback, records = [], []
    attempts_root.mkdir(parents=True, exist_ok=False)
    with event_log.open("w") as consolidated:
        for attempt in range(1, max_attempts + 1):
            remaining = int(deadline - time.monotonic())
            # Reserve the public replay budget instead of silently overrunning it.
            if remaining <= 50:
                break
            stage = attempts_root / f"attempt-{attempt:02d}"
            stage.mkdir()
            current_prompt = stage / "prompt.md"
            current_prompt.write_text(original_prompt + (
                "\n\nYour previous submission was returned by the public completion gate. "
                "Existing work remains in outputs/. Resolve these actual missing requirements "
                "and resubmit; no scientific answer is provided:\n" + json.dumps(feedback)
                if feedback else ""))
            current_events = stage / "events.jsonl"
            env = dict(os.environ, BENCHMARK_PROMPT=str(current_prompt), BENCHMARK_EVENT_LOG=str(current_events))
            started = time.monotonic()
            process = subprocess.run(command_factory(remaining - 45), cwd=workspace, env=env, check=False)
            if current_events.exists():
                consolidated.write(current_events.read_text())
                consolidated.flush()
            if (workspace / "agent_final.md").exists():
                shutil.copy2(workspace / "agent_final.md", stage / "agent_final.md")
            shutil.copytree(workspace / "outputs", stage / "submission")
            record = {"attempt": attempt, "exit_code": process.returncode, "elapsed_seconds": time.monotonic() - started,
                      "artifact_sha256": {p.name: digest(p) for p in (stage / "submission").iterdir() if p.is_file()}}
            records.append(record)
            current_inputs = {str(p.relative_to(workspace)): digest(p) for p in (workspace / "data").rglob("*") if p.is_file()}
            if current_inputs != original_inputs:
                record["status"] = "input_integrity_error"
                break
            try:
                receipt = check(stage / "submission", workspace / "data", stage / "completion_check")
            except (OSError, ValueError, TypeError) as exc:
                receipt = {"accepted": False, "issues": ["completion_check_error:" + type(exc).__name__]}
            record["completion"] = {"accepted": receipt["accepted"], "issues": receipt["issues"]}
            if process.returncode:
                record["status"] = "timeout_output_complete" if process.returncode == 124 and receipt["accepted"] else "timeout" if process.returncode == 124 else "agent_error"
            else:
                record["status"] = "accepted" if receipt["accepted"] else "returned"
            consolidated.write(json.dumps({"type": "completion_gate", **record}) + "\n")
            consolidated.flush()
            if process.returncode or receipt["accepted"]:
                break
            feedback = receipt["issues"]
    status = records[-1]["status"] if records else "budget_exhausted"
    if status == "returned":
        status = "attempt_budget_exhausted" if len(records) == max_attempts else "time_budget_exhausted"
    result = {"status": status, "attempts": records, "max_attempts": max_attempts, "total_timeout_seconds": timeout,
              "continuation_mode": "fresh ephemeral model turn with preserved workspace and public gate feedback",
              "feedback_is_scientific_scoring": False}
    save(attempts_root / "result.json", result)
    return 0 if status == "accepted" else 124 if "timeout" in status or "time_budget" in status else 2


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True)
    parser.add_argument("--timeout", type=int, default=840)
    parser.add_argument("--max-attempts", type=int, default=3)
    args = parser.parse_args()
    if args.max_attempts < 1 or args.timeout < 60:
        parser.error("positive attempts and at least 60 seconds required")
    workspace = Path(os.environ["BENCHMARK_WORKSPACE"]).resolve()
    adapter = Path(__file__).with_name("codex_complete_turn.py")
    return run_loop(
        lambda seconds: [sys.executable, str(adapter), "--model", args.model, "--timeout", str(seconds)],
        workspace, Path(os.environ["BENCHMARK_PROMPT"]), Path(os.environ["BENCHMARK_EVENT_LOG"]),
        workspace.parent / "completion_attempts", args.max_attempts, args.timeout,
    )


if __name__ == "__main__":
    raise SystemExit(main())
