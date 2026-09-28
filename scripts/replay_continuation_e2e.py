#!/usr/bin/env python3
"""Author-side fixed-version replay of rejected -> continued -> accepted delivery."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from benchmark_runner.continuation_controller import (  # noqa: E402
    ContinuationController,
    GateReceipt,
    SubmissionState,
)
from benchmark_runner.sequential_feedback import (  # noqa: E402
    FeedbackController,
    public_completion_check,
)


PATH = ["audit_quality", "repair_quality", "compare_context", "independent_replicate", "orthogonal_assay", "stop"]


def write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def load_verifier(task: Path):
    spec = importlib.util.spec_from_file_location("eb014_e2e_verifier", task / "verifier.py")
    if spec is None or spec.loader is None:
        raise RuntimeError("unable to load verifier")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_submission(workspace: Path, *, handoff: bool) -> None:
    events = []
    history = workspace / "outputs/feedback_history"
    for round_no, action_id in enumerate(PATH, 1):
        response = json.loads((history / f"round-{round_no:03d}-response.json").read_text(encoding="utf-8"))
        events.append(
            {
                "round": round_no,
                "action_id": action_id,
                "observed_outcome": response["outcome"],
                "cost": response["cost_charged"],
                "question_id": "Q-CONTEXT",
                "next_question": "continue only if a registered blocker remains",
            }
        )
    write_json(
        workspace / "outputs/research_log.json",
        {
            "events": events,
            "final_claims": {
                "quality_status": "PASS",
                "context_status": "HOLD",
                "replication_status": "SUPPORTED",
                "claim_boundary": "registered_cohort_only",
            },
        },
    )
    checks = {
        "quality_audit": True,
        "context_comparison": True,
        "independent_replication": True,
        "stop_rule": True,
        "handoff": handoff,
    }
    write_json(
        workspace / "outputs/completion.json",
        {
            "checks": checks,
            "stop_reason": "bounded_handoff",
            "human_review_required": True,
            "claim_boundary": "registered_cohort_only",
        },
    )
    data = workspace / "data"
    write_json(
        workspace / "outputs/provenance.json",
        {
            "input_sha256": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(data.glob("*.json"))},
            "rules_version": "sequential-evidence-feedback-v1",
            "network": "off",
            "deterministic": True,
        },
    )
    (workspace / "outputs/audit.md").write_text(
        "Quality passed, context shift was observed, independent replication was recorded, "
        "and the final claim remains bounded to the registered cohort.\n",
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task", type=Path, default=ROOT / "benchmarks/eb014-sequential-evidence-feedback-002")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    task = args.task.resolve()
    workspace = args.out.resolve()
    if workspace.exists():
        raise SystemExit(f"output exists: {workspace}")
    workspace.mkdir(parents=True)
    shutil.copytree(task / "data", workspace / "data")
    (workspace / "outputs").mkdir()

    action_controller = FeedbackController(task, workspace)
    action_events = []
    for round_no, action_id in enumerate(PATH, 1):
        request = {
            "round": round_no,
            "action_id": action_id,
            "question_id": "Q-CONTEXT",
            "rationale": "resolve the current registered blocker",
            "expected_information": "quality, context or independent replication state",
        }
        response = action_controller.submit(request)
        if not response.get("accepted"):
            raise SystemExit(json.dumps(response, indent=2))
        action_events.append({"round": round_no, "action_id": action_id, "cost": response["cost_charged"]})

    ledger = workspace / "outputs/completion_attempts.json"
    gate = ContinuationController(max_attempts=3, ledger_path=ledger)
    write_submission(workspace, handoff=False)
    first_errors = public_completion_check(workspace)
    first = gate.submit(
        ContinuationController.fingerprint({"phase": "initial", "completion": (workspace / "outputs/completion.json").read_bytes().decode()}),
        lambda: GateReceipt(not first_errors, tuple(first_errors)),
    )
    if first.state is not SubmissionState.NEEDS_REVISION or not first_errors:
        raise AssertionError({"first": first.state.value, "errors": first_errors})

    # Reopen the same workspace to prove action budget and completion attempts persist.
    restored_actions = FeedbackController(task, workspace)
    restored_gate = ContinuationController.load(ledger)
    write_submission(workspace, handoff=True)
    second_errors = public_completion_check(workspace)
    second = restored_gate.submit(
        ContinuationController.fingerprint({"phase": "repair", "completion": (workspace / "outputs/completion.json").read_bytes().decode()}),
        lambda: GateReceipt(not second_errors, tuple(second_errors)),
    )
    verifier = load_verifier(task)
    passed, verifier_errors = verifier.verify(workspace / "outputs", workspace / "data")
    report = {
        "schema_version": "continuation_e2e_replay.v1",
        "task_id": task.name,
        "same_workspace": True,
        "action_events": action_events,
        "spent_before_reload": action_controller.spent,
        "spent_after_reload": restored_actions.spent,
        "used_actions_after_reload": sorted(restored_actions.used),
        "completion_events": [gate.summary()["events"][0], restored_gate.summary()["events"][1]],
        "first_submission": {"state": first.state.value, "issues": list(first.receipt.issues)},
        "second_submission": {"state": second.state.value, "issues": list(second.receipt.issues) if second.receipt else []},
        "public_completion_errors_after_repair": second_errors,
        "verifier": {"passed": passed, "errors": verifier_errors},
        "early_stop_legal": True,
        "scientific_score_feedback_exposed": False,
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    write_json(args.report, report)
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if second.state is SubmissionState.ACCEPTED and passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
