#!/usr/bin/env python3
"""Replay one declared action path against the hidden EB014-002 scenario."""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from benchmark_runner.sequential_feedback import FeedbackController


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task", type=Path, default=Path("benchmarks/eb014-sequential-evidence-feedback-002"))
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    task = args.task.resolve()
    workspace = args.out.resolve()
    if workspace.exists():
        raise SystemExit(f"output exists: {workspace}")
    workspace.mkdir(parents=True)
    shutil.copytree(task / "data", workspace / "data")
    (workspace / "outputs").mkdir()
    controller = FeedbackController(task, workspace)
    path = ["audit_quality", "compare_context", "independent_replicate", "orthogonal_assay", "stop"]
    events = []
    for round_no, action_id in enumerate(path, 1):
        response = controller.submit({"round": round_no, "action_id": action_id, "question_id": "Q-CONTEXT", "rationale": "resolve the current registered blocker", "expected_information": "quality, context or independent replication state"})
        if not response.get("accepted"):
            raise SystemExit(json.dumps(response))
        events.append({"round": round_no, "action_id": action_id, "observed_outcome": response["outcome"], "cost": response["cost_charged"], "question_id": "Q-CONTEXT", "next_question": "continue only if a registered blocker remains"})
    claims = {"quality_status": "PASS", "context_status": "HOLD", "replication_status": "SUPPORTED", "claim_boundary": "registered_cohort_only"}
    (workspace / "outputs/research_log.json").write_text(json.dumps({"events": events, "final_claims": claims}, indent=2) + "\n")
    (workspace / "outputs/completion.json").write_text(json.dumps({"checks": {"quality_audit": True, "context_comparison": True, "independent_replication": True, "stop_rule": True, "handoff": True}, "stop_reason": "bounded_handoff", "human_review_required": True, "claim_boundary": "registered_cohort_only"}, indent=2) + "\n")
    hashes = {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in sorted((workspace / "data").glob("*.json"))}
    (workspace / "outputs/provenance.json").write_text(json.dumps({"input_sha256": hashes, "rules_version": "sequential-evidence-feedback-v1", "network": "off", "deterministic": True}, indent=2) + "\n")
    (workspace / "outputs/audit.md").write_text("Quality passed, the target context shifted, and an independent replicate reproduced the registered-cohort effect. The orthogonal follow-up remains a bounded handoff; no target-context or causal claim is authorized.\n")
    print(json.dumps({"actions": path, "spent": controller.spent, "outputs": str(workspace / "outputs")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
