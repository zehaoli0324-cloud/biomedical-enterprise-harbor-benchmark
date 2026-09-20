from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).parents[3]
TASK = ROOT / "benchmarks/biogen-adme-audit-001"


def _write_valid_submission(path: Path) -> None:
    report = {
        "schema_version": "1.0",
        "input_sha256": __import__("hashlib").sha256((TASK / "data/adme_measurements.csv").read_bytes()).hexdigest(),
        "summary": {"row_count": 8, "train_rows": 4, "test_rows": 4},
        "leakage": {"structure_overlap": [{"structure_key": "c1ccccc1", "train_ids": ["CMP-003"], "test_ids": ["CMP-008"]}]},
        "unit_audit": {"expected_unit": "uM", "issues": [{"compound_id": "CMP-007", "observed_unit": "mM", "converted_to_uM": 500.0}]},
        "missingness": {"compound_ids": ["CMP-006"]},
        "readiness": {"decision": "blocked", "reason": "leakage, unit and missingness issues"},
    }
    path.mkdir()
    (path / "audit_report.json").write_text(json.dumps(report), encoding="utf-8")
    (path / "audit_notes.md").write_text("structure overlap; unit issue; missing value; synthetic fixture; not establish enterprise validation", encoding="utf-8")
    (path / "run_manifest.json").write_text(json.dumps({"input_sha256": report["input_sha256"], "tool_version": "pytest", "deterministic": True}), encoding="utf-8")


def test_valid_submission_passes(tmp_path: Path) -> None:
    submission = tmp_path / "outputs"
    _write_valid_submission(submission)
    result = subprocess.run(
        [sys.executable, str(TASK / "verifier.py"), "--submission", str(submission), "--data", str(TASK / "data"), "--reference", str(TASK / "verifier_only/reference.json")],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_wrong_readiness_is_rejected(tmp_path: Path) -> None:
    submission = tmp_path / "outputs"
    _write_valid_submission(submission)
    report_path = submission / "audit_report.json"
    report = json.loads(report_path.read_text(encoding="utf-8"))
    report["readiness"]["decision"] = "ready"
    report_path.write_text(json.dumps(report), encoding="utf-8")
    result = subprocess.run(
        [sys.executable, str(TASK / "verifier.py"), "--submission", str(submission), "--data", str(TASK / "data"), "--reference", str(TASK / "verifier_only/reference.json")],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1
