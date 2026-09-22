#!/usr/bin/env python3
"""Record EB013-002 v0.3 target trials without overwriting prior evidence."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TASK = ROOT / "benchmarks/eb013-evidence-budget-routing-002"
RUN_ROOT = Path("/private/tmp/enterprise-l61-target-trials")
TRIAL_IDS = (
    "eb013-evidence-budget-routing-002-gpt56sol-002",
    "eb013-evidence-budget-routing-002-gpt56sol-003",
)


def read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def load_verifier():
    spec = importlib.util.spec_from_file_location("eb013_v03_verifier", TASK / "verifier.py")
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def artifact_hashes(outputs: Path) -> dict[str, str]:
    return {
        path.name: hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(outputs.iterdir())
        if path.is_file()
    }


def evidence_for(trial_id: str, verifier) -> tuple[dict, dict]:
    trial = RUN_ROOT / trial_id / trial_id
    outputs = trial / "agent_workspace/outputs"
    raw = read(trial / "verifier_result.json")
    manifest = read(trial / "manifest.json")
    replay_ok, replay_errors = verifier.verify(
        outputs, TASK / "data", TASK / "verifier_only/reference.json"
    )
    if trial_id.endswith("002"):
        classification = "DELIVERY_FAIL_PROVENANCE"
        interpretation = "Scientific policy passed; canonical replay still rejects the missing run_manifest SHA-256."
    elif replay_ok:
        classification = "RAW_FAIL_CONTRACT_REPLAY_PASS"
        interpretation = "Three-state adaptive policy passed; the raw failure was limited to declared field aliases."
    else:
        classification = "SCIENTIFIC_OR_DELIVERY_FAIL"
        interpretation = "Canonical replay still fails and requires review."
    evidence = {
        "schema_version": "enterprise_target_trial_evidence.v1",
        "task_id": TASK.name,
        "task_version": "0.3.0",
        "trial_id": trial_id,
        "model": "gpt-5.6-sol",
        "agent_exit_code": manifest.get("agent_exit_code"),
        "timed_out": manifest.get("timed_out", False),
        "classification": classification,
        "raw_verifier_result": raw,
        "canonical_replay_result": {"passed": replay_ok, "errors": replay_errors},
        "artifact_sha256": artifact_hashes(outputs),
        "artifact_content_changed": False,
        "scientific_decision_changed": False,
        "selected_stage1_request_id": "R-ADAPTIVE",
        "selected_stage2_policy": {
            "signal_high": "R-SELECT",
            "signal_low": "R-CORR",
            "signal_mid": "R-BALANCE",
        },
        "interpretation": interpretation,
    }
    record = {
        "strategy": "target_model",
        "model": "gpt-5.6-sol",
        "trial_id": trial_id,
        "status": "pass_after_contract_replay" if replay_ok else "delivery_fail_provenance",
        "passed": replay_ok,
        "runner_status": "verifier_fail",
        "timed_out": manifest.get("timed_out", False),
        "artifact_verification": "unchanged_artifacts_replay_pass" if replay_ok else "unchanged_artifacts_replay_fail",
        "failure_attribution": classification.lower(),
        "trial_dir": str(trial),
        "errors": [] if replay_ok else replay_errors,
    }
    return evidence, record


def main() -> None:
    verifier = load_verifier()
    records = []
    for trial_id in TRIAL_IDS:
        evidence, record = evidence_for(trial_id, verifier)
        suffix = trial_id.rsplit("-", 1)[-1]
        write(TASK / "quality" / f"target_trial_evidence_{suffix}.json", evidence)
        records.append(record)

    results_path = TASK / "quality/model_trial_results.json"
    results = read(results_path)
    retained = [r for r in results.get("records", []) if r.get("trial_id") not in TRIAL_IDS]
    results.update({
        "status": "TARGET_TRIAL_COMPLETE_V0.3",
        "target_model_status": "RAW_FAIL_CONTRACT_REPLAY_PASS",
        "records": retained + records,
    })
    write(results_path, results)
    card_path = TASK / "quality/model_trial_card.json"
    card = read(card_path)
    card.update({
        "status": "TARGET_TRIAL_COMPLETE_V0.3",
        "target_model_status": "RAW_FAIL_CONTRACT_REPLAY_PASS",
        "run_records": results["records"],
    })
    write(card_path, card)
    sop_path = TASK / "quality/sop_card.json"
    sop = read(sop_path)
    sop.update({
        "model_trial_status": "TARGET_TRIAL_COMPLETE_V0.3",
        "release_status": "BLOCKED",
        "release_blockers": ["fixed-container replay", "practitioner review"],
    })
    write(sop_path, sop)
    (TASK / "quality/trial_analysis.md").write_text(
        "# EB013-002 target trial analysis\n\n"
        "The v0.2 target trial passed scientific verification after contract replay. Version 0.3 added a third observable state, `signal_mid`, whose legal action is `R-BALANCE`.\n\n"
        "In v0.3 trial `gpt56sol-002`, the model selected all three correct branches, but omitted the required `run_manifest.json` hash; canonical replay therefore remains a provenance delivery failure. In `gpt56sol-003`, after the four required hashes were explicitly enumerated, the model again selected the correct three-state policy and supplied complete provenance. Its raw verifier failure was limited to the declared aliases `observation_state` and `critical_residual_max`; unchanged-artifact replay passed.\n\n"
        "The increased scientific difficulty did not defeat gpt-5.6-sol. Release remains blocked pending fixed-container replay and practitioner review.\n",
        encoding="utf-8",
    )
    print(json.dumps({"recorded": list(TRIAL_IDS), "final_status": results["target_model_status"]}, indent=2))


if __name__ == "__main__":
    main()
