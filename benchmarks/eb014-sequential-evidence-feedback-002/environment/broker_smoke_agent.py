"""Deterministic container-side agent used only for broker/isolation replay."""
from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path


ROOT = Path("/workspace")
OUTPUTS = ROOT / "outputs"
DATA = ROOT / "data"


def write_json(path: Path, payload: object) -> None:
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def request(round_no: int, action_id: str, question_id: str) -> dict:
    write_json(
        OUTPUTS / "experiment_request.json",
        {
            "round": round_no,
            "action_id": action_id,
            "question_id": question_id,
            "rationale": "Use the latest public observation to resolve the next registered question.",
            "expected_information": "The declared public outcome and cost for this action.",
        },
    )
    feedback = OUTPUTS / "experiment_feedback.json"
    deadline = time.monotonic() + 120
    while time.monotonic() < deadline:
        if feedback.is_file():
            try:
                payload = json.loads(feedback.read_text(encoding="utf-8"))
                if payload.get("round") == round_no and payload.get("action_id") == action_id:
                    return payload
            except (OSError, UnicodeError, json.JSONDecodeError):
                pass
        time.sleep(0.1)
    raise TimeoutError(f"no broker response for round {round_no}")


def main() -> int:
    events = []
    quality = request(1, "audit_quality", "Q-QUALITY")
    events.append({"round": 1, "action_id": "audit_quality", "observed_outcome": quality["outcome"], "cost": quality["cost_charged"], "question_id": "Q-QUALITY", "next_question": "context or quality repair"})
    if quality["outcome"] == "quality_issue":
        repaired = request(2, "repair_quality", "Q-QUALITY")
        events.append({"round": 2, "action_id": "repair_quality", "observed_outcome": repaired["outcome"], "cost": repaired["cost_charged"], "question_id": "Q-QUALITY", "next_question": "context"})
        next_round = 3
    else:
        next_round = 2
    context = request(next_round, "compare_context", "Q-CONTEXT")
    events.append({"round": next_round, "action_id": "compare_context", "observed_outcome": context["outcome"], "cost": context["cost_charged"], "question_id": "Q-CONTEXT", "next_question": "handoff if shifted"})
    round_no = next_round + 1
    if context["outcome"] == "context_shift":
        orthogonal = request(round_no, "orthogonal_assay", "Q-CONTEXT")
        events.append({"round": round_no, "action_id": "orthogonal_assay", "observed_outcome": orthogonal["outcome"], "cost": orthogonal["cost_charged"], "question_id": "Q-CONTEXT", "next_question": "independent replication"})
        round_no += 1
    replicate = request(round_no, "independent_replicate", "Q-REPLICATION")
    events.append({"round": round_no, "action_id": "independent_replicate", "observed_outcome": replicate["outcome"], "cost": replicate["cost_charged"], "question_id": "Q-REPLICATION", "next_question": "stop"})
    round_no += 1
    stopped = request(round_no, "stop", "Q-CONTEXT")
    events.append({"round": round_no, "action_id": "stop", "observed_outcome": stopped["outcome"], "cost": stopped["cost_charged"], "question_id": "Q-CONTEXT", "next_question": "finalize"})
    write_json(OUTPUTS / "research_log.json", {"events": events, "final_claims": {"quality_status": "PASS", "context_status": "HOLD", "replication_status": "SUPPORTED", "claim_boundary": "registered_cohort_only"}})
    write_json(OUTPUTS / "completion.json", {"checks": {"quality_audit": True, "context_comparison": True, "independent_replication": True, "stop_rule": True, "handoff": True}, "stop_reason": "evidence_complete", "human_review_required": True, "claim_boundary": "registered_cohort_only"})
    write_json(OUTPUTS / "provenance.json", {"input_sha256": {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in sorted(DATA.glob("*.json"))}, "rules_version": "sequential-evidence-feedback-v1", "network": "off", "deterministic": True})
    (OUTPUTS / "audit.md").write_text("Container broker smoke completed using only public feedback. The final claim remains bounded to the registered cohort and requires human review.\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
