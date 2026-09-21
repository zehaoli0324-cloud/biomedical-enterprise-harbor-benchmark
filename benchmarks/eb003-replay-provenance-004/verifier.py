from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path

def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def expected(data: Path) -> dict:
    artifact = json.loads((data / "artifact_manifest.json").read_text())
    env = json.loads((data / "environment.json").read_text())
    return {"artifact_id": artifact["artifact_id"], "rules_version": artifact["rules_version"],
            "input_hashes": artifact["input_hashes"], "output_hashes": artifact["output_hashes"],
            "environment": env, "hashes": {name: sha(data / name) for name in ("artifact_manifest.json", "environment.json")}}

def verify(submission: Path, data: Path, reference: Path) -> tuple[bool, list[str]]:
    exp, errors = expected(data), []
    required = ("replay_manifest.json", "provenance_diff.tsv", "handoff_replay_report.md")
    for name in required:
        if not (submission / name).is_file(): errors.append("missing artifact: " + name)
    if errors: return False, errors
    manifest = json.loads((submission / "replay_manifest.json").read_text())
    if manifest.get("artifact_id") != exp["artifact_id"]: errors.append("artifact id mismatch")
    if manifest.get("rules_version") != exp["rules_version"]: errors.append("rules version mismatch")
    if manifest.get("input_hashes") != exp["input_hashes"] or manifest.get("output_hashes") != exp["output_hashes"]: errors.append("provenance hash mismatch")
    if manifest.get("environment") != exp["environment"]: errors.append("environment mismatch")
    if manifest.get("replay_status") != "reproduced": errors.append("replay_status must be reproduced")
    diff = (submission / "provenance_diff.tsv").read_text().lower()
    for phrase in ("field", "status", "match"):
        if phrase not in diff: errors.append("provenance_diff.tsv missing " + phrase)
    report = (submission / "handoff_replay_report.md").read_text().lower()
    for phrase in ("replay", "checksum", "human review", "not biological validation"):
        if phrase not in report: errors.append("handoff report missing " + phrase)
    return not errors, errors

if __name__ == "__main__":
    p = argparse.ArgumentParser(); p.add_argument("--submission", type=Path, required=True); p.add_argument("--data", type=Path, required=True); p.add_argument("--reference", type=Path, required=True)
    a = p.parse_args(); ok, errors = verify(a.submission, a.data, a.reference); print(json.dumps({"passed": ok, "errors": errors})); raise SystemExit(0 if ok else 1)
