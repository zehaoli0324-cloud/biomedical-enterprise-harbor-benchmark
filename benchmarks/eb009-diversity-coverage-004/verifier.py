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

def verify(submission: Path, data: Path, reference: Path) -> tuple[bool, list[str]]:
    exp, errors = expected(data), []
    for name in ("candidate_set.tsv", "diversity_report.json", "coverage_review_gate.md", "run_manifest.json"):
        if not (submission / name).is_file(): errors.append("missing artifact: " + name)
    if errors: return False, errors
    report = json.loads((submission / "diversity_report.json").read_text())
    for key in ("candidate_count", "valid_count", "unique_valid_count", "scaffolds", "clusters", "coverage", "rules_version"):
        if report.get(key) != exp[key]: errors.append("diversity report mismatch: " + key)
    if report.get("input_sha256") != exp["hashes"]: errors.append("diversity report provenance mismatch")
    table = (submission / "candidate_set.tsv").read_text().lower()
    for phrase in ("candidate_id", "scaffold", "cluster", "valid"):
        if phrase not in table: errors.append("candidate_set.tsv missing " + phrase)
    gate = (submission / "coverage_review_gate.md").read_text().lower()
    for phrase in ("coverage", "scaffold", "human review", "not biological activity"):
        if phrase not in gate: errors.append("coverage gate missing " + phrase)
    manifest = json.loads((submission / "run_manifest.json").read_text())
    if manifest.get("input_sha256") != exp["hashes"] or manifest.get("rules_version") != exp["rules_version"] or manifest.get("deterministic") is not True: errors.append("run manifest provenance mismatch")
    return not errors, errors

if __name__ == "__main__":
    p = argparse.ArgumentParser(); p.add_argument("--submission", type=Path, required=True); p.add_argument("--data", type=Path, required=True); p.add_argument("--reference", type=Path, required=True)
    a = p.parse_args(); ok, errors = verify(a.submission, a.data, a.reference); print(json.dumps({"passed": ok, "errors": errors})); raise SystemExit(0 if ok else 1)
