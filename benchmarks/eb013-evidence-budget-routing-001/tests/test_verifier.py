import csv
import importlib.util
import json
from pathlib import Path


TASK = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("eb013_verifier", TASK / "verifier.py")
VERIFIER = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(VERIFIER)


def _write_json(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def write_reference(out: Path) -> dict:
    exp = VERIFIER.expected(TASK / "data")
    out.mkdir(parents=True, exist_ok=True)
    _write_json(out / "plan.json", {
        "selected_request_ids": exp["selected_request_ids"],
        "total_cost": exp["route_cost"],
        "network_used": False,
        "stop_condition": exp["stop_condition"],
    })
    _write_json(out / "decision.json", {
        "decision": exp["decision"],
        "selected_request_ids": exp["selected_request_ids"],
        "route_cost": exp["route_cost"],
        "residual_uncertainty": exp["residual_uncertainty"],
        "max_critical_residual": exp["max_critical_residual"],
        "human_review_required": exp["human_review_required"],
    })
    with (out / "route.tsv").open("w", newline="", encoding="utf-8") as handle:
        fields = ["request_id", "status", "included", "blockers", "effective_reductions", "route_position"]
        writer = csv.DictWriter(handle, fields, delimiter="\t")
        writer.writeheader()
        for request_id, row in exp["request_rows"].items():
            writer.writerow({
                "request_id": request_id,
                "status": row["status"],
                "included": str(row["included"]).lower(),
                "blockers": ";".join(row["blockers"]),
                "effective_reductions": json.dumps(row["effective_reductions"], sort_keys=True),
                "route_position": row["route_position"] or "",
            })
    _write_json(out / "provenance.json", {
        "input_sha256": exp["hashes"],
        "rules_version": exp["rules_version"],
        "network": exp["network"],
        "deterministic": True,
    })
    (out / "audit.md").write_text(
        "Critical uncertainty is the bottleneck. Dependency and prerequisite gates are enforced. "
        "Correlation prevents correlated reductions from being added. Future post-decision evidence is excluded. "
        "The budget and cost are bounded, and the stop condition is route selected. This is not experimental proof.\n",
        encoding="utf-8",
    )
    return exp


def test_expected_is_deterministic_and_matches_reference() -> None:
    first = VERIFIER.expected(TASK / "data")
    second = VERIFIER.expected(TASK / "data")
    reference = json.loads((TASK / "verifier_only/reference.json").read_text())
    assert first == second
    assert first["selected_request_ids"] == ["R-ASSAY", "R-ORTHO"]
    assert reference["selected_request_ids"] == first["selected_request_ids"]


def test_reference_submission_passes(tmp_path: Path) -> None:
    write_reference(tmp_path)
    passed, errors = VERIFIER.verify(tmp_path, TASK / "data", TASK / "verifier_only/reference.json")
    assert passed, errors


def test_missing_artifacts_fail(tmp_path: Path) -> None:
    passed, errors = VERIFIER.verify(tmp_path, TASK / "data", TASK / "verifier_only/reference.json")
    assert not passed
    assert len(errors) == 5


def test_correlated_shortcut_route_fails(tmp_path: Path) -> None:
    write_reference(tmp_path)
    decision = json.loads((tmp_path / "decision.json").read_text())
    decision["selected_request_ids"] = ["R-CHEM", "R-CORR"]
    _write_json(tmp_path / "decision.json", decision)
    passed, errors = VERIFIER.verify(tmp_path, TASK / "data", TASK / "verifier_only/reference.json")
    assert not passed
    assert "decision selected request mismatch" in errors


def test_provenance_hash_mutation_fails(tmp_path: Path) -> None:
    write_reference(tmp_path)
    provenance = json.loads((tmp_path / "provenance.json").read_text())
    provenance["input_sha256"].pop("rules.json")
    _write_json(tmp_path / "provenance.json", provenance)
    passed, errors = VERIFIER.verify(tmp_path, TASK / "data", TASK / "verifier_only/reference.json")
    assert not passed
    assert "provenance mismatch" in errors


def test_documented_aliases_and_explanatory_blockers_pass(tmp_path: Path) -> None:
    exp = write_reference(tmp_path)
    decision = json.loads((tmp_path / "decision.json").read_text())
    decision["decision"] = "route_selected"
    decision["residual_uncertainty_map"] = decision.pop("residual_uncertainty")
    decision["objective_values"] = {"maximum_critical_residual": decision.pop("max_critical_residual")}
    _write_json(tmp_path / "decision.json", decision)
    provenance = json.loads((tmp_path / "provenance.json").read_text())
    provenance["sha256"] = {"data/" + key: value for key, value in provenance.pop("input_sha256").items()}
    provenance["network_state"] = provenance.pop("network")
    _write_json(tmp_path / "provenance.json", provenance)
    rows = list(csv.DictReader((tmp_path / "route.tsv").open(), delimiter="\t"))
    with (tmp_path / "route.tsv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, rows[0].keys(), delimiter="\t"); writer.writeheader()
        for row in rows:
            if row["request_id"] == "R-ASSAY":
                row["blockers"] = "none"
            elif not exp["request_rows"][row["request_id"]]["included"]:
                row["effective_reductions"] = "{}"
                row["blockers"] = ";".join(filter(None, [row["blockers"], "not_selected"]))
            writer.writerow(row)
    passed, errors = VERIFIER.verify(tmp_path, TASK / "data", TASK / "verifier_only/reference.json")
    assert passed, errors
