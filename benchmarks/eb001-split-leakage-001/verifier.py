from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def expected(data_dir: Path) -> dict:
    rows = read_csv(data_dir / "compounds.csv")
    rules = json.loads((data_dir / "split_rules.json").read_text(encoding="utf-8"))
    canonical: dict[str, dict[str, list[str]]] = {}
    scaffolds: dict[str, dict[str, list[str]]] = {}
    for row in rows:
        canonical.setdefault(row["canonical_smiles"], {}).setdefault(row["split"], []).append(row["compound_id"])
        scaffolds.setdefault(row["scaffold_id"], {}).setdefault(row["split"], []).append(row["compound_id"])

    def overlaps(index: dict[str, dict[str, list[str]]], key_name: str) -> list[dict[str, object]]:
        result = []
        for key, splits in index.items():
            if "train" in splits and "test" in splits:
                result.append({key_name: key, "train_ids": sorted(splits["train"]), "test_ids": sorted(splits["test"])})
        return sorted(result, key=lambda item: str(item[key_name]))

    identity_notes = [
        {"compound_id": row["compound_id"], "identity_class": row["identity_note"], "canonical_smiles": row["canonical_smiles"]}
        for row in rows
        if row["identity_note"] != "exact"
    ]
    missing = sorted(row["compound_id"] for row in rows if not row["adme_value"])
    hashes = {name: sha256(data_dir / name) for name in ("compounds.csv", "split_rules.json")}
    return {
        "summary": {
            "row_count": len(rows),
            "train_rows": sum(row["split"] == "train" for row in rows),
            "test_rows": sum(row["split"] == "test" for row in rows),
            "unique_canonical_structures": len(canonical),
            "unique_scaffolds": len(scaffolds),
        },
        "canonical_overlap": overlaps(canonical, "canonical_smiles"),
        "scaffold_overlap": overlaps(scaffolds, "scaffold_id"),
        "identity_notes": identity_notes,
        "missing_measurements": missing,
        "hashes": hashes,
        "rules_version": rules["rules_version"],
    }


def normalize_hashes(payload: dict) -> dict:
    value = payload.get("input_sha256", payload.get("input_hashes"))
    if isinstance(value, dict):
        return {str(name).removeprefix("data/"): digest for name, digest in value.items() if str(name).removeprefix("data/") in {"compounds.csv", "split_rules.json"}}
    source_files = payload.get("fixture", {}).get("source_files", [])
    if isinstance(source_files, list):
        return {str(item.get("path", "")).removeprefix("data/"): item.get("sha256") for item in source_files if str(item.get("path", "")).removeprefix("data/") in {"compounds.csv", "split_rules.json"}}
    return {}


def report_summary(report: dict) -> dict:
    if isinstance(report.get("summary"), dict):
        return report["summary"]
    counts = report.get("dataset_counts", {})
    return {
        "row_count": counts.get("total_rows"), "train_rows": counts.get("train_rows"),
        "test_rows": counts.get("test_rows"), "unique_canonical_structures": counts.get("unique_canonical_structures"),
        "unique_scaffolds": counts.get("unique_scaffolds"),
    }


def overlap_signature(report: dict, kind: str) -> list[tuple[str, tuple[str, ...], tuple[str, ...]]]:
    direct = report.get(f"{kind}_overlap")
    key = "canonical_smiles" if kind == "canonical" else "scaffold_id"
    if isinstance(direct, list):
        return sorted((str(row.get(key)), tuple(sorted(row.get("train_ids", []))), tuple(sorted(row.get("test_ids", [])))) for row in direct)
    block = report.get("canonical_structure_leakage" if kind == "canonical" else "scaffold_leakage", {})
    rows = block.get("affected_canonical_structures" if kind == "canonical" else "affected_scaffolds", [])
    return sorted((str(row.get(key)), tuple(sorted(row.get("train_compound_ids", []))), tuple(sorted(row.get("test_compound_ids", [])))) for row in rows)


def verify(submission: Path, data_dir: Path, reference_path: Path) -> tuple[bool, list[str]]:
    truth = json.loads(reference_path.read_text(encoding="utf-8"))
    exp = expected(data_dir)
    errors: list[str] = []
    report_path = submission / "split_audit.json"
    identity_path = submission / "structure_identity.tsv"
    notes_path = submission / "readiness_report.md"
    manifest_path = submission / "run_manifest.json"
    for path in (report_path, identity_path, notes_path, manifest_path):
        if not path.exists():
            errors.append(f"missing artifact: {path.name}")
    if errors:
        return False, errors

    try:
        report = json.loads(report_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        report = {}
        errors.append(f"invalid split_audit.json: {exc}")
    if report.get("schema_version", report.get("audit_version")) != "1.0":
        errors.append("split_audit.schema_version must be 1.0")
    if report_summary(report) != exp["summary"]:
        errors.append("split_audit.summary mismatch")
    if normalize_hashes(report) and normalize_hashes(report) != exp["hashes"]:
        errors.append("split_audit.input_sha256 mismatch")
    if report.get("rules_version") != exp["rules_version"]:
        errors.append("split_audit.rules_version mismatch")
    for kind in ("canonical", "scaffold"):
        expected_signature = sorted((str(row["canonical_smiles" if kind == "canonical" else "scaffold_id"]), tuple(row["train_ids"]), tuple(row["test_ids"])) for row in exp[f"{kind}_overlap"])
        if overlap_signature(report, kind) != expected_signature:
            errors.append(f"split_audit.{kind}_overlap mismatch")
    missing = report.get("missing_measurements", report.get("endpoint_handling", {}).get("missing_measurement_compound_ids"))
    if missing != exp["missing_measurements"]:
        errors.append("split_audit.missing_measurements mismatch")
    decision = str(report.get("readiness", {}).get("decision", report.get("readiness", {}).get("model_comparison", report.get("decision", "")))).lower()
    if "hold" not in decision and "block" not in decision:
        errors.append("readiness.decision must be blocked")

    identity_rows = read_tsv(identity_path)
    expected_ids = sorted(row["compound_id"] for row in read_csv(data_dir / "compounds.csv"))
    if sorted(row.get("compound_id", "") for row in identity_rows) != expected_ids:
        errors.append("structure_identity.tsv must contain exactly one row per input compound")
    required = {"compound_id", "canonical_smiles", "scaffold_id", "split"}
    if not identity_rows or not required.issubset(identity_rows[0]) or not ({"identity_class", "identity_note"} & set(identity_rows[0])):
        errors.append("structure_identity.tsv is missing required columns")
    source_by_id = {row["compound_id"]: row for row in read_csv(data_dir / "compounds.csv")}
    for row in identity_rows:
        source = source_by_id.get(row.get("compound_id", ""), {})
        if any(row.get(field) != source.get(field) for field in ("canonical_smiles", "scaffold_id", "split")):
            errors.append(f"identity evidence mismatch for {row.get('compound_id')}")
        if row.get("identity_class", row.get("identity_note")) != source.get("identity_note"):
            errors.append(f"identity class mismatch for {row.get('compound_id')}")

    notes = notes_path.read_text(encoding="utf-8").lower()
    for phrase in ("canonical", "scaffold", "salt", "missing", "synthetic"):
        if phrase not in notes:
            errors.append(f"readiness_report.md is missing phrase: {phrase}")

    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        manifest = {}
        errors.append(f"invalid run_manifest.json: {exc}")
    if normalize_hashes(manifest) != exp["hashes"]:
        errors.append("run_manifest.input_sha256 mismatch")
    if manifest.get("rules_version") != exp["rules_version"]:
        errors.append("run_manifest.rules_version mismatch")
    if not (manifest.get("tool_version") or manifest.get("manifest_version")):
        errors.append("run_manifest.tool_version is required")
    deterministic = manifest.get("deterministic") is True or "deterministic" in str(manifest.get("execution", {}).get("ordering", "")).lower()
    if not deterministic:
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
