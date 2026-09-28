import json
from pathlib import Path

from scripts.audit_real_source_gate import audit


ROOT = Path(__file__).resolve().parents[2]
TASK = ROOT / "benchmarks/eb015-real-source-replacement-gate-001"


def test_metadata_only_source_card_stays_release_blocked():
    report = audit(TASK)
    assert report["release_status"] == "STAGING_BLOCKED"
    assert report["blocked_sources"] == [
        "SRC-CRISPR-PMC7006212",
        "SRC-BBBC021-V1",
        "SRC-ZENODO-10362368",
    ]
    assert report["claim_boundary"] == "source_audit_only_not_scientific_claim"
    assert report["network_used"] is False


def test_source_audit_is_deterministic():
    first = audit(TASK)
    second = audit(TASK)
    assert json.dumps(first, sort_keys=True) == json.dumps(second, sort_keys=True)
