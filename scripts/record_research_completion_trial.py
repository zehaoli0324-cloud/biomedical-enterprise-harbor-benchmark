"""Preserve gated trial attempts, raw verdict and unchanged scientific replay."""
import argparse
import json
import shutil
from datetime import datetime
from pathlib import Path

from calibrate_research_completion import ROOT, TASK, verifier
from benchmark_runner.research_gate import digest, load, save


def record(trial):
    manifest = load(trial/"manifest.json")
    if manifest["task_id"] != TASK.name or not manifest.get("finished_at"):
        raise ValueError("Finished trial for this task required")
    freeze = load(TASK/"quality/pretrial_freeze.json")
    for name,h in freeze["sha256"].items():
        if digest(TASK/name) != h:
            raise ValueError("Frozen task changed: "+name)
    for name,h in freeze["runtime_sha256"].items():
        if digest(ROOT/name) != h:
            raise ValueError("Frozen runtime changed: "+name)
    workspace = trial/"agent_workspace"
    for name,h in manifest["input_hashes"].items():
        if freeze["sha256"].get(name) != h or digest(workspace/name) != h:
            raise ValueError("Trial input mismatch: "+name)
    outputs = workspace/"outputs"
    hashes = {p.relative_to(outputs).as_posix():digest(p) for p in outputs.rglob("*") if p.is_file()}
    if any(hashes.get(name) != h for name,h in manifest.get("visible_output_hashes",{}).items()):
        raise ValueError("Trial outputs changed")
    attempts = load(trial/"completion_attempts/result.json") if (trial/"completion_attempts/result.json").exists() else {"status":"incomplete","attempts":[]}
    raw = load(trial/"verifier_result.json") if (trial/"verifier_result.json").exists() else None
    ok,errors = verifier().verify(outputs,TASK/"data")
    if raw is not None and raw.get("passed") != ok:
        raise ValueError("Raw scientific verdict differs from frozen replay")
    normal = manifest.get("agent_exit_code") == 0 and attempts["status"] == "accepted" and not manifest.get("timed_out")
    classification = "RAW_PASS" if normal and ok else "SCIENTIFIC_OR_CONTRACT_FAIL" if normal else "TIMEOUT" if manifest.get("timed_out") or manifest.get("agent_exit_code") == 124 else "COMPLETION_OR_AGENT_FAIL"
    events = []
    for p in sorted((trial/"completion_attempts").glob("attempt-*/events.jsonl")):
        events.extend(json.loads(line) for line in p.read_text().splitlines() if line.strip())
    model = next((e.get("model") for e in events if e.get("type")=="model_config"),None)
    record = {"task_id":TASK.name,"trial_id":manifest["trial_id"],"model":model,"classification":classification,
              "raw_verifier_result":raw,"frozen_replay":{"passed":ok,"errors":errors},
              "completion_status":attempts["status"],"submission_attempts":len(attempts["attempts"]),
              "returned_submissions":sum(a["status"]=="returned" for a in attempts["attempts"]),
              "completed_model_turns":sum(e.get("type")=="turn.completed" for e in events),
              "elapsed_seconds":(datetime.fromisoformat(manifest["finished_at"])-datetime.fromisoformat(manifest["started_at"])).total_seconds(),
              "artifact_sha256":hashes,"artifact_content_changed":False,"freeze_sha256":digest(TASK/"quality/pretrial_freeze.json"),
              "runtime_hashes_verified":True,"isolation_mode":manifest.get("isolation_mode"),"trial_dir":str(trial),
              "target_model_defeated":False if classification=="RAW_PASS" else None,
              "human_scientific_review":"NOT_RUN","container_isolation":"NOT_RUN"}
    dest = TASK/"quality/trials"/manifest["trial_id"]
    if dest.exists():
        raise ValueError("Already archived")
    dest.mkdir(parents=True)
    shutil.copytree(outputs,dest/"outputs")
    shutil.copytree(trial/"completion_attempts",dest/"completion_attempts")
    for name in ("manifest.json","verifier_result.json","verifier_stdout.log","verifier_stderr.log"):
        if (trial/name).exists():
            shutil.copy2(trial/name,dest/name)
    save(dest/"evidence.json",record)
    save(TASK/"quality/target_trial_evidence.json",record)
    path = TASK/"quality/model_trial_results.json"
    history = load(path) if path.exists() else {"task_id":TASK.name,"records":[]}
    history["records"].append(record)
    save(path,history)
    readiness = load(TASK/"quality/readiness.json")
    readiness.update(status="TARGET_TRIAL_COMPLETE",target_model_trial=classification)
    save(TASK/"quality/readiness.json",readiness)
    return record


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("trial",type=Path)
    parser.add_argument("--task",type=Path)
    args = parser.parse_args()
    if args.task:
        import calibrate_research_completion
        TASK = args.task.resolve()
        calibrate_research_completion.TASK = TASK
    print(json.dumps(record(args.trial.resolve()),indent=2))
