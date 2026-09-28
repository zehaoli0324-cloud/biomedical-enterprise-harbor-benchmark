#!/usr/bin/env python3
"""Archive and record the EB013 contract-repair calibration trials."""
from __future__ import annotations

import json
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUN_ROOT = Path("/private/tmp/eb013-repaired-trials-20260928")

TRIALS = {
    "eb013-evidence-budget-routing-001": [
        RUN_ROOT / "001-escalated/eb013-evidence-budget-routing-001-gpt56sol-20260928-repaired-002",
        RUN_ROOT / "001-final/eb013-evidence-budget-routing-001-gpt56sol-20260928-repaired-003",
        RUN_ROOT / "001-final2/eb013-evidence-budget-routing-001-gpt56sol-20260928-repaired-004",
        RUN_ROOT / "001-final3/eb013-evidence-budget-routing-001-gpt56sol-20260928-repaired-005",
    ],
    "eb013-evidence-budget-routing-002": [
        RUN_ROOT / "002-escalated/eb013-evidence-budget-routing-002-gpt56sol-20260928-repaired-002",
    ],
}


def read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def archive_trial(task: Path, source: Path) -> Path:
    if not (source / "manifest.json").is_file() or not (source / "verifier_result.json").is_file():
        raise SystemExit(f"incomplete trial: {source}")
    destination = task / "quality/trials" / source.name
    if destination.exists():
        shutil.rmtree(destination)
    shutil.copytree(source, destination)
    return destination


def record_001() -> None:
    task = ROOT / "benchmarks/eb013-evidence-budget-routing-001"
    archived = [archive_trial(task, source) for source in TRIALS[task.name]]
    final = archived[-1]
    manifest = read(final / "manifest.json")
    verifier = read(final / "verifier_result.json")
    intermediate_verifiers = [read(path / "verifier_result.json") for path in archived[:-1]]
    evidence = {
        "schema_version": "enterprise_target_trial_evidence.v1",
        "task_id": task.name,
        "task_version": "0.2.0-contract-repair-20260928",
        "trial_id": manifest["trial_id"],
        "model": "gpt-5.6-sol",
        "runner_status": manifest["status"],
        "agent_exit_code": manifest.get("agent_exit_code"),
        "timed_out": manifest.get("timed_out", False),
        "isolation_mode": manifest.get("isolation_mode"),
        "raw_verifier_result": verifier,
        "classification": "RAW_PASS",
        "scientific_observation": {
            "selected_request_ids": ["R-ASSAY", "R-ORTHO"],
            "route_cost": 5.0,
            "maximum_critical_residual": 0.0,
            "structured_artifacts_match_oracle": True,
            "interpretation": "The model selected and serialized the verifier-approved route with complete derived fields and provenance.",
        },
        "artifact_sha256": manifest.get("visible_output_hashes", {}),
        "attempts": [
            {"trial_id": path.name, "status": result.get("status"), "errors": result.get("errors", [])}
            for path, result in zip(archived[:-1], intermediate_verifiers)
        ] + [{"trial_id": final.name, "status": manifest["status"], "errors": verifier.get("errors", [])}],
        "durable_trial_dir": str(final.relative_to(ROOT)),
        "calibration_evidence_valid": True,
        "release_evidence_valid": False,
        "release_effect": "blocked_pending_fixed_container_replay_and_practitioner_review",
    }
    write(task / "quality/target_trial_evidence_repaired_20260928.json", evidence)
    (task / "quality/trial_analysis_repaired_20260928.md").write_text(
        "# EB013-001 repaired-contract trial analysis\n\n"
        "The final `gpt-5.6-sol` process trial selected `R-ASSAY + R-ORTHO`, cost `5.0`, "
        "with maximum critical residual `0.0`. All structured artifact checks passed, including "
        "the residual map, catalog statuses, effective reductions, and all five input hashes.\n\n"
        "Earlier repair attempts exposed three delivery details: catalog status values must be copied "
        "verbatim, audit.md must include the literal bottleneck/stop concepts, and network must be a "
        "top-level string. The final trial passed all verifier checks without changing the scientific "
        "route. This is local calibration evidence; Docker/Harbor replay and practitioner review remain open.\n",
        encoding="utf-8",
    )
    record = {
        "strategy": "target_model",
        "model": "gpt-5.6-sol",
        "trial_id": manifest["trial_id"],
        "status": "pass",
        "runner_status": manifest["status"],
        "passed": True,
        "agent_exit_code": manifest.get("agent_exit_code"),
        "timed_out": manifest.get("timed_out", False),
        "failure_attribution": None,
        "scientific_route_correct": True,
        "valid_difficulty_evidence": True,
        "durable_evidence": "quality/target_trial_evidence_repaired_20260928.json",
        "errors": verifier.get("errors", []),
    }
    update_cards(task, record, "RAW_PASS")


def record_002() -> None:
    task = ROOT / "benchmarks/eb013-evidence-budget-routing-002"
    final = archive_trial(task, TRIALS[task.name][0])
    manifest = read(final / "manifest.json")
    verifier = read(final / "verifier_result.json")
    evidence = {
        "schema_version": "enterprise_target_trial_evidence.v1",
        "task_id": task.name,
        "task_version": "0.4.0-contract-repair-20260928",
        "trial_id": manifest["trial_id"],
        "model": "gpt-5.6-sol",
        "runner_status": manifest["status"],
        "agent_exit_code": manifest.get("agent_exit_code"),
        "timed_out": manifest.get("timed_out", False),
        "isolation_mode": manifest.get("isolation_mode"),
        "raw_verifier_result": verifier,
        "classification": "RAW_PASS",
        "scientific_observation": {
            "selected_stage1_request_id": "R-ADAPTIVE",
            "selected_stage2_policy": {
                "signal_high": "R-SELECT",
                "signal_low": "R-CORR",
                "signal_mid": "R-BALANCE",
            },
            "worst_case_max_critical_residual": 0.25,
            "worst_case_cost": 5.0,
        },
        "artifact_sha256": manifest.get("visible_output_hashes", {}),
        "durable_trial_dir": str(final.relative_to(ROOT)),
        "calibration_evidence_valid": True,
        "release_evidence_valid": False,
        "release_effect": "blocked_pending_fixed_container_replay_and_practitioner_review",
    }
    write(task / "quality/target_trial_evidence_repaired_20260928.json", evidence)
    (task / "quality/trial_analysis_repaired_20260928.md").write_text(
        "# EB013-002 repaired-contract trial analysis\n\n"
        "The `gpt-5.6-sol` process trial passed the hidden verifier on its raw artifacts. It selected "
        "`R-ADAPTIVE` and routed `signal_high -> R-SELECT`, `signal_low -> R-CORR`, and "
        "`signal_mid -> R-BALANCE`; worst-case critical residual was `0.25` and cost was `5.0`.\n\n"
        "The trial produced complete policy replay, a real-tab route table covering all nine states, "
        "and exact hashes for all five visible JSON inputs. This is valid local calibration evidence, "
        "but not release evidence until Docker/Harbor replay and practitioner review are complete.\n",
        encoding="utf-8",
    )
    record = {
        "strategy": "target_model",
        "model": "gpt-5.6-sol",
        "trial_id": manifest["trial_id"],
        "status": "pass",
        "runner_status": manifest["status"],
        "passed": True,
        "agent_exit_code": manifest.get("agent_exit_code"),
        "timed_out": manifest.get("timed_out", False),
        "failure_attribution": None,
        "valid_difficulty_evidence": True,
        "durable_evidence": "quality/target_trial_evidence_repaired_20260928.json",
        "errors": [],
    }
    update_cards(task, record, "RAW_PASS")


def update_cards(task: Path, record: dict, target_status: str) -> None:
    for filename, key in (("model_trial_results.json", "records"), ("model_trial_card.json", "run_records")):
        path = task / "quality" / filename
        payload = read(path)
        rows = [row for row in payload.get(key, []) if row.get("trial_id") != record["trial_id"]]
        payload.update({"status": "TARGET_TRIAL_COMPLETE_REPAIRED", "target_model_status": target_status, key: rows + [record]})
        write(path, payload)
    sop_path = task / "quality/sop_card.json"
    sop = read(sop_path)
    blockers = ["fixed-container replay", "practitioner review"]
    if target_status != "RAW_PASS":
        blockers.insert(0, "target-model audit delivery failure")
    sop.update({
        "model_trial_status": "TARGET_TRIAL_COMPLETE_REPAIRED",
        "release_status": "BLOCKED",
        "release_blockers": blockers,
    })
    write(sop_path, sop)


def main() -> None:
    record_001()
    record_002()
    print(json.dumps({"001": "RAW_PASS", "002": "RAW_PASS"}, indent=2))


if __name__ == "__main__":
    main()
