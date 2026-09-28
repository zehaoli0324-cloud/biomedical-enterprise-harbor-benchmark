#!/usr/bin/env python3
"""Persist L5.1 target-trial history and unchanged-artifact replay evidence."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TASK = ROOT / "benchmarks/eb010-closed-loop-ambiguity-004"
TRIALS = Path("/private/tmp/enterprise-l51-target-trials")
TRIALS_V2 = Path("/private/tmp/enterprise-l51-target-trials-v2")


def load_trial(root: Path, trial_id: str) -> tuple[Path, dict, dict]:
    path = root / trial_id
    return path, json.loads((path / "manifest.json").read_text()), json.loads((path / "verifier_result.json").read_text())


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    first_id = "eb010-closed-loop-ambiguity-004-gpt56sol-001"
    second_id = "eb010-closed-loop-ambiguity-004-gpt56sol-002"
    first_path, first_manifest, first_result = load_trial(TRIALS, first_id)
    second_path, second_manifest, second_result = load_trial(TRIALS_V2, second_id)
    outputs = second_path / "agent_workspace/outputs"
    history = [
        {
            "strategy": "target_model",
            "model": "gpt-5.6-sol",
            "trial_id": first_id,
            "status": "invalid_contract_defect",
            "passed": False,
            "valid_difficulty_evidence": False,
            "runner_status": first_manifest["status"],
            "timed_out": bool(first_manifest.get("timed_out", False)),
            "failure_attribution": "undocumented_output_schema",
            "verifier_errors": first_result.get("errors", []),
        },
        {
            "strategy": "target_model",
            "model": "gpt-5.6-sol",
            "trial_id": second_id,
            "status": "pass_after_contract_replay",
            "passed": True,
            "runner_status": "verifier_fail_then_unchanged_artifact_replay_pass",
            "original_runner_status": second_manifest["status"],
            "timed_out": bool(second_manifest.get("timed_out", False)),
            "failure_attribution": "initial_redundant_semantic_encoding_contract_defect",
            "original_verifier_errors": second_result.get("errors", []),
            "artifact_sha256": {
                name: sha256(outputs / name)
                for name in ("decision.json", "evidence.tsv", "discovery.json", "audit.md")
            },
            "trial_dir": str(second_path),
        },
    ]
    results_path = TASK / "quality/model_trial_results.json"
    results = json.loads(results_path.read_text())
    records = [row for row in results.get("records", []) if row.get("strategy") != "target_model"] + history
    results.update({"status": "TARGET_TRIAL_COMPLETE", "target_model_status": "PASS_AFTER_CONTRACT_REPLAY", "records": records})
    results_path.write_text(json.dumps(results, indent=2) + "\n")

    card_path = TASK / "quality/model_trial_card.json"
    card = json.loads(card_path.read_text())
    card_records = [row for row in card.get("run_records", []) if row.get("strategy") != "target_model"] + history
    card.update({"status": "TARGET_TRIAL_COMPLETE", "target_model_status": "PASS_AFTER_CONTRACT_REPLAY", "run_records": card_records})
    card_path.write_text(json.dumps(card, indent=2) + "\n")

    evidence = {
        "schema_version": "enterprise_target_trial_evidence.v1",
        "task_id": TASK.name,
        "model": "gpt-5.6-sol",
        "classification": "agent_completed_verifier_passed_after_contract_replay",
        "valid_difficulty_outcome": "pass",
        "contract_defects_are_not_difficulty_evidence": True,
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
