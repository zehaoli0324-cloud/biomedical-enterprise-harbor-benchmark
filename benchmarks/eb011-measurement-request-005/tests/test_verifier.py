import importlib.util
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('verifier', ROOT / 'verifier.py')
verifier = importlib.util.module_from_spec(spec); spec.loader.exec_module(verifier)
def test_expected_is_deterministic(): assert verifier.expected(ROOT / 'data') == verifier.expected(ROOT / 'data')
def test_missing_submission_fails(tmp_path):
    ok, errors = verifier.verify(tmp_path, ROOT / 'data', ROOT / 'verifier_only/reference.json')
    assert not ok and errors
