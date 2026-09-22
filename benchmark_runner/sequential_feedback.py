"""Host-side deterministic feedback controller for the EB014 interactive prototype."""
from __future__ import annotations

import json
import shutil
from pathlib import Path


def load(path: Path):
    return json.loads(path.read_text())


class FeedbackController:
    def __init__(self, hidden_task: str | Path, workspace: str | Path):
        self.hidden_task = Path(hidden_task)
        self.workspace = Path(workspace)
        self.outputs = self.workspace / "outputs"
        self.scenario = load(self.hidden_task / "verifier_only/scenario.json")["outcomes"]
        self.actions = {row["id"]: row for row in load(self.workspace / "data/action_catalog.json")["actions"]}
        self.rules = load(self.workspace / "data/rules.json")
        self.used: set[str] = set()
        self.states: set[str] = set()
        self.spent = 0

    def submit(self, request: dict) -> dict:
        required = {"round", "action_id", "question_id", "rationale", "expected_information"}
        missing = sorted(required - set(request))
        if missing:
            return {"accepted": False, "error": "missing request fields", "missing": missing}
        action_id = request["action_id"]
        action = self.actions.get(action_id)
        if not action:
            return {"accepted": False, "error": "unknown action"}
        if action_id in self.used:
            return {"accepted": False, "error": "action already used"}
        if not set(action.get("requires", [])).issubset(self.states):
            return {"accepted": False, "error": "action dependency not observed"}
        requires_any = action.get("requires_any", [])
        if requires_any and not self.states.intersection(requires_any):
            return {"accepted": False, "error": "action dependency not observed"}
        outcome = "stopped" if action_id == "stop" else self.scenario.get(action_id, {}).get("outcome")
        cost = 0 if action_id == "stop" else self.scenario.get(action_id, {}).get("cost")
        if self.spent + (cost or 0) > self.rules["budget"]:
            return {"accepted": False, "error": "budget exceeded"}
        self.used.add(action_id)
        self.states.add(outcome)
        self.spent += cost or 0
        measurements = [] if action_id == "stop" else self.scenario.get(action_id, {}).get("measurements", [])
        response = {
            "round": request["round"], "action_id": action_id, "outcome": outcome,
            "cost_charged": cost, "observed_measurements": measurements,
            "remaining_budget": self.rules["budget"] - self.spent,
            "accepted": True,
        }
        history = self.outputs / "feedback_history"
        history.mkdir(parents=True, exist_ok=True)
        (history / f"round-{request['round']:03d}-request.json").write_text(json.dumps(request, indent=2) + "\n")
        (history / f"round-{request['round']:03d}-response.json").write_text(json.dumps(response, indent=2) + "\n")
        (self.outputs / "experiment_feedback.json").write_text(json.dumps(response, indent=2) + "\n")
        return response


def process_request(controller: FeedbackController) -> dict | None:
    request_path = controller.outputs / "experiment_request.json"
    if not request_path.is_file():
        return None
    request = load(request_path)
    response = controller.submit(request)
    if response.get("accepted"):
        request_path.unlink()
    return response
