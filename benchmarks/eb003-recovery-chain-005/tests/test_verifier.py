import csv
import importlib.util
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('verifier', ROOT / 'verifier.py')
verifier = importlib.util.module_from_spec(spec); spec.loader.exec_module(verifier)
def test_expected_is_deterministic(): assert verifier.expected(ROOT / 'data') == verifier.expected(ROOT / 'data')
def test_missing_submission_fails(tmp_path):
    ok, errors = verifier.verify(tmp_path, ROOT / 'data', ROOT / 'verifier_only/reference.json')
    assert not ok and errors
def test_reference_shape_passes(tmp_path):
    exp = verifier.expected(ROOT / 'data')
    (tmp_path / 'decision.json').write_text(json.dumps({'decision': exp['decision'], 'rules_version': exp['rules_version']}))
    fields = ['entity', 'outcome', 'decision', 'provenance', 'uncertainty', 'claim_boundary']
    rows = [{'entity': entity, 'outcome': str(exp['outcomes'][entity]), 'decision': exp['decision'], 'provenance': 'case.json#' + entity, 'uncertainty': 'bounded fixture', 'claim_boundary': 'not experimental proof'} for entity in exp['entities']]
    with (tmp_path / 'evidence.tsv').open('w', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, delimiter='\t'); writer.writeheader(); writer.writerows(rows)
    (tmp_path / 'review.md').write_text('Human review remains required; stop on missing evidence. This is not experimental proof.')
    (tmp_path / 'manifest.json').write_text(json.dumps({'input_sha256': exp['hashes'], 'rules_version': exp['rules_version'], 'deterministic': True}))
    ok, errors = verifier.verify(tmp_path, ROOT / 'data', ROOT / 'verifier_only/reference.json')
    assert ok, errors
