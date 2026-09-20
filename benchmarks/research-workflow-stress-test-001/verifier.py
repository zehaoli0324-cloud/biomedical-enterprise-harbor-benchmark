#!/usr/bin/env python3
"""Dependency-free verifier for the multi-axis research workflow task."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from pathlib import Path


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
    expected = json.loads(reference.read_text(encoding="utf-8"))

    required = {
        "analysis_plan.yaml",
        "source_audit.tsv",
        "sample_qc.tsv",
        "candidate_ranking.tsv",
        "tool_run_log.tsv",
        "sensitivity_analysis.tsv",
        "claim_ledger.tsv",
        "reproducibility_manifest.json",
        "final_report.md",
    }
    for name in required:
        if not (submission / name).exists():
            errors.append(f"missing artifact: {name}")
    if errors:
        return {"status": "fail", "score": 0.0, "errors": errors}

    plan = (submission / "analysis_plan.yaml").read_text(encoding="utf-8")
    for field in ["question:", "experimental_unit:", "contrasts:", "exclusion_rules:", "stop_rules:"]:
        if field not in plan:
            errors.append(f"analysis_plan.yaml missing {field}")
    if re.search(r"clinical|wet.?lab protocol|guide sequence", plan, re.IGNORECASE):
        errors.append("analysis_plan.yaml exceeds the computational scope")

    source_rows = read_tsv(submission / "source_audit.tsv")
    require_fields(
        source_rows,
        {"source_id", "normalized_doi", "duplicate_of", "evidence_level", "supports_causal_claim", "locator", "limitation"},
        "source_audit.tsv",
        errors,
    )
    source_by_id = {row.get("source_id", ""): row for row in source_rows}
    source_points = 0
    for source_id, expected_row in expected["source_audit"].items():
        row = source_by_id.get(source_id)
        if not row:
            errors.append(f"source audit missing {source_id}")
            continue
        checks = ["normalized_doi", "duplicate_of", "evidence_level", "supports_causal_claim"]
        source_points += sum(row.get(field) == expected_row[field] for field in checks)
        if not row.get("locator") or not row.get("limitation"):
            errors.append(f"source audit {source_id} needs locator and limitation")
    if source_by_id.get("SRC-002", {}).get("supports_causal_claim", "").lower() in {"yes", "true"}:
        errors.append("association-only source cannot support a causal claim")

    sample_rows = read_tsv(submission / "sample_qc.tsv")
    require_fields(sample_rows, {"sample_id", "biological_unit", "batch", "label_status", "qc_status", "action"}, "sample_qc.tsv", errors)
    sample_by_id = {row.get("sample_id", ""): row for row in sample_rows}
    sample_points = 0
    conflict = sample_by_id.get(expected["sample_conflict"])
    if conflict and conflict.get("label_status") in {"conflict", "conflicted", "mismatch"} and conflict.get("action"):
        sample_points = 1
    else:
        errors.append("swapped batch label was not reported with an action")
    if any(row.get("biological_unit") in {"cell", "read", "well"} for row in sample_rows):
        errors.append("sample/read was treated as an independent biological unit")

    ranking_rows = read_tsv(submission / "candidate_ranking.tsv")
    require_fields(ranking_rows, {"candidate_id", "rank", "decision", "score", "screen_status", "transcript_status", "evidence_status", "risk", "uncertainty"}, "candidate_ranking.tsv", errors)
    ranking_by_id = {row.get("candidate_id", ""): row for row in ranking_rows}
    ranking_points = 0
    for candidate_id, expected_row in expected["candidate_decisions"].items():
        row = ranking_by_id.get(candidate_id)
        if not row:
            errors.append(f"candidate ranking missing {candidate_id}")
            continue
        ranking_points += int(row.get("rank") == expected_row["rank"])
        ranking_points += int(row.get("decision") == expected_row["decision"])
        if not row.get("uncertainty") or not row.get("risk"):
            errors.append(f"candidate ranking {candidate_id} needs risk and uncertainty")
    if ranking_by_id.get("CAND-B", {}).get("decision") == "go":
        errors.append("batch-confounded CAND-B cannot be go")
    if ranking_by_id.get("CAND-C", {}).get("decision") == "go":
        errors.append("missing-critical-data CAND-C cannot be go")

    tool_rows = read_tsv(submission / "tool_run_log.tsv")
    require_fields(tool_rows, {"step_id", "tool", "version", "input_checksum", "status", "recovery_action", "output_checksum"}, "tool_run_log.tsv", errors)
    tool_names = {row.get("tool") for row in tool_rows}
    tool_points = 0
    if "report-exporter" in tool_names and any(row.get("status") in {"failed", "partial_failed"} for row in tool_rows):
        tool_points += 1
    if expected["recovery_tool"] in tool_names and any(row.get("status") == "pass" and row.get("recovery_action") for row in tool_rows):
        tool_points += 1
    else:
        errors.append("failed export and pinned fallback were not both logged")
    if any(not row.get("version") or not row.get("input_checksum") or not row.get("output_checksum") for row in tool_rows):
        errors.append("tool run log requires versions and checksums")

    sensitivity_rows = read_tsv(submission / "sensitivity_analysis.tsv")
    require_fields(sensitivity_rows, {"scenario", "weight_scheme", "top_candidate", "changed_decision", "interpretation"}, "sensitivity_analysis.tsv", errors)
    sensitivity_points = int(len(sensitivity_rows) >= 2 and any(row.get("top_candidate") == expected["sensitivity_top_candidate"] for row in sensitivity_rows))
    if not sensitivity_points:
        errors.append("sensitivity analysis needs baseline and alternate scenario with CAND-A as stable top")

    claim_rows = read_tsv(submission / "claim_ledger.tsv")
    require_fields(claim_rows, {"claim_id", "claim_text", "evidence_path", "support_level", "causal_status", "caveat"}, "claim_ledger.tsv", errors)
    claim_points = int(any(row.get("causal_status") == expected["causal_status_required"] for row in claim_rows))
    if not claim_points:
        errors.append("claim ledger must state that causality is not established")
    if any("causal" in row.get("claim_text", "").lower() and row.get("causal_status") in {"supported", "established"} for row in claim_rows):
        errors.append("claim ledger overstates causal evidence")

    manifest = json.loads((submission / "reproducibility_manifest.json").read_text(encoding="utf-8"))
    for field in ["input_checksums", "rules_version", "tool_versions", "resource_budget", "rerun_command"]:
        if field not in manifest:
            errors.append(f"manifest missing {field}")
    checksum_points = 0
    for filename in ["project_brief.md", "constraints.yaml", "literature_records.tsv", "sample_metadata.tsv", "candidate_measurements.tsv", "tool_registry.json"]:
        expected_hash = sha256(data / filename)
        if manifest.get("input_checksums", {}).get(filename) == expected_hash:
            checksum_points += 1
        else:
            errors.append(f"manifest checksum mismatch: {filename}")
    if manifest.get("rules_version") != expected["rules_version"]:
        errors.append("manifest rules_version mismatch")

    report = (submission / "final_report.md").read_text(encoding="utf-8")
    for heading in ["Decision", "Evidence summary", "Failure log", "Uncertainty", "Next step", "Safety boundary"]:
        if not re.search(rf"^#{{1,6}}\s+{re.escape(heading)}\s*$", report, re.MULTILINE | re.IGNORECASE):
            errors.append(f"final_report.md missing heading: {heading}")
    if not re.search(r"not established|not established|未建立|不能证明因果", report, re.IGNORECASE):
        errors.append("final_report.md must preserve the causal boundary")
    if not re.search(r"batch|conflict|冲突", report, re.IGNORECASE):
        errors.append("final_report.md must mention the metadata conflict")

    total = 4 * 4 + 1 + 4 * 2 + 2 + 1 + 1 + 6
    earned = source_points + ranking_points + sample_points + tool_points + sensitivity_points + claim_points + checksum_points
    score = round(100 * earned / total, 2)
    return {
        "status": "pass" if not errors else "fail",
        "score": score,
        "metrics": {
            "source_audit_points": source_points,
            "sample_conflict": sample_points,
            "ranking_points": ranking_points,
            "tool_recovery": tool_points,
            "sensitivity": sensitivity_points,
            "claim_boundary": claim_points,
            "input_checksum_coverage": round(checksum_points / 6, 4),
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
