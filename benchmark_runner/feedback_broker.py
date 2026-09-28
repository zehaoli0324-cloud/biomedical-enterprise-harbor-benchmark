"""Host-side broker for stateful feedback when the agent runs in a container."""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from benchmark_runner.sequential_feedback import FeedbackController
else:
    from .sequential_feedback import FeedbackController


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def process_request_once(task: str | Path, workspace: str | Path) -> dict | None:
    """Process one pending public request without exposing the hidden task."""
    workspace = Path(workspace).resolve()
    request_path = workspace / "outputs/experiment_request.json"
    if not request_path.is_file():
        return None
    try:
        request = json.loads(request_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        response = {"accepted": False, "error": "invalid request JSON", "detail": str(exc), "round": None}
        _write_json(workspace / "outputs/experiment_feedback.json", response)
        request_path.unlink(missing_ok=True)
        return response
    if not isinstance(request, dict):
        response = {"accepted": False, "error": "request must be a JSON object", "round": None}
        _write_json(workspace / "outputs/experiment_feedback.json", response)
        request_path.unlink(missing_ok=True)
        return response

    round_no = request.get("round")
    request_archive = workspace / "outputs/feedback_history" / f"round-{int(round_no):03d}-request.json" if isinstance(round_no, int) else None
    if request_archive:
        _write_json(request_archive, request)
    controller = FeedbackController(Path(task).resolve(), workspace)
    response = controller.submit(request)
    if isinstance(response, dict):
        response.setdefault("round", request.get("round"))
        response.setdefault("action_id", request.get("action_id"))
    _write_json(workspace / "outputs/experiment_feedback.json", response)
    request_path.unlink(missing_ok=True)
    return response


def run_broker(task: str | Path, workspace: str | Path, pid: int, poll_interval: float = 0.2) -> int:
    """Serve requests until the agent exits and no request remains."""
    workspace = Path(workspace).resolve()
    request_path = workspace / "outputs/experiment_request.json"
    while True:
        processed = process_request_once(task, workspace)
        if processed is None:
            try:
                os.kill(pid, 0)
                alive = True
            except OSError:
                alive = False
            if not alive and not request_path.exists():
                return 0
            time.sleep(poll_interval)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--task", required=True, type=Path)
    parser.add_argument("--workspace", required=True, type=Path)
    parser.add_argument("--pid", required=True, type=int)
    args = parser.parse_args()
    raise SystemExit(run_broker(args.task, args.workspace, args.pid))
