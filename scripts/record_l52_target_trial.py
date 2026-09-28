#!/usr/bin/env python3
"""Persist the L5.2 target-model trial and its reproducible artifact evidence."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TASK = ROOT / "benchmarks/eb010-adaptive-policy-regret-005"
TRIAL_ID = "eb010-adaptive-policy-regret-005-gpt56sol-001"
TRIAL = Path("/private/tmp/enterprise-l52-target-trials") / TRIAL_ID


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    manifest = json.loads((TRIAL / "manifest.json").read_text(encoding="utf-8"))
    verifier_result = json.loads((TRIAL / "verifier_result.json").read_text(encoding="utf-8"))
    outputs = TRIAL / "agent_workspace/outputs"
    artifacts = ("policy.json", "branches.tsv", "audit.md", "manifest.json")
    passed = manifest.get("status") == "pass" and verifier_result.get("passed") is True
    if not passed:
        raise RuntimeError("refusing to record L5.2 target trial because the formal runner result is not pass")

    started = datetime.fromisoformat(manifest["started_at"])
    finished = datetime.fromisoformat(manifest["finished_at"])
    target_record = {
        "strategy": "target_model",
        "model": "gpt-5.6-sol",
        "trial_id": TRIAL_ID,
        "status": "pass",
        "passed": True,
        "valid_difficulty_evidence": True,
        "runner_status": manifest["status"],
        "agent_exit_code": manifest.get("agent_exit_code"),
        "timed_out": bool(manifest.get("timed_out", False)),
        "verifier_status": manifest.get("verifier_status"),
        "duration_seconds": round((finished - started).total_seconds(), 3),
        "failure_attribution": None,
        "artifact_sha256": {name: sha256(outputs / name) for name in artifacts},
        "trial_dir": str(TRIAL),
    }

    for filename, records_key in (("model_trial_results.json", "records"), ("model_trial_card.json", "run_records")):
        path = TASK / "quality" / filename
        payload = json.loads(path.read_text(encoding="utf-8"))
        records = [row for row in payload.get(records_key, []) if row.get("strategy") != "target_model"]
        payload.update({"status": "TARGET_TRIAL_COMPLETE", "target_model_status": "PASS", records_key: records + [target_record]})
        path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    evidence = {
        "schema_version": "enterprise_target_trial_evidence.v1",
        "task_id": TASK.name,
        "model": "gpt-5.6-sol",
        "classification": "agent_completed_verifier_passed",
        "valid_difficulty_outcome": "pass",
        "trial": target_record,
        "verifier_revision_disclosure": {
            "issue": "missing branch was initially also classified as an unknown action",
            "resolution": "unknown_action now requires an explicit non-null unknown action id",
            "model_visible_inputs_changed": False,
            "artifact_content_changed": False,
            "formal_runner_verifier_status": "pass",
        },
        "release_effect": "blocked_pending_fixed_container_replay_and_practitioner_review",
    }
    (TASK / "quality/target_trial_evidence.json").write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")

    sop_path = TASK / "quality/sop_card.json"
    sop = json.loads(sop_path.read_text(encoding="utf-8"))
    sop["model_trial_status"] = "PASS"
    sop["release_blockers"] = ["fixed-container replay", "practitioner review"]
    sop_path.write_text(json.dumps(sop, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
