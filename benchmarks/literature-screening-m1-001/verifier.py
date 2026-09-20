#!/usr/bin/env python3
"""Dependency-free verifier for the offline literature-screening task."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
from pathlib import Path


DECISIONS = {"include", "exclude", "context_only", "uncertain"}


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require_fields(rows: list[dict[str, str]], fields: set[str], label: str, errors: list[str]) -> None:
    if not rows:
        errors.append(f"{label} is empty")
        return
    missing = fields - set(rows[0])
    if missing:
        errors.append(f"{label} missing fields: {sorted(missing)}")


def verify(submission: Path, data: Path, reference: Path) -> dict[str, object]:
    errors: list[str] = []
    records = read_tsv(data / "literature_records.tsv")
    record_ids = [row.get("record_id", "") for row in records]
    if len(record_ids) != len(set(record_ids)):
        errors.append("input record IDs are not unique")
    expected = json.loads(reference.read_text(encoding="utf-8"))

    decision_path = submission / "screening_decisions.tsv"
    evidence_path = submission / "evidence_table.tsv"
    uncertainty_path = submission / "uncertainty_queue.tsv"
    manifest_path = submission / "run_manifest.json"
    report_path = submission / "final_report.md"
    for path in [decision_path, evidence_path, uncertainty_path, manifest_path, report_path]:
        if not path.exists():
            errors.append(f"missing artifact: {path.name}")
    if errors:
        return {"status": "fail", "score": 0, "errors": errors}

    decisions = read_tsv(decision_path)
    require_fields(
        decisions,
        {"record_id", "decision", "reason_code", "confidence", "evidence_locator"},
        "screening_decisions.tsv",
        errors,
    )
    by_id = {row.get("record_id", ""): row for row in decisions}
    if len(decisions) != len(record_ids) or set(by_id) != set(record_ids):
        errors.append("screening_decisions.tsv must contain exactly one row for every input record")
    decision_points = 0
    reason_points = 0
    for record_id, expected_row in expected["decisions"].items():
        row = by_id.get(record_id)
        if row is None:
            continue
        if row.get("decision") not in DECISIONS:
            errors.append(f"{record_id} has invalid decision")
        else:
            decision_points += int(row["decision"] == expected_row["decision"])
        accepted_reasons = expected_row.get("accepted_reason_codes", [expected_row["reason_code"]])
        reason_points += int(row.get("reason_code") in accepted_reasons)
        try:
            confidence = float(row.get("confidence", ""))
            if not 0 <= confidence <= 1:
                raise ValueError
        except ValueError:
            errors.append(f"{record_id} confidence must be between 0 and 1")
        if not row.get("evidence_locator"):
            errors.append(f"{record_id} requires evidence_locator")
    if decision_points != len(expected["decisions"]):
        errors.append("one or more screening decisions do not match the reference labels")
    if reason_points != len(expected["decisions"]):
        errors.append("one or more screening reason codes do not match the reference labels")

    evidence = read_tsv(evidence_path)
    require_fields(
        evidence,
        {"claim_id", "source_id", "evidence_type", "support_status", "locator", "limitation"},
        "evidence_table.tsv",
        errors,
    )
    sources = {row.get("source_id") for row in evidence}
    evidence_points = 0
    for source_id in expected["required_evidence_sources"]:
        rows = [row for row in evidence if row.get("source_id") == source_id]
        if not rows:
            errors.append(f"missing evidence row for {source_id}")
            continue
        evidence_points += 1
        for row in rows:
            if not row.get("locator") or not row.get("limitation"):
                errors.append(f"evidence row for {source_id} needs locator and limitation")
    context_rows = [row for row in evidence if row.get("source_id") in expected["context_only_records"]]
    if context_rows and any(
        "not_causal" not in row.get("support_status", "").lower().replace("-", "_")
        and ("causal" in row.get("support_status", "").lower() or "mechanism" in row.get("support_status", "").lower())
        for row in context_rows
    ):
        errors.append("association-only source cannot have causal support status")
    for row in evidence:
        if row.get("source_id") not in record_ids:
            errors.append(f"evidence references unknown source {row.get('source_id')}")

    uncertainty = read_tsv(uncertainty_path)
    require_fields(
        uncertainty,
        {"record_id", "uncertainty_reason", "minimum_next_check"},
        "uncertainty_queue.tsv",
        errors,
    )
    uncertain_ids = {row.get("record_id") for row in uncertainty}
    uncertainty_points = int(set(expected["uncertain_records"]).issubset(uncertain_ids))
    for row in uncertainty:
        if not row.get("uncertainty_reason") or not row.get("minimum_next_check"):
            errors.append("uncertainty rows need a reason and minimum next check")

    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        manifest = {}
        errors.append("run_manifest.json is not valid JSON")
    if manifest.get("input_sha256") != sha256(data / "literature_records.tsv"):
        errors.append("run_manifest input_sha256 does not match literature_records.tsv")
    if manifest.get("rules_version") != expected["rules_version"]:
        errors.append("run_manifest rules_version does not match the task")
    if not manifest.get("tool_version"):
        errors.append("run_manifest requires tool_version")
    reproducibility_points = int(not any("run_manifest" in error for error in errors))

    report = report_path.read_text(encoding="utf-8")
    for heading in ["Screening summary", "Evidence boundary", "Uncertainty", "Next step"]:
        if not re.search(rf"^#{{1,6}}\s+{re.escape(heading)}\s*$", report, re.MULTILINE):
            errors.append(f"final_report.md missing heading: {heading}")
    if not re.search(r"causal|因果", report, re.IGNORECASE):
        errors.append("final_report.md must state a causal boundary")
    if not re.search(r"uncertain|不确定|insufficient|不足", report, re.IGNORECASE):
        errors.append("final_report.md must report uncertainty")

    total = len(expected["decisions"])
    score = round(
        45 * decision_points / total
        + 20 * reason_points / total
        + 20 * evidence_points / len(expected["required_evidence_sources"])
        + 10 * uncertainty_points
        + 5 * reproducibility_points,
        2,
    )
    return {
        "status": "pass" if not errors else "fail",
        "score": score,
        "metrics": {
            "decision_accuracy": round(decision_points / total, 4),
            "reason_accuracy": round(reason_points / total, 4),
            "evidence_source_coverage": round(evidence_points / len(expected["required_evidence_sources"]), 4),
            "uncertainty_queue": uncertainty_points,
            "reproducibility": reproducibility_points,
        },
        "errors": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--submission", type=Path, required=True)
    parser.add_argument("--data", type=Path, default=Path("data"))
    parser.add_argument("--reference", type=Path, default=Path("verifier_only/reference_labels.json"))
    args = parser.parse_args()
    result = verify(args.submission, args.data, args.reference)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
