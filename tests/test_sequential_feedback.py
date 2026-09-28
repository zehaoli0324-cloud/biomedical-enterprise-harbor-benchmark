import importlib.util
import hashlib
import json
from pathlib import Path

from benchmark_runner.adapters.codex_sequential_feedback import _contract_timeout, _default_timeout, _model_environment, _resolve_timeout
from benchmark_runner.sequential_feedback import FeedbackController, public_completion_check

ROOT = Path(__file__).resolve().parents[1]
TASK = ROOT / "benchmarks/eb014-sequential-evidence-feedback-002"
LADDER_TASK = ROOT / "benchmarks/eb014-adaptive-evidence-ladder-003"


def make_workspace(tmp_path, task=TASK):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / "outputs").mkdir()
    (workspace / "data").mkdir()
    for path in (task / "data").glob("*.json"):
        (workspace / "data" / path.name).write_bytes(path.read_bytes())
    return workspace


def request(round_no, action_id, token=None):
    payload = {
        "round": round_no,
        "action_id": action_id,
        "question_id": "Q",
        "rationale": "Resolve the next evidence dependency.",
        "expected_information": "Return the declared observation.",
    }
    if token is not None:
        payload["prior_state_token"] = token
    return payload


def test_feedback_requires_observed_dependencies(tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / "outputs").mkdir()
    (workspace / "data").mkdir()
    for path in (TASK / "data").glob("*.json"):
        (workspace / "data" / path.name).write_bytes(path.read_bytes())
    controller = FeedbackController(TASK, workspace)
    rejected = controller.submit({"round": 1, "action_id": "compare_context", "question_id": "Q", "rationale": "", "expected_information": ""})
    assert rejected["accepted"] is False
    assert "dependency" in rejected["error"]
    accepted = controller.submit({"round": 1, "action_id": "audit_quality", "question_id": "Q", "rationale": "", "expected_information": "quality"})
    assert accepted["accepted"] is True
    assert accepted["outcome"] == "quality_issue"
    repaired = controller.submit({"round": 2, "action_id": "repair_quality", "question_id": "Q", "rationale": "", "expected_information": "quality"})
    assert repaired["accepted"] is True
    assert repaired["outcome"] == "quality_repaired"


def test_feedback_is_deterministic_and_budgeted(tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / "outputs").mkdir()
    (workspace / "data").mkdir()
    for path in (TASK / "data").glob("*.json"):
        (workspace / "data" / path.name).write_bytes(path.read_bytes())
    controller = FeedbackController(TASK, workspace)
    path = (
        "audit_quality",
        "repair_quality",
        "compare_context",
        "characterize_shift",
        "independent_replicate",
        "assay_screen",
        "adjudicate_assay",
        "orthogonal_assay",
        "external_validity_check",
    )
    for round_no, action in enumerate(path, 1):
        result = controller.submit({"round": round_no, "action_id": action, "question_id": "Q", "rationale": "", "expected_information": "state"})
        assert result["accepted"] is True
    assert controller.spent == 12
    stopped = controller.submit({"round": 10, "action_id": "stop", "question_id": "Q", "rationale": "", "expected_information": "stop"})
    assert stopped["remaining_budget"] == 0


def test_feedback_rejects_noncontiguous_round(tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / "outputs").mkdir()
    (workspace / "data").mkdir()
    for path in (TASK / "data").glob("*.json"):
        (workspace / "data" / path.name).write_bytes(path.read_bytes())
    controller = FeedbackController(TASK, workspace)
    result = controller.submit({"round": 2, "action_id": "audit_quality", "question_id": "Q", "rationale": "", "expected_information": "quality"})
    assert result["accepted"] is False
    assert result["expected_round"] == 1


def test_model_environment_does_not_expose_hidden_task(tmp_path, monkeypatch):
    monkeypatch.setenv("BENCHMARK_HIDDEN_TASK_DIR", "/hidden/scenario")
    prompt = tmp_path / "prompt.md"
    events = tmp_path / "events.jsonl"
    env = _model_environment(prompt, events)
    assert "BENCHMARK_HIDDEN_TASK_DIR" not in env
    assert env["BENCHMARK_PROMPT"] == str(prompt)
    assert env["BENCHMARK_EVENT_LOG"] == str(events)


def test_sequential_adapter_uses_declared_shared_model_budget(tmp_path):
    (tmp_path / "data").mkdir()
    (tmp_path / "data/research_contract.json").write_text('{"shared_model_seconds": 1200}\n')
    assert _contract_timeout(tmp_path) == 1200
    assert _default_timeout(tmp_path) == 1200


def test_sequential_adapter_has_bounded_interactive_default_without_contract(tmp_path):
    (tmp_path / "data").mkdir()
    assert _contract_timeout(tmp_path) is None
    assert _default_timeout(tmp_path) == 1700


def test_sequential_adapter_budget_is_capped_inside_outer_runner_timeout(tmp_path):
    (tmp_path / "data").mkdir()
    assert _resolve_timeout(tmp_path, None, {"BENCHMARK_TRIAL_TIMEOUT_SECONDS": "900"}) == 870
    assert _resolve_timeout(tmp_path, 1200, {"BENCHMARK_TRIAL_TIMEOUT_SECONDS": "900"}) == 870


def test_public_completion_check_returns_declared_schema_errors(tmp_path):
    workspace = tmp_path / "workspace"
    (workspace / "outputs").mkdir(parents=True)
    (workspace / "data").mkdir()
    for path in (TASK / "data").glob("*.json"):
        (workspace / "data" / path.name).write_bytes(path.read_bytes())
    (workspace / "outputs/research_log.json").write_text(json.dumps({"events": [{}], "final_claims": {key: "x" for key in ("quality_status", "context_status", "replication_status", "claim_boundary")}}))
    (workspace / "outputs/completion.json").write_text(json.dumps({"checks": {"quality_audit": "PASS"}, "stop_reason": "done", "human_review_required": True, "claim_boundary": "registered_cohort_only"}))
    (workspace / "outputs/provenance.json").write_text("{}")
    (workspace / "outputs/audit.md").write_text("audit")
    errors = public_completion_check(workspace)
    assert "completion.checks must map every required check to boolean true" in errors
    assert "completion.stop_reason must use a declared enum value" in errors
    assert "provenance.input_sha256 must hash every data/*.json file" in errors


def test_feedback_controller_restores_cumulative_budget_from_workspace_history(tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / "outputs").mkdir()
    (workspace / "data").mkdir()
    for path in (TASK / "data").glob("*.json"):
        (workspace / "data" / path.name).write_bytes(path.read_bytes())
    first = FeedbackController(TASK, workspace)
    accepted = first.submit({"round": 1, "action_id": "audit_quality", "question_id": "Q", "rationale": "", "expected_information": "quality"})
    assert accepted["accepted"] is True
    restored = FeedbackController(TASK, workspace)
    assert restored.spent == first.spent == accepted["cost_charged"]
    assert "audit_quality" in restored.used
    duplicate = restored.submit({"round": 1, "action_id": "audit_quality", "question_id": "Q", "rationale": "", "expected_information": "quality"})
    assert duplicate["accepted"] is False
    assert duplicate["error"] == "round must be the next contiguous integer"


def test_token_bound_ladder_rejects_early_stop_and_wrong_token(tmp_path):
    workspace = make_workspace(tmp_path, LADDER_TASK)
    controller = FeedbackController(LADDER_TASK, workspace)

    early = controller.submit(request(1, "stop", "GENESIS"))
    assert early["accepted"] is False
    assert early["error"] == "evidence requirements are incomplete"
    assert "quality_audit" in early["incomplete_checks"]

    wrong = controller.submit(request(1, "audit_quality", "fabricated"))
    assert wrong["accepted"] is False
    assert "prior_state_token" in wrong["error"]


def test_token_bound_ladder_chains_observed_responses(tmp_path):
    workspace = make_workspace(tmp_path, LADDER_TASK)
    controller = FeedbackController(LADDER_TASK, workspace)

    first = controller.submit(request(1, "audit_quality", "GENESIS"))
    assert first["accepted"] is True
    assert len(first["state_token"]) == 64
    second = controller.submit(request(2, "audit_pairing", first["state_token"]))
    assert second["accepted"] is True
    assert second["state_token"] != first["state_token"]

    restored = FeedbackController(LADDER_TASK, workspace)
    assert restored.last_token == second["state_token"]
    assert restored.used == {"audit_quality", "audit_pairing"}


def test_trusted_completion_gate_rejects_direct_final_artifacts(tmp_path):
    workspace = make_workspace(tmp_path, LADDER_TASK)
    outputs = workspace / "outputs"
    rules = json.loads((workspace / "data/rules.json").read_text())
    required = rules["required_checks"]
    (outputs / "research_log.json").write_text(json.dumps({
        "events": [{"round": 1}],
        "final_claims": {key: "x" for key in (
            "quality_status", "pairing_status", "primary_status", "context_status",
            "replication_status", "confounding_status", "robustness_status", "claim_boundary",
        )},
    }))
    (outputs / "completion.json").write_text(json.dumps({
        "checks": {key: True for key in required},
        "stop_reason": "bounded_handoff",
        "human_review_required": True,
        "claim_boundary": rules["claim_boundary"],
    }))
    hashes = {
        path.name: hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted((workspace / "data").glob("*.json"))
    }
    (outputs / "provenance.json").write_text(json.dumps({
        "input_sha256": hashes,
        "rules_version": rules["rules_version"],
        "network": "off",
        "deterministic": True,
    }))
    (outputs / "audit.md").write_text("Premature submission.")

    controller = FeedbackController(LADDER_TASK, workspace)
    errors = public_completion_check(workspace, controller)
    assert any("interactive evidence requirements are incomplete" in error for error in errors)
    assert "an accepted stop action is required before completion" in errors


def test_public_completion_gate_exposes_final_claim_contract(tmp_path):
    workspace = make_workspace(tmp_path, LADDER_TASK)
    outputs = workspace / "outputs"
    rules = json.loads((workspace / "data/rules.json").read_text())
    (outputs / "research_log.json").write_text(json.dumps({
        "events": [{"round": 1}],
        "final_claims": {**rules["final_claims"], "confounding_status": "HOLD"},
    }))
    errors = public_completion_check(workspace, FeedbackController(LADDER_TASK, workspace))
    assert "research_log.final_claims must exactly match data/rules.json final_claims" in errors


def test_token_bound_ladder_requires_all_observation_activated_actions(tmp_path):
    workspace = make_workspace(tmp_path, LADDER_TASK)
    controller = FeedbackController(LADDER_TASK, workspace)
    actions = (
        "audit_quality",
        "audit_pairing",
        "estimate_primary",
        "compare_context",
        "independent_replicate",
        "negative_control",
        "orthogonal_assay",
        "bridge_assay",
        "influence_analysis",
        "confounding_audit",
        "robustness_analysis",
        "stop",
    )
    token = "GENESIS"
    for round_no, action_id in enumerate(actions, 1):
        response = controller.submit(request(round_no, action_id, token))
        assert response["accepted"] is True, response
        token = response["state_token"]

    assert controller.spent == 18
    assert controller.missing_completion_requirements() == []
    assert controller.required_completion_checks() == {
        "quality_audit",
        "pairing_audit",
        "primary_estimate",
        "context_comparison",
        "independent_replication",
        "negative_control",
        "orthogonal_assay",
        "bridge_assay",
        "influence_analysis",
        "confounding_audit",
        "robustness_check",
        "stop_rule",
    }
