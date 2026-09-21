from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def expected(data: Path) -> dict:
    runs = json.loads((data / "tool_runs.json").read_text())
    spec = json.loads((data / "branch_spec.json").read_text())
    primary = next(row for row in runs if row["branch"] == "primary")
    candidates = [row for row in runs if row["branch"] != "primary" and row["status"] == "success"]
    equivalent = [
        row["branch"]
        for row in candidates
        if row["question_id"] == spec["question_id"] and row["parameters"] == spec["fallback_parameters"]
    ]
    drifted = [row["branch"] for row in candidates if row["branch"] not in equivalent]
    return {
        "primary_failed": primary["status"] != "success",
        "selected_branch": equivalent[0] if len(equivalent) == 1 else None,
        "equivalent_branches": equivalent,
        "drifted_branches": drifted,
        "hashes": {name: sha(data / name) for name in ("tool_runs.json", "branch_spec.json", "provenance.json")},
        "rules_version": spec["rules_version"],
    }


def _manifest_hashes(manifest: dict) -> dict | None:
    for key in ("input_sha256", "inputs"):
        value = manifest.get(key)
        if isinstance(value, dict):
            result = {str(name).removeprefix("data/"): digest for name, digest in value.items()}
            result.pop("instruction.md", None)
            return result
        if isinstance(value, list) and all(isinstance(item, dict) for item in value):
            result = {item.get("path", "").removeprefix("data/"): item.get("sha256") for item in value}
            result.pop("instruction.md", None)
            return result
    value = manifest.get("input_hashes")
    if isinstance(value, list) and all(isinstance(item, dict) for item in value):
        result = {item.get("path", "").removeprefix("data/"): item.get("sha256") for item in value}
        result.pop("instruction.md", None)
        return result
    return None


def verify(submission: Path, data: Path, reference: Path) -> tuple[bool, list[str]]:
    exp, errors = expected(data), []
    for name in ("execution_log.jsonl", "failure_recovery.md", "claim_ledger.tsv", "run_manifest.json"):
        if not (submission / name).is_file():
            errors.append("missing artifact: " + name)
    if errors:
        return False, errors

    events = [json.loads(line) for line in (submission / "execution_log.jsonl").read_text().splitlines() if line.strip()]
    if not any(row.get("branch") == "primary" and row.get("status") == "failed" for row in events):
        errors.append("primary failure is not preserved")
    if not any(row.get("branch") == exp["selected_branch"] and row.get("status") in {"success", "selected"} for row in events):
        errors.append("claim-preserving fallback is not selected")
    for branch in exp["drifted_branches"]:
        if not any(row.get("branch") == branch and row.get("status") in {"rejected", "excluded", "scientific_drift"} for row in events):
            errors.append("scientifically drifted fallback is not rejected: " + branch)

    report = (submission / "failure_recovery.md").read_text().lower()
    for concept, terms in {
        "partial output": ("partial", "incomplete"),
        "scientific drift": ("drift", "reference change", "version change"),
        "review boundary": ("review", "human"),
    }.items():
        if not any(term in report for term in terms):
            errors.append("failure recovery omits " + concept)
    ledger = (submission / "claim_ledger.tsv").read_text().lower()
    if exp["selected_branch"].lower() not in ledger:
        errors.append("claim ledger does not identify the selected fallback")
    if "causal" not in report and "causal" not in ledger:
        errors.append("causal claim boundary is not explicit")

    manifest = json.loads((submission / "run_manifest.json").read_text())
    if _manifest_hashes(manifest) != exp["hashes"]:
        errors.append("manifest provenance mismatch")
    if manifest.get("rules_version") != exp["rules_version"]:
        errors.append("manifest rules version mismatch")
    if not (manifest.get("deterministic") is True or manifest.get("reproducibility", {}).get("deterministic") is True):
        errors.append("manifest must declare deterministic execution")
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
