#!/usr/bin/env python3
"""Persist L5.3 target trials and unchanged-artifact replay evidence."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TASK = ROOT / "benchmarks/eb010-distributional-policy-stress-006"
FIRST_ID = "eb010-distributional-policy-stress-006-gpt56sol-001"
SECOND_ID = "eb010-distributional-policy-stress-006-gpt56sol-002"
FIRST = Path("/private/tmp/enterprise-l53-target-trials") / FIRST_ID
SECOND = Path("/private/tmp/enterprise-l53-target-trials-v2") / SECOND_ID


def load(path: Path) -> tuple[dict, dict]:
    return json.loads((path / "manifest.json").read_text()), json.loads((path / "verifier_result.json").read_text())


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def elapsed(manifest: dict) -> float:
    return round((datetime.fromisoformat(manifest["finished_at"]) - datetime.fromisoformat(manifest["started_at"])).total_seconds(), 3)


def main() -> int:
    first_manifest, first_result = load(FIRST)
    second_manifest, second_result = load(SECOND)
    outputs = SECOND / "agent_workspace/outputs"
    artifact_names = ("policy.json", "branches.tsv", "profiles.tsv", "audit.md", "manifest.json")
    history = [
        {
            "strategy": "target_model",
            "model": "gpt-5.6-sol",
            "trial_id": FIRST_ID,
            "status": "invalid_contract_defect",
            "passed": False,
            "valid_difficulty_evidence": False,
            "runner_status": first_manifest["status"],
            "agent_exit_code": first_manifest.get("agent_exit_code"),
            "timed_out": bool(first_manifest.get("timed_out", False)),
            "duration_seconds": elapsed(first_manifest),
            "failure_attribution": "undocumented branch container, numeric rounding and lexical equivalence",
            "unchanged_artifact_replay": "pass",
            "original_verifier_error_count": len(first_result.get("errors", [])),
        },
        {
            "strategy": "target_model",
            "model": "gpt-5.6-sol",
            "trial_id": SECOND_ID,
            "status": "pass_after_contract_replay",
            "passed": True,
            "valid_difficulty_evidence": True,
            "runner_status": "verifier_fail_then_unchanged_artifact_replay_pass",
            "original_runner_status": second_manifest["status"],
            "agent_exit_code": second_manifest.get("agent_exit_code"),
            "timed_out": bool(second_manifest.get("timed_out", False)),
            "duration_seconds": elapsed(second_manifest),
            "failure_attribution": "one-unit-last-place intermediate-rounding verifier boundary",
            "original_verifier_errors": second_result.get("errors", []),
            "artifact_sha256": {name: sha256(outputs / name) for name in artifact_names},
            "trial_dir": str(SECOND),
        },
    ]
    for filename, key in (("model_trial_results.json", "records"), ("model_trial_card.json", "run_records")):
        path = TASK / "quality" / filename
        payload = json.loads(path.read_text())
        records = [row for row in payload.get(key, []) if row.get("strategy") != "target_model"]
        payload.update({"status": "TARGET_TRIAL_COMPLETE", "target_model_status": "PASS_AFTER_CONTRACT_REPLAY", key: records + history})
        path.write_text(json.dumps(payload, indent=2) + "\n")
    evidence = {
        "schema_version": "enterprise_target_trial_evidence.v1",
        "task_id": TASK.name,
        "model": "gpt-5.6-sol",
        "classification": "agent_completed_verifier_passed_after_contract_replay",
        "valid_difficulty_outcome": "pass",
        "contract_defects_are_not_difficulty_evidence": True,
        "scientific_result": {"selected_policy": "P-ADAPT", "nominal_winner": "P-NOMINAL", "robust_winner": "P-ADAPT"},
        "trials": history,
        "release_effect": "blocked_pending_fixed_container_replay_and_practitioner_review",
    }
    (TASK / "quality/target_trial_evidence.json").write_text(json.dumps(evidence, indent=2) + "\n")
    sop_path = TASK / "quality/sop_card.json"
    sop = json.loads(sop_path.read_text())
    sop["model_trial_status"] = "PASS_AFTER_CONTRACT_REPLAY"
    sop["release_blockers"] = ["fixed-container replay", "practitioner review"]
    sop_path.write_text(json.dumps(sop, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
