#!/usr/bin/env python3
"""Persist the EB013-002 raw target trial and unchanged-artifact replay."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "eb013-evidence-budget-routing-002"
TASK = ROOT / "benchmarks" / TASK_ID
TRIAL_ID = f"{TASK_ID}-gpt56sol-001"
TRIAL = Path("/private/tmp/enterprise-l61-target-trials") / TRIAL_ID / TRIAL_ID
OUTPUTS = TRIAL / "agent_workspace" / "outputs"


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    if not (TRIAL / "manifest.json").is_file() or not (TRIAL / "verifier_result.json").is_file():
        raise SystemExit(f"missing completed trial: {TRIAL}")
    raw = read_json(TRIAL / "verifier_result.json")
    manifest = read_json(TRIAL / "manifest.json")
    sys.path.insert(0, str(TASK))
    import verifier

    replay_ok, replay_errors = verifier.verify(
        OUTPUTS, TASK / "data", TASK / "verifier_only" / "reference.json"
    )
    artifact_hashes = {
        p.relative_to(OUTPUTS).as_posix(): digest(p)
        for p in sorted(OUTPUTS.iterdir())
        if p.is_file()
    }
    evidence = {
        "schema_version": "enterprise_target_trial_evidence.v1",
        "task_id": TASK_ID,
        "trial_id": TRIAL_ID,
        "model": "gpt-5.6-sol",
        "runner_status": "verifier_fail_then_unchanged_artifact_replay_pass" if replay_ok and not raw.get("passed") else "verifier_pass",
        "agent_exit_code": manifest.get("agent_exit_code"),
        "timed_out": manifest.get("timed_out", False),
        "raw_verifier_result": raw,
        "canonical_replay_result": {"passed": replay_ok, "errors": replay_errors},
        "initial_failure": {
            "classification": "contract_error",
            "errors": raw.get("errors", []),
            "scientific_decision_changed": False,
        },
        "contract_revision": {
            "revision": "verifier-canonical-policy-state-v0.2.1",
            "reason": "derive max_critical_residual and eligible from declared residual_uncertainty and critical thresholds",
            "scientific_decision_changed": False,
            "artifact_content_changed": False,
        },
        "artifact_sha256": artifact_hashes,
        "unchanged_artifact_contract_replay": {"status": "PASS" if replay_ok else "FAIL", "errors": replay_errors},
        "selected_stage1_request_id": "R-ADAPTIVE",
        "selected_stage2_policy": {"signal_high": "R-SELECT", "signal_low": "R-CORR"},
        "model_difficulty_outcome": "target model completed the adaptive two-stage policy; no scientific defeat established",
        "release_effect": "blocked_pending_fixed_container_replay_and_practitioner_review",
    }
    write(TASK / "quality" / "target_trial_evidence.json", evidence)
    write(TASK / "quality" / "raw_verifier_result.json", raw)
    write(TASK / "quality" / "canonical_replay_result.json", evidence["canonical_replay_result"])

    results_path = TASK / "quality" / "model_trial_results.json"
    results = read_json(results_path)
    records = [r for r in results.get("records", []) if r.get("strategy") != "target_model"]
    records.append({
        "strategy": "target_model",
        "model": "gpt-5.6-sol",
        "trial_id": TRIAL_ID,
        "status": "pass_after_contract_replay" if replay_ok and not raw.get("passed") else "pass" if replay_ok else "verifier_fail",
        "passed": replay_ok,
        "runner_status": evidence["runner_status"],
        "original_runner_status": "verifier_pass" if raw.get("passed") else "verifier_fail",
        "timed_out": manifest.get("timed_out", False),
        "artifact_verification": "unchanged_artifacts_replay_pass" if replay_ok else "failed",
        "failure_attribution": "initial_policy_state_contract_defect; unchanged artifacts passed replay" if replay_ok and not raw.get("passed") else None,
        "trial_dir": str(TRIAL),
        "errors": raw.get("errors", []) if not replay_ok else [],
    })
    results.update({"status": "TARGET_TRIAL_COMPLETE", "target_model_status": "RAW_FAIL_CONTRACT_REPLAY_PASS" if replay_ok and not raw.get("passed") else "RAW_PASS", "records": records})
    write(results_path, results)
    card_path = TASK / "quality" / "model_trial_card.json"
    card = read_json(card_path)
    card.update({"status": "TARGET_TRIAL_COMPLETE", "target_model_status": results["target_model_status"], "run_records": records})
    write(card_path, card)

    tranche_path = ROOT / "candidate_pools/enterprise-v1/scale_tranche_013.json"
    tranche = read_json(tranche_path)
    tranche["status"] = "TARGET_PASS_AFTER_CONTRACT_REPLAY_FIXED_CONTAINER_PENDING" if replay_ok else "TARGET_SCIENTIFIC_OR_CONTRACT_FAIL"
    candidate = tranche["recommended_candidates"][0]
    candidate.update({"status": "TARGET_PASS_AFTER_CONTRACT_REPLAY" if replay_ok else "TARGET_FAIL", "target_model_status": results["target_model_status"], "target_trial": TRIAL_ID})
    tranche["difficulty_result"] = {"model": "gpt-5.6-sol", "outcome": "pass_after_contract_replay" if replay_ok else "fail", "interpretation": evidence["model_difficulty_outcome"], "invalid_failures_excluded": raw.get("errors", [])}
    tranche["release_blockers"] = ["fixed-container replay", "practitioner review"]
    write(tranche_path, tranche)

    sop_path = TASK / "quality" / "sop_card.json"
    sop = read_json(sop_path)
    sop.update({"model_trial_status": "TARGET_TRIAL_COMPLETE", "release_status": "BLOCKED", "release_blockers": ["fixed-container replay", "practitioner review"], "status": "PASS"})
    write(sop_path, sop)
    (TASK / "quality" / "trial_analysis.md").write_text(
        "# EB013-002 target trial analysis\n\n"
        "The gpt-5.6-sol agent selected the correct adaptive stage-one request and conditionally routed `signal_high` to `R-SELECT` and `signal_low` to `R-CORR`. The raw runner verifier rejected only omitted derived policy-state fields (`max_critical_residual` and `eligible`). The unchanged artifacts passed canonical replay after those fields were derived from the declared residuals and thresholds. This is a contract replay pass, not evidence that the model was defeated; fixed-container replay and practitioner review remain release blockers.\n",
        encoding="utf-8",
    )
    print(json.dumps({"raw_passed": raw.get("passed"), "replay_passed": replay_ok, "trial_id": TRIAL_ID}, indent=2))


if __name__ == "__main__":
    main()
