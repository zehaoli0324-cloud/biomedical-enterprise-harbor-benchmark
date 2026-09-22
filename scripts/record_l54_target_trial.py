#!/usr/bin/env python3
"""Record the completed L5.4 target trial without changing its artifacts."""

from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TASK = ROOT / "benchmarks/eb012-cross-stage-chain-002"
TRIAL_ID = "eb012-cross-stage-chain-002-gpt56sol-002"
TRIAL = Path("/private/tmp/enterprise-l54-target-trials-v2") / TRIAL_ID


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    manifest = json.loads((TRIAL / "manifest.json").read_text())
    stored_verifier = json.loads((TRIAL / "verifier_result.json").read_text())
    outputs = TRIAL / "agent_workspace/outputs"
    spec = importlib.util.spec_from_file_location("eb012_verifier", TASK / "verifier.py")
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    passed, current_errors = module.verify(outputs, TASK / "data", TASK / "verifier_only/reference.json")
    artifacts = ("chain.json", "handoff.tsv", "audit.md", "manifest.json")
    record = {
        "strategy": "target_model",
        "model": "gpt-5.6-sol",
        "trial_id": TRIAL_ID,
        "task_version": "0.9.0",
        "status": "verifier_fail",
        "passed": False,
        "valid_difficulty_evidence": True,
        "runner_status": manifest.get("status"),
        "agent_exit_code": manifest.get("agent_exit_code"),
        "timed_out": bool(manifest.get("timed_out", False)),
        "verifier_status": manifest.get("verifier_status"),
        "failure_attribution": "required_manifest_rules_version_missing",
        "verifier_errors": current_errors,
        "stored_runner_verifier_errors": stored_verifier.get("errors", []),
        "artifact_sha256": {name: digest(outputs / name) for name in artifacts},
        "trial_dir": str(TRIAL),
    }
    for filename, key in (("model_trial_results.json", "records"), ("model_trial_card.json", "run_records")):
        path = TASK / "quality" / filename
        payload = json.loads(path.read_text())
        records = [row for row in payload.get(key, []) if row.get("strategy") != "target_model"]
        payload.update({"status": "TARGET_TRIAL_COMPLETE", "target_model_status": "VERIFIER_FAIL", key: records + [record]})
        path.write_text(json.dumps(payload, indent=2) + "\n")
    evidence = {
        "schema_version": "enterprise_target_trial_evidence.v1",
        "task_id": TASK.name,
        "model": "gpt-5.6-sol",
        "classification": "agent_completed_verifier_failed",
        "valid_difficulty_outcome": "verifier_fail",
        "contract_defect_replay": "not_applied",
        "reason": "rules_version was explicitly required in manifest.json and omitted by the agent",
        "trial": record,
        "release_effect": "blocked_pending_contract-review-fixed-container-replay-and-practitioner-review",
    }
    (TASK / "quality/target_trial_evidence.json").write_text(json.dumps(evidence, indent=2) + "\n")
    sop_path = TASK / "quality/sop_card.json"
    sop = json.loads(sop_path.read_text())
    sop.update({"model_trial_status": "VERIFIER_FAIL", "release_status": "BLOCKED"})
    sop["release_blockers"] = ["target model verifier failure", "fixed-container replay", "practitioner review"]
    sop_path.write_text(json.dumps(sop, indent=2) + "\n")
    print(json.dumps(record, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
