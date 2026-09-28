import csv, importlib.util, json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('verifier', ROOT / 'verifier.py')
verifier = importlib.util.module_from_spec(spec); spec.loader.exec_module(verifier)
def test_expected_deterministic():
    assert verifier.expected(ROOT / 'data') == verifier.expected(ROOT / 'data')
def test_missing_submission_fails(tmp_path):
    ok, errors = verifier.verify(tmp_path, ROOT / 'data', ROOT / 'verifier_only/reference.json')
    assert not ok and errors

def test_equivalent_nested_report_and_prefixed_hashes_pass(tmp_path):
    exp = verifier.expected(ROOT / 'data')
    prefixed = {'data/' + key: value for key, value in exp['hashes'].items()}
    report = {
        'rules_version': exp['rules_version'],
        'counts': {'input_rows': exp['candidate_count'], 'valid_candidates': exp['valid_count'],
                   'unique_candidate_ids': exp['candidate_count'], 'duplicate_candidate_ids': 0},
        'scaffolds': exp['scaffolds'], 'clusters': exp['clusters'],
        'coverage': {'passes': exp['coverage']}, 'input_hashes': prefixed,
    }
    (tmp_path / 'diversity_report.json').write_text(json.dumps(report))
    rows = list(csv.DictReader((ROOT / 'data/candidates.csv').open()))
    with (tmp_path / 'candidate_set.tsv').open('w', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=rows[0], delimiter='\t'); writer.writeheader(); writer.writerows(rows)
    (tmp_path / 'coverage_review_gate.md').write_text('Coverage and scaffold evidence; human review; not biological activity.')
    (tmp_path / 'run_manifest.json').write_text(json.dumps({'input_hashes': prefixed, 'rules_version': exp['rules_version'], 'deterministic': True}))
    ok, errors = verifier.verify(tmp_path, ROOT / 'data', ROOT / 'verifier_only/reference.json')
    assert ok, errors
