import csv
import hashlib
import json
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
REFERENCE = ROOT / "verifier_only/reference_labels.json"
sys.path.insert(0, str(ROOT))

from verifier import verify


def write_tsv(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)


def write_valid_submission(path: Path) -> None:
    path.mkdir()
    decisions = [
        {"record_id": "LIT-001", "decision": "include", "reason_code": "primary_human_direct_resistance", "confidence": "0.95", "evidence_locator": "abstract:sentences-1-2"},
        {"record_id": "LIT-002", "decision": "exclude", "reason_code": "secondary_review", "confidence": "0.99", "evidence_locator": "abstract:sentence-1"},
        {"record_id": "LIT-003", "decision": "context_only", "reason_code": "association_without_perturbation", "confidence": "0.9", "evidence_locator": "abstract:sentences-1-2"},
        {"record_id": "LIT-004", "decision": "exclude", "reason_code": "non_human_model", "confidence": "0.99", "evidence_locator": "abstract:sentences-1-2"},
        {"record_id": "LIT-005", "decision": "exclude", "reason_code": "duplicate_normalized_doi", "confidence": "0.95", "evidence_locator": "doi:10.1000/resistance.001"},
        {"record_id": "LIT-006", "decision": "exclude", "reason_code": "wrong_outcome_sensitivity", "confidence": "0.99", "evidence_locator": "abstract:sentences-1-2"},
        {"record_id": "LIT-007", "decision": "uncertain", "reason_code": "insufficient_metadata_full_text_unavailable", "confidence": "0.95", "evidence_locator": "abstract:sentence-1"},
        {"record_id": "LIT-008", "decision": "include", "reason_code": "primary_human_functional_resistance", "confidence": "0.9", "evidence_locator": "abstract:sentences-1-2"},
    ]
    write_tsv(path / "screening_decisions.tsv", list(decisions[0]), decisions)
    write_tsv(
        path / "evidence_table.tsv",
        ["claim_id", "source_id", "evidence_type", "support_status", "locator", "limitation"],
        [
            {"claim_id": "CLM-001", "source_id": "LIT-001", "evidence_type": "primary_direct", "support_status": "supported_for_functional_observation", "locator": "abstract:sentences-1-2", "limitation": "abstract snapshot does not establish complete mechanism"},
            {"claim_id": "CLM-002", "source_id": "LIT-003", "evidence_type": "association", "support_status": "context_only_not_causal", "locator": "abstract:sentences-1-2", "limitation": "no perturbation or causal test"},
            {"claim_id": "CLM-003", "source_id": "LIT-008", "evidence_type": "primary_functional", "support_status": "supported_for_functional_observation", "locator": "abstract:sentences-1-2", "limitation": "does not establish complete mechanism"},
        ],
    )
    write_tsv(
        path / "uncertainty_queue.tsv",
        ["record_id", "uncertainty_reason", "minimum_next_check"],
        [{"record_id": "LIT-007", "uncertainty_reason": "model, drug, and outcome are not established", "minimum_next_check": "retrieve and inspect the full text and methods"}],
    )
    input_sha = hashlib.sha256((DATA / "literature_records.tsv").read_bytes()).hexdigest()
    (path / "run_manifest.json").write_text(json.dumps({"input_sha256": input_sha, "rules_version": "m1-literature-screening-v1", "tool_version": "calibration-verifier-0.1"}), encoding="utf-8")
    (path / "final_report.md").write_text("""# Screening Report\n\n# Screening summary\nEight records were screened under the frozen rules.\n\n# Evidence boundary\nThe included records support functional or association-level observations, not a causal mechanism claim.\n\n# Uncertainty\nLIT-007 remains uncertain because the available metadata and abstract are insufficient.\n\n# Next step\nRetrieve the missing full text and perform expert adjudication before causal synthesis.\n""", encoding="utf-8")


def test_valid_submission_passes(tmp_path: Path):
    submission = tmp_path / "outputs"
    write_valid_submission(submission)
    result = verify(submission, DATA, REFERENCE)
    assert result["status"] == "pass"
    assert result["score"] == 100.0


def test_wrong_decision_fails(tmp_path: Path):
    submission = tmp_path / "outputs"
    write_valid_submission(submission)
    decision_file = submission / "screening_decisions.tsv"
    text = decision_file.read_text(encoding="utf-8").replace("LIT-003\tcontext_only", "LIT-003\tinclude")
    decision_file.write_text(text, encoding="utf-8")
    result = verify(submission, DATA, REFERENCE)
    assert result["status"] == "fail"
    assert result["metrics"]["decision_accuracy"] < 1


def test_publicly_allowed_reason_alias_passes(tmp_path: Path):
    submission = tmp_path / "outputs"
    write_valid_submission(submission)
    decision_file = submission / "screening_decisions.tsv"
    text = decision_file.read_text(encoding="utf-8").replace(
        "LIT-001\tinclude\tprimary_human_direct_resistance",
        "LIT-001\tinclude\tprimary_human_functional_resistance",
    )
    decision_file.write_text(text, encoding="utf-8")
    result = verify(submission, DATA, REFERENCE)
    assert result["status"] == "pass"


@pytest.mark.parametrize("field", ["input_sha256", "rules_version"])
def test_manifest_is_required(tmp_path: Path, field: str):
    submission = tmp_path / "outputs"
    write_valid_submission(submission)
    manifest = json.loads((submission / "run_manifest.json").read_text(encoding="utf-8"))
    manifest[field] = "wrong"
    (submission / "run_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    result = verify(submission, DATA, REFERENCE)
    assert result["status"] == "fail"
