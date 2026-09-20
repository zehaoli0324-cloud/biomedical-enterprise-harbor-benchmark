import csv
import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("eb001_verifier", ROOT / "verifier.py")
assert spec and spec.loader
verifier = importlib.util.module_from_spec(spec)
spec.loader.exec_module(verifier)


def test_expected_fixture_has_both_leakage_levels():
    result = verifier.expected(ROOT / "data")
    assert result["summary"] == {
        "row_count": 8,
        "train_rows": 4,
        "test_rows": 4,
        "unique_canonical_structures": 6,
        "unique_scaffolds": 5,
    }
    assert len(result["canonical_overlap"]) == 1
    assert len(result["scaffold_overlap"]) == 2
    assert result["missing_measurements"] == ["CMP-108"]


def test_verifier_rejects_missing_submission(tmp_path: Path):
    ok, errors = verifier.verify(tmp_path, ROOT / "data", ROOT / "verifier_only/reference.json")
    assert not ok
    assert any("missing artifact" in error for error in errors)


def test_reference_shaped_submission_passes(tmp_path: Path):
    result = verifier.expected(ROOT / "data")
    report = {
        "schema_version": "1.0",
        "input_sha256": result["hashes"],
        "rules_version": result["rules_version"],
        "summary": result["summary"],
        "canonical_overlap": result["canonical_overlap"],
        "scaffold_overlap": result["scaffold_overlap"],
        "identity_notes": result["identity_notes"],
        "missing_measurements": result["missing_measurements"],
        "readiness": {"decision": "blocked"},
    }
    (tmp_path / "split_audit.json").write_text(json.dumps(report), encoding="utf-8")
    rows = verifier.read_csv(ROOT / "data/compounds.csv")
    with (tmp_path / "structure_identity.tsv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["compound_id", "canonical_smiles", "scaffold_id", "split", "identity_class", "evidence"], delimiter="\t")
        writer.writeheader()
        for row in rows:
            writer.writerow({
                "compound_id": row["compound_id"],
                "canonical_smiles": row["canonical_smiles"],
                "scaffold_id": row["scaffold_id"],
                "split": row["split"],
                "identity_class": row["identity_note"],
                "evidence": f"CSV:{row['compound_id']}",
            })
    (tmp_path / "readiness_report.md").write_text("canonical scaffold salt missing synthetic enterprise validation", encoding="utf-8")
    (tmp_path / "run_manifest.json").write_text(json.dumps({"input_sha256": result["hashes"], "rules_version": result["rules_version"], "tool_version": "test", "deterministic": True}), encoding="utf-8")
    ok, errors = verifier.verify(tmp_path, ROOT / "data", ROOT / "verifier_only/reference.json")
    assert ok, errors
