import csv
import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("ambiguity_verifier", ROOT / "verifier.py")
verifier = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(verifier)


def test_expected_is_deterministic():
    assert verifier.expected(ROOT / "data") == verifier.expected(ROOT / "data")


def test_expanded_fixture_covers_decision_boundaries():
    expected = verifier.expected(ROOT / "data")
    assert expected["selected_record"] == "P-OMICRON"
    assert expected["records"]["P-NU"]["eligible"] is True
    assert expected["records"]["P-NU"]["utility_range"] == 0.2
    assert expected["records"]["P-XI"]["blocker_reasons"] == ["budget"]
    assert expected["records"]["P-PI"]["blocker_reasons"] == ["semantic_ambiguity"]
    assert expected["records"]["P-RHO"]["blocker_reasons"] == ["uncertainty"]
    assert expected["records"]["P-SIGMA"]["blocker_reasons"] == ["signal_threshold"]
    assert expected["records"]["P-UPSILON"]["blocker_reasons"] == ["replay_stability"]
    assert expected["records"]["P-PHI"]["blocker_reasons"] == ["scope"]


def test_reference_shape_passes(tmp_path):
    exp = verifier.expected(ROOT / "data")
    (tmp_path / "plan.json").write_text(json.dumps({"operations": ["inventory", "interpret", "screen", "replay", "decide"], "total_cost": 6.5, "network_used": False, "stop_condition": "eligible_record_selected"}))
    (tmp_path / "decision.json").write_text(json.dumps({
        "selected_record": exp["selected_record"],
        "rules_version": exp["rules_version"],
        "claim_boundary": "planning_only_not_experimental_proof",
        "human_review_required": True,
        "records": exp["records"],
    }))
    fields = ["record_id", "semantic_status", "eligible", "blocker_reasons"]
    with (tmp_path / "evidence.tsv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, delimiter="\t")
        writer.writeheader()
        for record_id, row in exp["records"].items():
            writer.writerow({"record_id": record_id, "semantic_status": row["semantic_status"], "eligible": str(row["eligible"]).lower(), "blocker_reasons": ",".join(row["blocker_reasons"])})
    (tmp_path / "discovery.json").write_text(json.dumps({"discovered_files": exp["discovered_files"], "input_hashes": exp["hashes"], "network": "off", "deterministic": True}))
    (tmp_path / "audit.md").write_text("The plan uses a dependency-ordered workflow and stops after selecting. Ambiguous language triggers human review. Scope, future outcome, stability and budget were checked. This is not experimental proof.")
    ok, errors = verifier.verify(tmp_path, ROOT / "data", ROOT / "verifier_only/reference.json")
    assert ok, errors


def test_missing_submission_fails(tmp_path):
    ok, errors = verifier.verify(tmp_path, ROOT / "data", ROOT / "verifier_only/reference.json")
    assert not ok and errors


def test_incomplete_shortcut_plan_fails(tmp_path):
    exp = verifier.expected(ROOT / "data")
    (tmp_path / "plan.json").write_text(json.dumps({"operations": ["inventory", "label_scan", "top_only_replay"], "total_cost": 2.0, "network_used": False, "stop_condition": "eligible_record_selected"}))
    (tmp_path / "decision.json").write_text(json.dumps({"selected_record": exp["selected_record"], "rules_version": exp["rules_version"], "claim_boundary": "planning_only_not_experimental_proof", "human_review_required": True, "records": exp["records"]}))
    (tmp_path / "evidence.tsv").write_text("record_id\tsemantic_status\teligible\tblocker_reasons\n")
    (tmp_path / "discovery.json").write_text(json.dumps({"discovered_files": exp["discovered_files"], "input_hashes": exp["hashes"], "network": exp["network"], "deterministic": True}))
    (tmp_path / "audit.md").write_text("plan workflow ambiguity scope future stability human review not experimental proof")
    ok, errors = verifier.verify(tmp_path, ROOT / "data", ROOT / "verifier_only/reference.json")
    assert not ok and any("capabilities" in error for error in errors)


def test_instruction_declares_machine_checked_output_contract():
    text = (ROOT / "instruction.md").read_text()
    for term in (
        "selected_record` as the selected record ID string",
        "records` as an object keyed by every record ID",
        "semantic_status",
        "blocker_reasons",
        "discovered_files",
        "input_hashes",
        "not experimental proof",
    ):
        assert term in text


def test_equivalent_status_and_blocker_encoding_passes(tmp_path):
    exp = verifier.expected(ROOT / "data")
    (tmp_path / "plan.json").write_text(json.dumps({"operations": [{"operation_id": "inventory"}, {"operation_id": "interpret"}, {"operation_id": "screen"}, {"operation_id": "replay"}, {"operation_id": "decide"}], "total_cost": 6.5, "network_used": False, "stop_condition": "eligible_record_selected"}))
    records = json.loads(json.dumps(exp["records"]))
    records["P-GAMMA"]["blocker_reasons"].remove("semantic_ambiguity")
    records["P-DELTA"]["semantic_status"] = "unresolved"
    records["P-ARCHIVE"]["semantic_status"] = "unresolved"
    (tmp_path / "decision.json").write_text(json.dumps({
        "selected_record": exp["selected_record"],
        "rules_version": exp["rules_version"],
        "claim_boundary": "planning_only_not_experimental_proof",
        "human_review_required": True,
        "records": records,
    }))
    fields = ["record_id", "semantic_status", "utility", "utility_range", "replay_count", "eligible", "blocker_reasons"]
    with (tmp_path / "evidence.tsv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, delimiter="\t")
        writer.writeheader()
        for record_id, row in records.items():
            writer.writerow({"record_id": record_id, **row, "eligible": str(row["eligible"]).lower(), "blocker_reasons": ";".join(row["blocker_reasons"])})
    (tmp_path / "discovery.json").write_text(json.dumps({"discovered_files": exp["discovered_files"], "input_hashes": exp["hashes"], "network": exp["network"], "deterministic": True}))
    (tmp_path / "audit.md").write_text("The plan and operation workflow stop after selection. Ambiguity, scope and future outcomes are recorded. Replays are stable and require human review. This is not experimental proof.")
    ok, errors = verifier.verify(tmp_path, ROOT / "data", ROOT / "verifier_only/reference.json")
    assert ok, errors
