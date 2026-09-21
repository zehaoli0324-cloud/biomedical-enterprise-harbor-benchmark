import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("verifier", ROOT / "verifier.py")
verifier = importlib.util.module_from_spec(spec)
assert spec.loader
spec.loader.exec_module(verifier)


def test_expected_is_deterministic_and_selects_eligible_option():
    first = verifier.expected(ROOT / "data")
    assert first == verifier.expected(ROOT / "data")
    assert first["selected_measurement_id"] == "M-01"
    assert first["eligible_count"] == 3


def test_missing_submission_fails(tmp_path):
    passed, errors = verifier.verify(tmp_path, ROOT / "data", ROOT / "verifier_only/reference.json")
    assert not passed
    assert errors
