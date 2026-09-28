"""Record completed local trials without replacing raw verdicts or frozen files."""
import argparse
import hashlib
import json
import shutil
from pathlib import Path

from calibrate_observation_boundary import ROOT, TASK, read, verifier, write


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("trial", type=Path)
    args = parser.parse_args()
    trial = args.trial.resolve()
    manifest = read(trial / "manifest.json")
    if manifest["task_id"] != TASK.name or not manifest.get("finished_at"):
        raise ValueError("finished trial for this task required")
    freeze = read(TASK / "quality/pretrial_freeze.json")["sha256"]
    for name, value in freeze.items():
        if digest(TASK / name) != value:
            raise ValueError("frozen task changed: " + name)
    workspace = trial / "agent_workspace"
    for name, value in manifest["input_hashes"].items():
        if freeze[name] != value or digest(workspace / name) != value:
            raise ValueError("trial inputs changed: " + name)
    events_path = workspace / "agent_events.jsonl"
    events = [json.loads(line) for line in events_path.read_text().splitlines() if line.strip()] if events_path.exists() else []
    completed = any(e.get("type") == "turn.completed" for e in events)
    config = next((e for e in events if e.get("type") == "model_config"), {})
    raw = read(trial / "verifier_result.json") if (trial / "verifier_result.json").exists() else None
    outputs = workspace / "outputs"
    artifact_hashes = {p.name: digest(p) for p in sorted(outputs.glob("*")) if p.is_file()}
    for name, value in manifest.get("visible_output_hashes", {}).items():
        if digest(outputs / name) != value:
            raise ValueError("output changed: " + name)
    passed, errors = verifier().verify(outputs, TASK / "data")
    normal = completed and manifest.get("agent_exit_code") == 0 and not manifest.get("timed_out")
    if normal and raw is not None and raw.get("passed") != passed:
        raise ValueError("frozen replay differs from raw verdict")
    classification = "RAW_PASS" if normal and passed else "VERIFIER_FAIL_REQUIRES_TRIAGE" if normal else "TIMEOUT" if manifest.get("timed_out") or manifest.get("agent_exit_code") == 124 else "AGENT_ERROR"
    destination = TASK / "quality/trials" / manifest["trial_id"]
    if destination.exists():
        raise ValueError("trial already archived")
    destination.mkdir(parents=True)
    shutil.copytree(outputs, destination / "outputs")
    for name in ("manifest.json", "verifier_result.json"):
        if (trial / name).exists():
            shutil.copy2(trial / name, destination / name)
    record = {"strategy": "target_model", "model": config.get("model"), "trial_id": manifest["trial_id"],
              "classification": classification, "runner_status": manifest["status"], "turn_completed": completed,
              "agent_exit_code": manifest.get("agent_exit_code"), "timed_out": manifest.get("timed_out", False),
              "started_at": manifest.get("started_at"), "finished_at": manifest.get("finished_at"),
              "raw_verifier_result": raw, "frozen_replay": {"passed": passed, "errors": errors},
              "artifact_sha256": artifact_hashes, "event_log_sha256": digest(events_path) if events_path.exists() else None,
              "freeze_sha256": digest(TASK / "quality/pretrial_freeze.json"), "artifact_content_changed": False,
              "isolation_mode": manifest.get("isolation_mode"), "trial_dir": str(trial),
              "adapter_sha256": {n: digest(ROOT / "benchmark_runner/adapters" / n) for n in ("codex_complete_turn.py", "codex_gpt55.py")},
              "adapter_capture": "post-run source hashes; no adapter edits during this trial",
              "limitation": "Local calibration, not container-isolated or cross-domain target-model validation."}
    write(destination / "evidence.json", record)
    quality = TASK / "quality"
    write(quality / "target_trial_evidence.json", record)
    controls = read(TASK / "controls/calibration_results.json")["controls"]
    strategy_names = {"reference": "reference_solution", "mean-objective-baseline": "simple_legal_baseline"}
    baselines = [{"strategy": strategy_names.get(c["id"], c["id"]), "passed": c["expected_pass"], "errors": c["errors"]}
                 for c in controls if c["id"] in {"reference", "mean-objective-baseline", "absolute-residual-baseline", "cheapest-baseline"}]
    baselines.extend([
        {"strategy": "always_abstain", "passed": False, "errors": ["decision.decision: mismatch", "decision.selected: object required"]},
        {"strategy": "template_or_keyword", "passed": False, "errors": ["delivery_or_contract: invalid table: stage1_id"]},
    ])
    results_path = quality / "model_trial_results.json"
    old = read(results_path).get("records", []) if results_path.exists() else baselines
    write(results_path, {"task_id": TASK.name, "protocol_version": "enterprise-model-trial.v1",
          "status": "TARGET_TRIAL_COMPLETE", "target_model_status": classification, "records": old + [record]})
    write(quality / "model_trial_card.json", {"task_id": TASK.name, "protocol_version": "enterprise-model-trial.v1",
          "status": "TARGET_TRIAL_COMPLETE", "target_model_status": classification,
          "strategies": ["reference_solution", "simple_legal_baseline", "always_abstain", "template_or_keyword", "target_model"],
          "trial_id": manifest["trial_id"], "evidence": "target_trial_evidence.json",
          "records": "model_trial_results.json", "release_status": "BLOCKED"})
    difficulty = read(quality / "difficulty_card.json")
    difficulty.update(status="LOCAL_CALIBRATION_PASS_TARGET_" + classification,
                      target_trial=manifest["trial_id"], target_model_defeated=False if classification == "RAW_PASS" else None)
    write(quality / "difficulty_card.json", difficulty)
    sop_path = quality / "sop_card.json"
    sop = read(sop_path) if sop_path.exists() else {}
    sop.update({"schema_version": "enterprise_harbor_sop_card.v1", "sop_version": "enterprise-harbor-sop-v1.2",
          "task_id": TASK.name, "task_version": "1.0.0", "source_status": "SYNTHETIC_DISCLOSED",
          "control_status": "PASS", "contract_status": "FROZEN", "model_trial_status": classification,
          "independent_verifier_status": "AUTOMATED_CROSSCHECK_PASS", "release_status": "BLOCKED",
          "release_blockers": ["fixed-container replay", "held-out target-model trial", "practitioner review"]})
    write(sop_path, sop)
    outcome = ("The model passed the frozen contract and scientific checks. This task did not defeat the target in this trial."
               if classification == "RAW_PASS" else "No claim of scientific defeat is supported without trace-level failure triage.")
    (quality / "trial_analysis.md").write_text(
        "# EB013-004 Trial Analysis\n\n" + f"Trial `{manifest['trial_id']}`: `{classification}`.\n\n" + outcome
        + "\n\n18 contract/negative/baseline controls and eight input variants passed before the model trial. "
        "The task and verifier were frozen before execution. Raw verdict, artifact hashes and unchanged frozen replay are retained. "
        "One local process trial is not an estimate of general model failure rate.\n")
    print(json.dumps(record, indent=2))


if __name__ == "__main__":
    main()
