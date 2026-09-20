from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path


def _load_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _expected(data_dir: Path) -> dict:
    csv_path = data_dir / "adme_measurements.csv"
    rows = _load_rows(csv_path)
    by_key: dict[str, dict[str, list[str]]] = {}
    for row in rows:
        by_key.setdefault(row["canonical_smiles"], {}).setdefault(row["split"], []).append(row["compound_id"])
    overlap = []
    for key, splits in by_key.items():
        if "train" in splits and "test" in splits:
            overlap.append({"structure_key": key, "train_ids": sorted(splits["train"]), "test_ids": sorted(splits["test"])})
    issues = []
    for row in rows:
        if row["solubility_unit"] != "uM" and row["solubility_value"]:
            value = float(row["solubility_value"])
            converted = value * 1000 if row["solubility_unit"] == "mM" else None
            issues.append({"compound_id": row["compound_id"], "observed_unit": row["solubility_unit"], "converted_to_uM": converted})
    missing = sorted(row["compound_id"] for row in rows if not row["solubility_value"] or row["measurement_status"] == "missing")
    return {
        "row_count": len(rows),
        "train_rows": sum(row["split"] == "train" for row in rows),
        "test_rows": sum(row["split"] == "test" for row in rows),
        "structure_overlap": sorted(overlap, key=lambda item: item["structure_key"]),
        "unit_issues": sorted(issues, key=lambda item: item["compound_id"]),
        "missing_ids": missing,
        "input_sha256": hashlib.sha256(csv_path.read_bytes()).hexdigest(),
    }


def verify(submission: Path, data_dir: Path, reference_path: Path) -> tuple[bool, list[str]]:
    truth = json.loads(reference_path.read_text(encoding="utf-8"))
    expected = _expected(data_dir)
    errors: list[str] = []
    report_path = submission / "audit_report.json"
    notes_path = submission / "audit_notes.md"
    manifest_path = submission / "run_manifest.json"
    if not report_path.exists():
        errors.append("missing audit_report.json")
        return False, errors
    try:
        report = json.loads(report_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return False, [f"invalid audit_report.json: {exc}"]
    summary = report.get("summary", {})
    expected_summary = {key: truth[key] for key in ("row_count", "train_rows", "test_rows")}
    if summary != expected_summary:
        errors.append(f"summary mismatch: expected {expected_summary}, got {summary}")
    if report.get("input_sha256") != expected["input_sha256"]:
        errors.append("input_sha256 does not match the supplied CSV")
    leakage = report.get("leakage", {}).get("structure_overlap")
    if leakage != truth["structure_overlap"]:
        errors.append("structure_overlap mismatch")
    unit_issues = report.get("unit_audit", {}).get("issues")
    if unit_issues != truth["unit_issues"]:
        errors.append("unit_audit.issues mismatch")
    missing_ids = report.get("missingness", {}).get("compound_ids")
    if missing_ids != truth["missing_ids"]:
        errors.append("missingness.compound_ids mismatch")
    if report.get("readiness", {}).get("decision") != "blocked":
        errors.append("readiness.decision must be blocked")
    if not notes_path.exists():
        errors.append("missing audit_notes.md")
    else:
        notes = notes_path.read_text(encoding="utf-8").lower()
        for phrase in ("structure", "unit", "missing", "synthetic", "not establish enterprise validation"):
            if phrase not in notes:
                errors.append(f"audit_notes.md is missing boundary/evidence phrase: {phrase}")
    if not manifest_path.exists():
        errors.append("missing run_manifest.json")
    else:
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            errors.append(f"invalid run_manifest.json: {exc}")
        else:
            if manifest.get("input_sha256") != expected["input_sha256"]:
                errors.append("run_manifest.input_sha256 does not match the supplied CSV")
            if not manifest.get("tool_version"):
                errors.append("run_manifest.tool_version is required")
            if manifest.get("deterministic") is not True:
                errors.append("run_manifest.deterministic must be true")
    return not errors, errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--submission", type=Path, required=True)
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--reference", type=Path, required=True)
    args = parser.parse_args()
    ok, errors = verify(args.submission, args.data, args.reference)
    print(json.dumps({"passed": ok, "errors": errors}, ensure_ascii=False, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
