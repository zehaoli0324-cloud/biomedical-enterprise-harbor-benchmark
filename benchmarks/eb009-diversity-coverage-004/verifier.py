from __future__ import annotations
import argparse, csv, hashlib, json
from pathlib import Path

def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def expected(data: Path) -> dict:
    rows = list(csv.DictReader((data / "candidates.csv").open(newline="", encoding="utf-8")))
    rules = json.loads((data / "rules.json").read_text())
    valid = [r for r in rows if r["valid"] == "true"]
    unique = {r["candidate_id"] for r in valid}
    scaffolds = sorted({r["scaffold"] for r in valid})
    clusters = sorted({r["cluster"] for r in valid})
    covered = len(scaffolds) >= rules["minimum_scaffolds"] and len(clusters) >= rules["minimum_clusters"]
    return {"candidate_count": len(rows), "valid_count": len(valid), "unique_valid_count": len(unique), "scaffolds": scaffolds, "clusters": clusters, "coverage": covered, "rules_version": rules["rules_version"], "hashes": {"candidates.csv": sha(data / "candidates.csv"), "rules.json": sha(data / "rules.json")}}

def _hashes(payload: dict) -> dict:
    value = payload.get("input_sha256", payload.get("input_hashes", {}))
    if not isinstance(value, dict):
        return {}
    return {str(key).removeprefix("data/"): digest for key, digest in value.items()}

def _report_value(report: dict, key: str):
    counts = report.get("counts", {}) if isinstance(report.get("counts"), dict) else {}
    coverage = report.get("coverage", {}) if isinstance(report.get("coverage"), dict) else {}
    aliases = {
        "candidate_count": ("candidate_count", "input_rows"),
        "valid_count": ("valid_count", "valid_candidates"),
        "unique_valid_count": ("unique_valid_count",),
    }
    if key in aliases:
        for name in aliases[key]:
            if name in report: return report[name]
            if name in counts: return counts[name]
    if key == "unique_valid_count" and "valid_candidates" in counts and "duplicate_candidate_ids" in counts:
        return counts["valid_candidates"] - counts["duplicate_candidate_ids"]
    if key == "coverage":
        if isinstance(report.get("coverage"), bool): return report["coverage"]
        for name in ("passes", "covered", "coverage_pass"):
            if name in coverage: return coverage[name]
    return report.get(key)

def verify(submission: Path, data: Path, reference: Path) -> tuple[bool, list[str]]:
    exp, errors = expected(data), []
    for name in ("candidate_set.tsv", "diversity_report.json", "coverage_review_gate.md", "run_manifest.json"):
        if not (submission / name).is_file(): errors.append("missing artifact: " + name)
    if errors: return False, errors
    report = json.loads((submission / "diversity_report.json").read_text())
    for key in ("candidate_count", "valid_count", "unique_valid_count", "scaffolds", "clusters", "coverage", "rules_version"):
        if _report_value(report, key) != exp[key]: errors.append("diversity report mismatch: " + key)
    if _hashes(report) != exp["hashes"]: errors.append("diversity report provenance mismatch")
    table_path = submission / "candidate_set.tsv"
    table = table_path.read_text().lower()
    for phrase in ("candidate_id", "scaffold", "cluster", "valid"):
        if phrase not in table: errors.append("candidate_set.tsv missing " + phrase)
    submitted_rows = list(csv.DictReader(table_path.open(), delimiter="\t"))
    source_rows = list(csv.DictReader((data / "candidates.csv").open()))
    fields = ("candidate_id", "scaffold", "cluster", "valid")
    if sorted(tuple(row.get(field, "") for field in fields) for row in submitted_rows) != sorted(tuple(row[field] for field in fields) for row in source_rows):
        errors.append("candidate_set.tsv does not match input candidates")
    gate = (submission / "coverage_review_gate.md").read_text().lower()
    for phrase in ("coverage", "scaffold", "human review", "not biological activity"):
        if phrase not in gate: errors.append("coverage gate missing " + phrase)
    manifest = json.loads((submission / "run_manifest.json").read_text())
    if _hashes(manifest) != exp["hashes"] or manifest.get("rules_version") != exp["rules_version"] or manifest.get("deterministic") is not True: errors.append("run manifest provenance mismatch")
    return not errors, errors

if __name__ == "__main__":
    p = argparse.ArgumentParser(); p.add_argument("--submission", type=Path, required=True); p.add_argument("--data", type=Path, required=True); p.add_argument("--reference", type=Path, required=True)
    a = p.parse_args(); ok, errors = verify(a.submission, a.data, a.reference); print(json.dumps({"passed": ok, "errors": errors})); raise SystemExit(0 if ok else 1)
