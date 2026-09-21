import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('verifier', ROOT / 'verifier.py')
assert spec and spec.loader
verifier = importlib.util.module_from_spec(spec)
spec.loader.exec_module(verifier)

def test_expected_fixture_is_deterministic():
    result = verifier.expected(ROOT / 'data')
    assert result == verifier.expected(ROOT / 'data')

def test_missing_submission_fails(tmp_path):
    ok, errors = verifier.verify(tmp_path, ROOT / 'data', ROOT / 'verifier_only/reference.json')
    assert not ok and errors
