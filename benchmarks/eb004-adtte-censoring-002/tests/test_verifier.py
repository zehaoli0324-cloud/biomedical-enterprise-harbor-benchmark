import csv
import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("eb004_verifier", ROOT / "verifier.py")
assert spec and spec.loader
verifier = importlib.util.module_from_spec(spec)
spec.loader.exec_module(verifier)


def test_expected_endpoint_cases():
    result = verifier.expected(ROOT / "data")
    assert result["summary"] == {"subject_count": 6, "event_count": 2, "censor_count": 2, "review_count": 2}
    by_id = {row["USUBJID"]: row for row in result["rows"]}
    assert by_id["SUBJ-202"]["EVNTDESC"] == "DEATH"
    assert by_id["SUBJ-203"]["ADT_DTYPE"] == "CUTOFF"
    assert by_id["SUBJ-206"]["DERIVATION_STATUS"] == "REVIEW"
    assert result["edge_cases"] == [
        {"id": "SUBJ-202", "type": "competing_events"},
        {"id": "SUBJ-203", "type": "post_cutoff_event"},
        {"id": "SUBJ-205", "type": "missing_followup"},
        {"id": "SUBJ-206", "type": "partial_date"},
    ]


def test_verifier_rejects_missing_submission(tmp_path: Path):
    ok, errors = verifier.verify(tmp_path, ROOT / "data", ROOT / "verifier_only/reference.json")
    assert not ok
    assert any("missing artifact" in error for error in errors)
