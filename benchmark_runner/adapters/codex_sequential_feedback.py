#!/usr/bin/env python3
"""Run sequential model turns with host-side feedback between turns.

This is a local protocol adapter. The hidden scenario is supplied by the runner
side and is not mounted into the agent workspace; production use still needs
container or service isolation.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from benchmark_runner.sequential_feedback import FeedbackController, process_request
from benchmark_runner.trajectory import summarize
from codex_gpt55 import SUPPORTED_MODELS, build_command


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True, choices=sorted(SUPPORTED_MODELS))
    parser.add_argument("--timeout", type=int, default=840)
    parser.add_argument("--max-turns", type=int, default=20)
    args = parser.parse_args()
    workspace = Path(os.environ["BENCHMARK_WORKSPACE"]).resolve()
    hidden_task = Path(os.environ["BENCHMARK_HIDDEN_TASK_DIR"]).resolve()
    base_prompt = Path(os.environ["BENCHMARK_PROMPT"]).read_text()
    base_prompt += "\n\nSTRICT PATH RULE: every required final artifact and every experiment request must be under outputs/. Files at the workspace root do not count."
    event_path = Path(os.environ["BENCHMARK_EVENT_LOG"])
    codex = shutil.which("codex")
    if not codex:
        raise SystemExit("codex executable missing")
    controller = FeedbackController(hidden_task, workspace)
    trajectory = workspace / "trajectory_turns"
    trajectory.mkdir(exist_ok=True)
    all_events = [{"type": "model_config", "model": args.model, "completion_policy": "sequential_feedback_process_exit"}]
    prompt = base_prompt
    exit_code = 0
    for turn in range(1, args.max_turns + 1):
        turn_prompt = trajectory / f"turn-{turn:03d}-prompt.md"
        turn_prompt.write_text(prompt)
        turn_events = trajectory / f"turn-{turn:03d}-events.jsonl"
        turn_final = trajectory / f"turn-{turn:03d}-final.md"
        env = dict(os.environ, BENCHMARK_PROMPT=str(turn_prompt), BENCHMARK_EVENT_LOG=str(turn_events))
        try:
            process = subprocess.run(
                build_command(codex, workspace, turn_final, args.model),
                cwd=workspace, env=env, input=prompt, text=True, capture_output=False,
                timeout=args.timeout,
            )
        except subprocess.TimeoutExpired:
            all_events.append({"type": "turn.timeout", "round": turn, "timeout_seconds": args.timeout})
            exit_code = 124
            break
        if turn_events.exists():
            turn_rows = [json.loads(line) for line in turn_events.read_text().splitlines() if line.strip()]
            all_events.extend(turn_rows)
        if process.returncode:
            exit_code = process.returncode
            break
        response = process_request(controller)
        if response is not None:
            all_events.append({"type": "feedback.response", "round": turn, "response": response})
            if response.get("accepted") and (workspace / "outputs/completion.json").is_file() and (workspace / "outputs/research_log.json").is_file():
                all_events.append({"type": "completion.requested", "round": turn})
                break
            if not response.get("accepted"):
                prompt = base_prompt + "\n\nThe environment rejected the last request for this public reason; repair it and continue:\n" + json.dumps(response)
            else:
                prompt = base_prompt + "\n\nA new environment observation is available in outputs/experiment_feedback.json. Update the research log and choose the next legal action. Do not infer hidden scores."
        elif (workspace / "outputs/completion.json").is_file() and (workspace / "outputs/research_log.json").is_file():
            all_events.append({"type": "completion.requested", "round": turn})
            break
        else:
            prompt = base_prompt + "\n\nNo valid experiment request or complete submission was found. Continue the research loop and submit exactly one legal experiment_request.json."
        all_events.append({"type": "turn.completed", "round": turn})
    event_path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in all_events))
    (workspace / "trajectory_summary.json").write_text(json.dumps(summarize(all_events), indent=2) + "\n")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
