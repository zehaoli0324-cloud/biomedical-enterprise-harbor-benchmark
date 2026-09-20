import csv
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
_SPEC = importlib.util.spec_from_file_location("admiral_adsl_verifier", ROOT / "verifier.py")
assert _SPEC and _SPEC.loader
verifier = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(verifier)


def test_expected_fixture_has_four_edge_cases():
    result = verifier.expected(ROOT / "data")
    assert result["summary"] == {
        "subject_count": 6,
        "randomized_count": 5,
        "treated_count": 4,
        "itt_count": 5,
        "saffl_count": 4,
        "pprot_count": 2,
    }
    assert result["rows"][4]["TRTEDT"] == "2024-02-28"
    assert result["rows"][4]["TRTEDT_DTYPE"] == "CUTOFF"


def test_verifier_rejects_missing_submission(tmp_path: Path):
    ok, errors = verifier.verify(tmp_path, ROOT / "data", ROOT / "verifier_only/reference.json")
    assert not ok
    assert any("missing artifact" in error for error in errors)


def test_reference_shaped_submission_passes(tmp_path: Path):
    result = verifier.expected(ROOT / "data")
    with (tmp_path / "adsl.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=verifier.REQUIRED_ADSL)
        writer.writeheader()
        writer.writerows(result["rows"])
    with (tmp_path / "derivation_trace.csv").open("w", newline="", encoding="utf-8") as handle:
        fields = ["USUBJID", "target_variable", "source_domain", "source_rows", "rule_id", "derived_value"]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in result["rows"]:
            for target in verifier.TRACE_TARGETS:
                writer.writerow({
                    "USUBJID": row["USUBJID"],
                    "target_variable": target,
                    "source_domain": "DM+EX",
                    "source_rows": f"DM:{row['USUBJID']}",
                    "rule_id": "TEST_RULE",
                    "derived_value": row[target] or "NA",
                })
    (tmp_path / "audit_report.json").write_text(json.dumps({
        "schema_version": "1.0",
        "summary": result["summary"],
        "rules_version": result["rules_version"],
        "input_sha256": result["hashes"],
        "edge_cases": result["edge_cases"],
        "handoff": {"decision": "hold_for_review"},
        "claim_boundary": "Synthetic fixture; not clinical and not sponsor data.",
    }), encoding="utf-8")
    (tmp_path / "derivation_notes.md").write_text("screen failure; no exposure; missing RFENDTC; cutoff; synthetic", encoding="utf-8")
    (tmp_path / "run_manifest.json").write_text(json.dumps({
        "input_sha256": result["hashes"],
        "rules_version": result["rules_version"],
        "tool_version": "test",
        "deterministic": True,
    }), encoding="utf-8")
    ok, errors = verifier.verify(tmp_path, ROOT / "data", ROOT / "verifier_only/reference.json")
    assert ok, errors
