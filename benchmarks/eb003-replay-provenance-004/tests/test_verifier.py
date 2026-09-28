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

def test_missing_rerun_is_held_not_fabricated(tmp_path):
    exp = verifier.expected(ROOT / 'data')
    assert exp['replay_status'] == 'not_run'
    (tmp_path / 'replay_manifest.json').write_text(json.dumps({
        'artifact_id': exp['artifact_id'], 'rules_version': exp['rules_version'],
        'input_hashes': exp['input_hashes'], 'output_hashes': exp['output_hashes'],
        'environment': exp['environment'], 'replay_status': 'not_run',
        'human_review': 'required'}))
    with (tmp_path / 'provenance_diff.tsv').open('w', newline='') as handle:
        writer = csv.writer(handle, delimiter='\t'); writer.writerow(['field', 'status', 'match'])
        writer.writerow(['rerun_result', 'missing', 'unknown'])
    (tmp_path / 'handoff_replay_report.md').write_text(
        'Replay held: no rerun result or checksum evidence. Human review required. Not biological validation.')
    ok, errors = verifier.verify(tmp_path, ROOT / 'data', ROOT / 'verifier_only/reference.json')
    assert ok, errors
