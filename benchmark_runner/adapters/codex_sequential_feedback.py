#!/usr/bin/env python3
"""Run sequential model turns with host-side feedback between turns.

This is a local protocol adapter. The hidden scenario is supplied by the runner
side and is not mounted into the agent workspace; production use still needs
container or service isolation.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from benchmark_runner.sequential_feedback import FeedbackController, process_request, public_completion_check
from benchmark_runner.continuation_controller import ContinuationController, GateReceipt, SubmissionState, snapshot_submission
from benchmark_runner.trajectory import summarize
from benchmark_runner.adapters.codex_gpt55 import SUPPORTED_MODELS, build_command


def _request_signature(path: Path) -> bytes | None:
    try:
        return path.read_bytes()
    except OSError:
        return None


def _required_final_files(workspace: Path) -> tuple[str, ...]:
    """Return the public contract's final files, with a conservative fallback."""
    fallback = ("research_log.json", "completion.json", "provenance.json", "audit.md")
    try:
        contract = json.loads((workspace / "data/output_contract.json").read_text(encoding="utf-8"))
        required = contract.get("required_files")
        if (
            isinstance(required, list)
            and required
            and all(isinstance(name, str) and name and Path(name).name == name for name in required)
        ):
            return tuple(required)
    except (OSError, UnicodeError, json.JSONDecodeError):
        pass
    return fallback


def _completion_submission_fingerprint(workspace: Path) -> str:
    """Hash only visible final artifacts so retries remain deterministic."""
    files = {}
    for name in _required_final_files(workspace):
        path = workspace / "outputs" / name
        files[name] = hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None
    return ContinuationController.fingerprint(files)


def _final_artifacts_ready(workspace: Path, initial_fingerprint: str) -> bool:
    required = _required_final_files(workspace)
    return (
        all((workspace / "outputs" / name).is_file() for name in required)
        and _completion_submission_fingerprint(workspace) != initial_fingerprint
    )


def _run_completion_gate(
    controller: ContinuationController,
    workspace: Path,
    feedback_controller: FeedbackController,
):
    errors = public_completion_check(workspace, feedback_controller)
    event = controller.submit(
        _completion_submission_fingerprint(workspace),
        lambda: GateReceipt(not errors, tuple(errors)),
    )
    return event, errors


def _model_environment(turn_prompt: Path, turn_events: Path) -> dict[str, str]:
    env = dict(os.environ)
    env.pop("BENCHMARK_HIDDEN_TASK_DIR", None)
    env["BENCHMARK_PROMPT"] = str(turn_prompt)
    env["BENCHMARK_EVENT_LOG"] = str(turn_events)
    return env


def _contract_timeout(workspace: Path) -> int | None:
    """Read the task's declared shared model budget when one is available."""
    contract = workspace / "data/research_contract.json"
    if not contract.is_file():
        return None
    try:
        value = json.loads(contract.read_text(encoding="utf-8")).get("shared_model_seconds")
        return int(value) if isinstance(value, (int, float)) and value >= 60 else None
    except (OSError, UnicodeError, json.JSONDecodeError, TypeError, ValueError):
        return None


def _default_timeout(workspace: Path) -> int:
    """Prefer the public task budget; otherwise allow a bounded interactive run."""
    declared = _contract_timeout(workspace)
    if declared is not None:
        return declared
    return 1700


def _resolve_timeout(workspace: Path, explicit: int | None, environment: dict[str, str] | None = None) -> int:
    """Resolve one shared budget and keep it inside the outer runner deadline."""
    environment = environment or os.environ
    declared = explicit
    if declared is None:
        declared = int(environment.get("BENCHMARK_SHARED_MODEL_SECONDS", _default_timeout(workspace)))
    outer_raw = environment.get("BENCHMARK_TRIAL_TIMEOUT_SECONDS")
    if outer_raw:
        try:
            outer = int(outer_raw)
        except ValueError:
            outer = None
        if outer is not None:
            declared = min(declared, outer - 30)
    return declared


def _broker_mode() -> bool:
    return os.environ.get("BENCHMARK_FEEDBACK_BROKER") == "1"


def _wait_for_broker_response(workspace: Path, expected_round: int, deadline: float) -> dict | None:
    """Wait for the host broker to answer the request emitted by this turn."""
    history = workspace / "outputs/feedback_history"
    feedback = workspace / "outputs/experiment_feedback.json"
    while time.monotonic() < deadline:
        request_path = history / f"round-{expected_round:03d}-request.json"
        response_path = history / f"round-{expected_round:03d}-response.json"
        if response_path.is_file():
            try:
                return json.loads(response_path.read_text(encoding="utf-8"))
            except (OSError, UnicodeError, json.JSONDecodeError):
                pass
        if request_path.is_file() and feedback.is_file():
            try:
                response = json.loads(feedback.read_text(encoding="utf-8"))
                if response.get("round") == expected_round:
                    return response
            except (OSError, UnicodeError, json.JSONDecodeError):
                pass
        if all((workspace / "outputs" / name).is_file() for name in _required_final_files(workspace)):
            return None
        time.sleep(0.2)
    return None


def _stop_process(process: subprocess.Popen[str]) -> None:
    if process.poll() is not None:
        return
    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=5)


def _run_model_turn(
    codex: str,
    workspace: Path,
    prompt: str,
    turn_prompt: Path,
    turn_events: Path,
    turn_final: Path,
    model: str,
    deadline: float,
    turn_timeout: int,
) -> tuple[int, bool]:
    request_path = workspace / "outputs/experiment_request.json"
    initial_request = _request_signature(request_path)
    initial_final_fingerprint = _completion_submission_fingerprint(workspace)
    turn_deadline = min(deadline, time.monotonic() + turn_timeout)
    turn_stderr = turn_events.with_name(turn_events.stem + "-stderr.log")
    with turn_events.open("w", encoding="utf-8") as events, turn_stderr.open("w", encoding="utf-8") as errors:
        process = subprocess.Popen(
            build_command(codex, workspace, turn_final, model),
            cwd=workspace,
            env=_model_environment(turn_prompt, turn_events),
            stdin=subprocess.PIPE,
            stdout=events,
            stderr=errors,
            text=True,
        )
        if process.stdin is None:
            raise RuntimeError("failed to open Codex CLI stdin")
        process.stdin.write(prompt)
        process.stdin.close()
        artifact_ready_at: float | None = None
        stopped_for_artifact = False
        timed_out = False
        while process.poll() is None:
            request_changed = _request_signature(request_path) not in (None, initial_request)
            final_ready = _final_artifacts_ready(workspace, initial_final_fingerprint)
            if request_changed or final_ready:
                artifact_ready_at = artifact_ready_at or time.monotonic()
                if time.monotonic() - artifact_ready_at >= 1.0:
                    stopped_for_artifact = True
                    _stop_process(process)
                    break
            else:
                artifact_ready_at = None
            if time.monotonic() >= turn_deadline:
                timed_out = True
                _stop_process(process)
                break
            time.sleep(0.2)
        returncode = process.wait()
    if turn_stderr.stat().st_size:
        print(turn_stderr.read_text(encoding="utf-8", errors="replace"), file=sys.stderr, end="")
    if stopped_for_artifact:
        return 0, False
    return returncode, timed_out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True, choices=sorted(SUPPORTED_MODELS))
    parser.add_argument("--timeout", type=int, default=None, help="total adapter budget in seconds")
    parser.add_argument("--turn-timeout", type=int, default=360)
    parser.add_argument("--finalization-timeout", type=int, default=480)
    parser.add_argument("--max-turns", type=int, default=20)
    args = parser.parse_args()
    workspace = Path(os.environ["BENCHMARK_WORKSPACE"]).resolve()
    args.timeout = _resolve_timeout(workspace, args.timeout)
    if args.timeout < 60:
        parser.error("--timeout must be at least 60 seconds")
    broker_mode = _broker_mode()
    hidden_task = None if broker_mode else Path(os.environ["BENCHMARK_HIDDEN_TASK_DIR"]).resolve()
    base_prompt = Path(os.environ["BENCHMARK_PROMPT"]).read_text()
    base_prompt += "\n\nSTRICT PATH RULE: every required final artifact and every experiment request must be under outputs/. Files at the workspace root do not count."
    event_path = Path(os.environ["BENCHMARK_EVENT_LOG"])
    codex = shutil.which("codex")
    if not codex:
        raise SystemExit("codex executable missing")
    controller = None if broker_mode else FeedbackController(hidden_task, workspace)
    completion_controller = ContinuationController.load(
        workspace / "outputs/completion_attempts.json", max_attempts=3
    )
    accepted_snapshot = workspace / "accepted_submission"
    trajectory = workspace / "trajectory_turns"
    trajectory.mkdir(exist_ok=True)
    all_events = [{"type": "model_config", "model": args.model, "completion_policy": "sequential_feedback_process_exit"}]
    prompt = base_prompt
    exit_code = 0
    finalization_pending = False
    deadline = time.monotonic() + args.timeout
    for turn in range(1, args.max_turns + 1):
        if time.monotonic() >= deadline:
            all_events.append({"type": "adapter.timeout", "timeout_seconds": args.timeout})
            exit_code = 124
            break
        turn_prompt = trajectory / f"turn-{turn:03d}-prompt.md"
        turn_prompt.write_text(prompt)
        turn_events = trajectory / f"turn-{turn:03d}-events.jsonl"
        turn_final = trajectory / f"turn-{turn:03d}-final.md"
        current_turn_timeout = (
            args.finalization_timeout if finalization_pending else args.turn_timeout
        )
        expected_round = len(list((workspace / "outputs/feedback_history").glob("*-response.json"))) + 1
        returncode, turn_timed_out = _run_model_turn(
            codex,
            workspace,
            prompt,
            turn_prompt,
            turn_events,
            turn_final,
            args.model,
            deadline,
            current_turn_timeout,
        )
        if turn_events.exists():
            turn_rows = [json.loads(line) for line in turn_events.read_text().splitlines() if line.strip()]
            all_events.extend(turn_rows)
        if broker_mode:
            response = _wait_for_broker_response(workspace, expected_round, deadline) if (workspace / "outputs/feedback_history" / f"round-{expected_round:03d}-request.json").exists() or (workspace / "outputs/experiment_request.json").exists() else None
        else:
            response = process_request(controller)
        if response is not None:
            all_events.append({"type": "feedback.response", "round": turn, "response": response})
            if response.get("accepted") and (workspace / "outputs/completion.json").is_file() and (workspace / "outputs/research_log.json").is_file():
                gate_event, completion_errors = _run_completion_gate(
                    completion_controller, workspace, controller
                )
                if gate_event.state is SubmissionState.ACCEPTED:
                    if not accepted_snapshot.exists():
                        manifest = snapshot_submission(workspace / "outputs", accepted_snapshot)
                        all_events.append({"type": "accepted_snapshot", "round": turn, "files": len(manifest)})
                    all_events.append({"type": "completion_gate", "round": turn, "attempt": gate_event.attempt, "status": "accepted"})
                    break
                terminal_stop = gate_event.state in {SubmissionState.STOPPED_BUDGET, SubmissionState.STOPPED_NO_PROGRESS}
                status = "stopped_budget" if gate_event.state is SubmissionState.STOPPED_BUDGET else ("stopped_no_progress" if terminal_stop else "returned")
                all_events.append({"type": "completion_gate", "round": turn, "attempt": gate_event.attempt, "status": status, "errors": completion_errors, "reason": gate_event.reason})
                if terminal_stop:
                    break
                prompt = base_prompt + "\n\nThe public completion check returned these issues:\n" + json.dumps(completion_errors, indent=2)
            elif not response.get("accepted"):
                prompt = base_prompt + "\n\nThe environment rejected the last request for this public reason; repair it and continue:\n" + json.dumps(response)
            elif response.get("action_id") == "stop":
                finalization_pending = True
                required_files = ", ".join(
                    f"outputs/{name}" for name in _required_final_files(workspace)
                )
                prompt = (
                    base_prompt
                    + "\n\nThe environment accepted the stop action. Do not submit another experiment and do not "
                    "re-read the trajectory logs. Append the stop response already present in "
                    "outputs/experiment_feedback.json to outputs/research_log.json, then immediately write "
                    + required_files
                    + ". Hash data/*.json for provenance and use the public output contract exactly, "
                    "including research_log.final_claims."
                )
            else:
                prompt = base_prompt + "\n\nA new environment observation is available in outputs/experiment_feedback.json. Update the research log and choose the next legal action. Do not infer hidden scores."
        elif (workspace / "outputs/completion.json").is_file() and (workspace / "outputs/research_log.json").is_file():
            gate_event, completion_errors = _run_completion_gate(
                completion_controller, workspace, controller
            )
            if gate_event.state is SubmissionState.ACCEPTED:
                if not accepted_snapshot.exists():
                    manifest = snapshot_submission(workspace / "outputs", accepted_snapshot)
                    all_events.append({"type": "accepted_snapshot", "round": turn, "files": len(manifest)})
                all_events.append({"type": "completion_gate", "round": turn, "attempt": gate_event.attempt, "status": "accepted"})
                break
            if gate_event.state in {SubmissionState.STOPPED_BUDGET, SubmissionState.STOPPED_NO_PROGRESS}:
                status = "stopped_budget" if gate_event.state is SubmissionState.STOPPED_BUDGET else "stopped_no_progress"
                all_events.append({"type": "completion_gate", "round": turn, "attempt": gate_event.attempt, "status": status, "errors": completion_errors, "reason": gate_event.reason})
                break
            if completion_errors:
                all_events.append({"type": "completion_gate", "round": turn, "attempt": gate_event.attempt, "status": "returned", "errors": completion_errors})
                prompt = (
                    base_prompt
                    + "\n\nThe public completion check returned this submission. Repair only these declared contract issues, "
                    "preserve the observed action history, and resubmit the final files:\n"
                    + json.dumps(completion_errors, indent=2)
                )
        else:
            prompt = base_prompt + "\n\nNo valid experiment request or complete submission was found. Continue the research loop and submit exactly one legal experiment_request.json."
        if turn_timed_out:
            all_events.append({"type": "turn.timeout", "round": turn, "timeout_seconds": current_turn_timeout, "request_processed": response is not None})
            if response is None or time.monotonic() >= deadline:
                exit_code = 124
                break
        elif returncode:
            exit_code = returncode
            break
        all_events.append({"type": "turn.completed", "round": turn})
    event_path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in all_events))
    (workspace / "trajectory_summary.json").write_text(json.dumps(summarize(all_events), indent=2) + "\n")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
