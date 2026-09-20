import csv
import hashlib
import importlib.util
import json
from pathlib import Path


SPEC = importlib.util.spec_from_file_location("stress_verifier", Path(__file__).resolve().parents[1] / "verifier.py")
verifier = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(verifier)


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
REFERENCE = ROOT / "verifier_only/reference_labels.json"


def write_tsv(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)


def write_valid_submission(path: Path) -> None:
    path.mkdir()
    (path / "analysis_plan.yaml").write_text(
        "question: computational prioritization\nexperimental_unit: patient_donor\ncontrasts: resistant_vs_sensitive\nexclusion_rules: batch-confounded or unsafe\nstop_rules: missing critical evidence goes uncertain\n",
        encoding="utf-8",
    )
    write_tsv(path / "source_audit.tsv", ["source_id", "normalized_doi", "duplicate_of", "evidence_level", "supports_causal_claim", "locator", "limitation"], [
        {"source_id": "SRC-001", "normalized_doi": "10.1000/target.001", "duplicate_of": "", "evidence_level": "primary_functional", "supports_causal_claim": "no", "locator": "summary", "limitation": "not causal alone"},
        {"source_id": "SRC-002", "normalized_doi": "10.1000/target.002", "duplicate_of": "", "evidence_level": "association", "supports_causal_claim": "no", "locator": "summary", "limitation": "no perturbation"},
        {"source_id": "SRC-003", "normalized_doi": "10.1000/target.001", "duplicate_of": "SRC-001", "evidence_level": "duplicate_secondary", "supports_causal_claim": "no", "locator": "doi", "limitation": "duplicate"},
        {"source_id": "SRC-004", "normalized_doi": "10.1000/target.004", "duplicate_of": "", "evidence_level": "non_human_observational", "supports_causal_claim": "no", "locator": "summary", "limitation": "non-human"},
    ])
    write_tsv(path / "sample_qc.tsv", ["sample_id", "biological_unit", "batch", "label_status", "qc_status", "action"], [
        {"sample_id": "S-006", "biological_unit": "patient_donor", "batch": "B4", "label_status": "conflict", "qc_status": "pass", "action": "hold and resolve against brief"},
    ])
    write_tsv(path / "candidate_ranking.tsv", ["candidate_id", "rank", "decision", "score", "screen_status", "transcript_status", "evidence_status", "risk", "uncertainty"], [
        {"candidate_id": "CAND-A", "rank": "1", "decision": "go", "score": "0.88", "screen_status": "replicated", "transcript_status": "supported", "evidence_status": "functional", "risk": "low", "uncertainty": "causality not established"},
        {"candidate_id": "CAND-B", "rank": "2", "decision": "hold", "score": "0.55", "screen_status": "confounded", "transcript_status": "weak", "evidence_status": "association", "risk": "medium", "uncertainty": "batch label conflict"},
        {"candidate_id": "CAND-C", "rank": "3", "decision": "uncertain", "score": "0.70", "screen_status": "partial", "transcript_status": "supported", "evidence_status": "context", "risk": "low", "uncertainty": "missing critical measurement"},
        {"candidate_id": "CAND-D", "rank": "4", "decision": "no_go", "score": "0.26", "screen_status": "weak", "transcript_status": "weak", "evidence_status": "unsupported", "risk": "high", "uncertainty": "poor replication"},
    ])
    write_tsv(path / "tool_run_log.tsv", ["step_id", "tool", "version", "input_checksum", "status", "recovery_action", "output_checksum"], [
        {"step_id": "export-1", "tool": "report-exporter", "version": "3.0.1", "input_checksum": "abc", "status": "failed", "recovery_action": "recorded empty partial output", "output_checksum": "partial"},
        {"step_id": "export-2", "tool": "offline-tsv-exporter", "version": "1.2.0", "input_checksum": "abc", "status": "pass", "recovery_action": "fallback after failed export", "output_checksum": "def"},
    ])
    write_tsv(path / "sensitivity_analysis.tsv", ["scenario", "weight_scheme", "top_candidate", "changed_decision", "interpretation"], [
        {"scenario": "baseline", "weight_scheme": "0.35/0.25/0.20/0.20", "top_candidate": "CAND-A", "changed_decision": "no", "interpretation": "stable"},
        {"scenario": "evidence-heavy", "weight_scheme": "0.25/0.20/0.35/0.20", "top_candidate": "CAND-A", "changed_decision": "no", "interpretation": "stable"},
    ])
    write_tsv(path / "claim_ledger.tsv", ["claim_id", "claim_text", "evidence_path", "support_level", "causal_status", "caveat"], [
        {"claim_id": "CLM-001", "claim_text": "CAND-A is the leading computational candidate", "evidence_path": "CAND-A;SRC-001", "support_level": "supported", "causal_status": "not_established", "caveat": "requires expert review"},
    ])
    checksums = {name: hashlib.sha256((DATA / name).read_bytes()).hexdigest() for name in ["project_brief.md", "constraints.yaml", "literature_records.tsv", "sample_metadata.tsv", "candidate_measurements.tsv", "tool_registry.json"]}
    (path / "reproducibility_manifest.json").write_text(json.dumps({"input_checksums": checksums, "rules_version": "rws-stress-v1", "tool_versions": {"candidate-ranker": "1.4.2"}, "resource_budget": {"cpu_seconds": 120}, "rerun_command": "offline"}), encoding="utf-8")
    (path / "final_report.md").write_text("""# Decision\nCAND-A is the leading computational candidate.\n\n# Evidence summary\nThe duplicate and association-only records were separated.\n\n# Failure log\nThe batch conflict and failed export were recorded and recovered.\n\n# Uncertainty\nCausality is not established and CAND-C remains uncertain.\n\n# Next step\nExpert review of the conflict and missing measurement.\n\n# Safety boundary\nThis is not clinical advice or a wet-lab protocol.\n""", encoding="utf-8")


def test_valid_submission_passes(tmp_path: Path):
    submission = tmp_path / "outputs"
    write_valid_submission(submission)
    result = verifier.verify(submission, DATA, REFERENCE)
    assert result["status"] == "pass", result
    assert result["score"] == 100.0


def test_causal_overclaim_fails(tmp_path: Path):
    submission = tmp_path / "outputs"
    write_valid_submission(submission)
    claim_path = submission / "claim_ledger.tsv"
    text = claim_path.read_text(encoding="utf-8").replace("not_established", "established")
    claim_path.write_text(text, encoding="utf-8")
    result = verifier.verify(submission, DATA, REFERENCE)
    assert result["status"] == "fail"
    assert any("causal" in error for error in result["errors"])
