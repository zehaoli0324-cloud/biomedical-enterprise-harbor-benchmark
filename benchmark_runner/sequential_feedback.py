"""Host-side deterministic feedback controller for the EB014 interactive prototype."""
from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path


def load(path: Path):
    return json.loads(path.read_text())


def public_completion_check(
    workspace: str | Path,
    feedback_controller: FeedbackController | None = None,
) -> list[str]:
    """Check only agent-visible delivery rules; never inspect hidden scenario data."""
    workspace = Path(workspace)
    data = workspace / "data"
    outputs = workspace / "outputs"
    contract = load(data / "output_contract.json")
    rules = load(data / "rules.json")
    errors: list[str] = []
    payloads: dict[str, object] = {}
    for name in contract["required_files"]:
        path = outputs / name
        if not path.is_file():
            errors.append(f"missing required file: {name}")
            continue
        if name.endswith(".json"):
            try:
                payloads[name] = load(path)
            except (OSError, UnicodeError, json.JSONDecodeError) as exc:
                errors.append(f"invalid JSON in {name}: {exc}")
    log = payloads.get("research_log.json")
    if isinstance(log, dict):
        if not isinstance(log.get("events"), list) or not log["events"]:
            errors.append("research_log.events must be a nonempty array")
        claims = log.get(contract["claim_container"])
        if not isinstance(claims, dict) or any(key not in claims for key in contract["claim_fields"]):
            errors.append(f"research_log.{contract['claim_container']} is missing required claim fields")
    completion = payloads.get("completion.json")
    if isinstance(completion, dict):
        checks = completion.get("checks")
        if not isinstance(checks, dict) or any(checks.get(key) is not True for key in rules["required_checks"]):
            errors.append("completion.checks must map every required check to boolean true")
        allowed_reasons = contract["completion_schema"]["stop_reason"]["enum"]
        if completion.get("stop_reason") not in allowed_reasons:
            errors.append("completion.stop_reason must use a declared enum value")
        if completion.get("human_review_required") is not True:
            errors.append("completion.human_review_required must be boolean true")
        if completion.get("claim_boundary") != rules["claim_boundary"]:
            errors.append("completion.claim_boundary must match rules.claim_boundary")
    provenance = payloads.get("provenance.json")
    if isinstance(provenance, dict):
        expected_hashes = {
            path.name: hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted(data.glob("*.json"))
        }
        if provenance.get("input_sha256") != expected_hashes:
            errors.append("provenance.input_sha256 must hash every data/*.json file")
        if provenance.get("rules_version") != rules["rules_version"]:
            errors.append("provenance.rules_version must match rules.rules_version")
        if provenance.get("network") != "off":
            errors.append("provenance.network must be 'off'")
        if provenance.get("deterministic") is not True:
            errors.append("provenance.deterministic must be boolean true")
    audit = outputs / "audit.md"
    if audit.is_file() and not audit.read_text(encoding="utf-8").strip():
        errors.append("audit.md must be nonempty")
    if feedback_controller is not None:
        missing = feedback_controller.missing_completion_requirements()
        if missing:
            errors.append(
                "interactive evidence requirements are incomplete: " + ", ".join(missing)
            )
        if "stop" not in feedback_controller.used:
            errors.append("an accepted stop action is required before completion")
        if isinstance(completion, dict):
            checks = completion.get("checks")
            required = feedback_controller.required_completion_checks()
            if not isinstance(checks, dict) or set(checks) != required:
                errors.append(
                    "completion.checks must exactly cover every active interactive check; "
                    "expected keys: " + ", ".join(sorted(required))
                )
            elif any(checks[key] is not True for key in required):
                errors.append("completion.checks must map every active check to boolean true")
    if feedback_controller is not None and isinstance(log, dict):
        expected_claims = rules.get("final_claims")
        claims = log.get(contract["claim_container"])
        if isinstance(expected_claims, dict) and claims != expected_claims:
            errors.append(
                "research_log.final_claims must exactly match data/rules.json final_claims"
            )
    return errors


class FeedbackController:
    def __init__(self, hidden_task: str | Path, workspace: str | Path):
        self.hidden_task = Path(hidden_task)
        self.workspace = Path(workspace)
        self.outputs = self.workspace / "outputs"
        scenario_payload = load(self.hidden_task / "verifier_only/scenario.json")
        self.scenario = scenario_payload["outcomes"]
        self.actions = {row["id"]: row for row in load(self.workspace / "data/action_catalog.json")["actions"]}
        self.action_contract = load(self.workspace / "data/action_contract.json")
        self.rules = load(self.workspace / "data/rules.json")
        self.token_contract = self.action_contract.get("state_token")
        self.chain_seed = scenario_payload.get("chain_seed")
        if self.token_contract and not isinstance(self.chain_seed, str):
            raise ValueError("state-token protocol requires a hidden chain_seed")
        self.genesis_token = (
            self.token_contract.get("genesis", "GENESIS") if self.token_contract else None
        )
        self.last_token = self.genesis_token
        self.used: set[str] = set()
        self.states: set[str] = set()
        self.spent = 0
        self._restore_history()

    def _restore_history(self) -> None:
        """Rebuild public action state when a continuation reopens the workspace."""
        history = self.outputs / "feedback_history"
        if not history.is_dir():
            return
        for response_path in sorted(history.glob("round-*-response.json")):
            try:
                response = load(response_path)
            except (OSError, UnicodeError, json.JSONDecodeError):
                continue
            if response.get("accepted") is not True:
                continue
            request_path = response_path.with_name(response_path.name.replace("-response.json", "-request.json"))
            try:
                request = load(request_path)
            except (OSError, UnicodeError, json.JSONDecodeError):
                continue
            action_id = request.get("action_id")
            if not isinstance(action_id, str) or action_id in self.used:
                continue
            if self.token_contract:
                if request.get("prior_state_token") != self.last_token:
                    break
                expected_token = self._state_token(
                    self.last_token,
                    response.get("round"),
                    action_id,
                    response.get("outcome"),
                )
                if response.get("state_token") != expected_token:
                    break
                self.last_token = expected_token
            self.used.add(action_id)
            outcome = response.get("outcome")
            if outcome:
                self.states.add(outcome)
            self.spent += response.get("cost_charged") or 0

    def _state_token(self, prior_token, round_no, action_id, outcome) -> str:
        payload = "|".join(
            str(value)
            for value in (self.chain_seed, prior_token, round_no, action_id, outcome)
        )
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def resolved_checks(self) -> set[str]:
        return {
            self.actions[action_id]["resolves"]
            for action_id in self.used
            if isinstance(self.actions[action_id].get("resolves"), str)
        }

    def required_completion_checks(self) -> set[str]:
        required = set(self.rules.get("required_checks", []))
        for outcome in self.states:
            required.update(self.rules.get("conditional_checks", {}).get(outcome, []))
        return required

    def missing_completion_requirements(self, before_stop: bool = False) -> list[str]:
        required = self.required_completion_checks()
        if before_stop:
            required.discard("stop_rule")
        return sorted(required - self.resolved_checks())

    def submit(self, request: dict) -> dict:
        required = {"round", "action_id", "question_id", "rationale", "expected_information"}
        if self.token_contract:
            required.add("prior_state_token")
        missing = sorted(required - set(request))
        if missing:
            return {"accepted": False, "error": "missing request fields", "missing": missing}
        expected_round = len(self.used) + 1
        if request.get("round") != expected_round:
            return {
                "accepted": False,
                "error": "round must be the next contiguous integer",
                "expected_round": expected_round,
            }
        if self.token_contract and request.get("prior_state_token") != self.last_token:
            return {
                "accepted": False,
                "error": "prior_state_token does not match the latest observed response",
                "expected_round": expected_round,
            }
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
        if action_id == "stop":
            incomplete = self.missing_completion_requirements(before_stop=True)
            if incomplete:
                return {
                    "accepted": False,
                    "error": "evidence requirements are incomplete",
                    "incomplete_checks": incomplete,
                }
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
        if self.token_contract:
            self.last_token = self._state_token(
                self.last_token,
                request["round"],
                action_id,
                outcome,
            )
            response["state_token"] = self.last_token
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
    try:
        request = load(request_path)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        return {"accepted": False, "error": "invalid request JSON", "detail": str(exc)}
    if not isinstance(request, dict):
        return {"accepted": False, "error": "request must be a JSON object"}
    response = controller.submit(request)
    if response.get("accepted"):
        request_path.unlink()
    return response
