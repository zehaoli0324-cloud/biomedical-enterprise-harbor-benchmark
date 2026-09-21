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
    decisions = {}
    eligible = []
    invariants = spec["registered_invariants"]
    for row in runs:
        branch = row["branch"]
        if branch == "primary":
            decisions[branch] = {"status": "failed", "failed_invariants": ["primary_failed"]}
            continue
        failed = []
        if row.get("scope") != spec["decision_scope"]:
            failed.append("scope")
        for field in ("question_id", "estimand", "cohort", "reference", "version", "input_digest"):
            if row.get(field) != invariants[field]:
                failed.append(field)
        try:
            tool_major = int(str(row.get("tool_version", "")).split(".", 1)[0])
        except ValueError:
            tool_major = None
        if tool_major != invariants["tool_major_version"]:
            failed.append("tool_major_version")
        for field in spec["required_provenance"]:
            if row.get(field) in (None, "") and field not in failed:
                failed.append(field)
        if row.get("status") != "success":
            failed.append("execution_status")
        if not failed:
            eligible.append(branch)
            status = "selected"
        elif "scope" in failed:
            status = "excluded"
        elif any(field in failed for field in spec["required_provenance"]):
            status = "provenance_incomplete"
        else:
            status = "scientific_drift"
        decisions[branch] = {"status": status, "failed_invariants": sorted(failed)}
    selected = eligible[0] if len(eligible) == 1 else None
    if selected is None:
        for branch in eligible:
            decisions[branch]["status"] = "hold_ambiguous"
    return {
        "primary_failed": primary["status"] != "success",
        "selected_branch": selected,
        "eligible_branches": eligible,
        "decisions": decisions,
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
    by_branch = {row.get("branch"): row for row in events}
    if set(by_branch) != set(exp["decisions"]):
        errors.append("execution log must cover every branch exactly once")
    accepted_statuses = {
        "failed": {"failed"},
        "selected": {"selected", "success"},
        "excluded": {"excluded"},
        "provenance_incomplete": {"provenance_incomplete", "rejected"},
        "scientific_drift": {"scientific_drift", "rejected"},
        "hold_ambiguous": {"hold", "hold_ambiguous"},
    }
    for branch, decision in exp["decisions"].items():
        row = by_branch.get(branch, {})
        if row.get("status") not in accepted_statuses[decision["status"]]:
            errors.append(f"{branch} disposition mismatch")
        actual_failed = row.get("failed_invariants", [])
        if isinstance(actual_failed, str):
            actual_failed = [item.strip() for item in actual_failed.split(",") if item.strip()]
        if sorted(actual_failed) != decision["failed_invariants"]:
            errors.append(f"{branch} failed invariants mismatch")

    report = (submission / "failure_recovery.md").read_text().lower()
    for concept, terms in {
        "partial output": ("partial", "incomplete"),
        "scientific drift": ("drift", "reference", "cohort", "estimand"),
        "provenance blocker": ("provenance", "digest"),
        "scope exclusion": ("pilot", "archiv", "scope"),
        "review boundary": ("review", "human"),
    }.items():
        if not any(term in report for term in terms):
            errors.append("failure recovery omits " + concept)
    ledger = (submission / "claim_ledger.tsv").read_text().lower()
    if exp["selected_branch"] and exp["selected_branch"].lower() not in ledger:
        errors.append("claim ledger does not identify the selected fallback")
    if "blocker" not in ledger.splitlines()[0].split("\t"):
        errors.append("claim ledger lacks blocker column")
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
