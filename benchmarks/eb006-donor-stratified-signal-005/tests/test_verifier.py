import importlib.util
import runpy
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("verifier", ROOT / "verifier.py")
verifier = importlib.util.module_from_spec(spec)
spec.loader.exec_module(verifier)


def test_reference_passes(tmp_path):
    calibration = runpy.run_path(str(ROOT / "run_calibration.py"))
    calibration["write_reference"](verifier, tmp_path)
    passed, errors = verifier.verify(tmp_path, ROOT / "data", ROOT / "verifier_only/reference.json")
    assert passed, errors


def test_oracle_exposes_targeted_scientific_traps():
    truth = verifier.expected(ROOT / "data")
    summaries = {row["candidate_id"]: row for row in truth["summaries"]}
    diagnostics = {(row["candidate_id"], row["state"]): row for row in truth["diagnostics"]}
    assert truth["selected"] == "method_gamma"
    assert summaries["method_beta"]["decision"] == "CONTRADICTORY"
    assert diagnostics[("method_beta", "early")]["nonpositive_donors"] == ["D4"]
    assert diagnostics[("method_gamma", "late")]["missing_donors"] == ["D4"]
    assert diagnostics[("method_gamma", "late")]["status"] == "SUPPORTED"


def test_calibration_controls_pass():
    calibration = runpy.run_path(str(ROOT / "run_calibration.py"))
    assert calibration["main"]() == 0
