from __future__ import annotations
import argparse
import csv
import hashlib
import json
from pathlib import Path

def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def expected(data: Path) -> dict:
    rows = list(csv.DictReader((data / "profiles.csv").open(newline="", encoding="utf-8")))
    rules = json.loads((data / "rules.json").read_text(encoding="utf-8"))
    treated = [row for row in rows if row["control_status"] == "treated"]
    controls = [row for row in rows if row["control_status"] == "control"]
    raw_effect = round(sum(float(row["raw_signal"]) for row in treated) / len(treated) - sum(float(row["raw_signal"]) for row in controls) / len(controls), 4)
    adjusted_effect = round(sum(float(row["adjusted_signal"]) for row in treated) / len(treated) - sum(float(row["adjusted_signal"]) for row in controls) / len(controls), 4)
    control_drift = round(max(float(row["adjusted_signal"]) for row in controls) - min(float(row["adjusted_signal"]) for row in controls), 4)
    identifiable = adjusted_effect >= rules["minimum_adjusted_effect"] and len(treated) >= rules["minimum_replicates"] and control_drift <= rules["maximum_control_drift"]
    return {"raw_effect": raw_effect, "adjusted_effect": adjusted_effect, "control_drift": control_drift, "replicate_count": len(treated), "identifiable": identifiable, "decision": "proceed_to_profile_review" if identifiable else "hold_for_human_review", "rules_version": rules["rules_version"], "input_sha256": {name: sha(data / name) for name in ("profiles.csv", "rules.json")}, "claim_boundary": {"mechanism_established": False, "human_review_required": True}}

def verify(submission: Path, data: Path, reference: Path) -> tuple[bool, list[str]]:
    exp, errors = expected(data), []
    for name in ("signal_noise_report.json", "replicate_diagnostics.tsv", "profile_review_gate.md"):
        if not (submission / name).is_file(): errors.append("missing artifact: " + name)
    if errors: return False, errors
    report = json.loads((submission / "signal_noise_report.json").read_text(encoding="utf-8"))
    for key in ("raw_effect", "adjusted_effect", "control_drift", "replicate_count", "identifiable", "decision", "rules_version"):
        if report.get(key) != exp[key]: errors.append("signal/noise report mismatch: " + key)
    if report.get("input_sha256") != exp["input_sha256"]: errors.append("signal/noise report provenance mismatch")
    if report.get("claim_boundary") != exp["claim_boundary"]: errors.append("signal/noise report claim boundary mismatch")
    diagnostics = (submission / "replicate_diagnostics.tsv").read_text(encoding="utf-8").lower()
    for phrase in ("perturbation", "plate", "replicate", "raw_signal", "adjusted_signal", "control_status"):
        if phrase not in diagnostics: errors.append("replicate diagnostics missing " + phrase)
    gate = (submission / "profile_review_gate.md").read_text(encoding="utf-8").lower()
    for phrase in ("signal", "technical noise", "human review", "mechanism"):
        if phrase not in gate: errors.append("profile review gate missing " + phrase)
    return not errors, errors

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--submission", type=Path, required=True)
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--reference", type=Path, required=True)
    args = parser.parse_args()
    ok, errors = verify(args.submission, args.data, args.reference)
    print(json.dumps({"passed": ok, "errors": errors}))
    raise SystemExit(0 if ok else 1)
