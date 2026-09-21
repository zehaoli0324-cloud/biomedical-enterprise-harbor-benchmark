import csv
import importlib.util
import json
import tomllib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load(task_id):
    path = ROOT / "benchmarks" / task_id / "verifier.py"
    spec = importlib.util.spec_from_file_location(task_id, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, ROOT / "benchmarks" / task_id


def test_eb003_reference_shape_passes(tmp_path):
    verifier, root = load("eb003-failure-recovery-003")
    exp = verifier.expected(root / "data")
    events = []
    for branch, decision in exp["decisions"].items():
        events.append(json.dumps({"branch": branch, "status": decision["status"], "failed_invariants": decision["failed_invariants"]}))
    (tmp_path / "execution_log.jsonl").write_text("\n".join(events) + "\n", encoding="utf-8")
    (tmp_path / "failure_recovery.md").write_text("Partial output was preserved. retry_parallel retains the question; reference, cohort, estimand, provenance and scope drift are classified. Pilot and archived scope are excluded. Human review remains and no causal result is claimed.\n", encoding="utf-8")
    (tmp_path / "claim_ledger.tsv").write_text("claim\tstatus\tevidence\tblocker\treview_boundary\nrecovery\tsupported\tretry_parallel\t\tnot causal\n", encoding="utf-8")
    (tmp_path / "run_manifest.json").write_text(json.dumps({"input_sha256": exp["hashes"], "rules_version": exp["rules_version"], "deterministic": True}), encoding="utf-8")
    ok, errors = verifier.verify(tmp_path, root / "data", root / "verifier_only/reference.json")
    assert ok, errors


def test_eb005_reference_shape_passes(tmp_path):
    verifier, root = load("eb005-batch-normalization-002")
    exp = verifier.expected(root / "data")
    joined = [{**row, "qc_pass": str(row["qc_pass"]).lower()} for row in exp["joined_rows"]]
    fields = list(joined[0])
    (tmp_path / "normalization_comparison.tsv").write_text("\t".join(fields) + "\n" + "\n".join("\t".join(str(row[field]) for field in fields) for row in joined) + "\n", encoding="utf-8")
    profile_metrics = {name: {key: values[key] for key in ("control_batch_range", "effect_retention_fraction", "direction_preserved", "blocker_reasons", "eligible")} for name, values in exp["profiles"].items()}
    report = {"recommended_profile": exp["recommended"], "evidence_complete": exp["evidence_complete"], "cell_counts": exp["cell_counts"], "excluded_plates": exp["excluded_plates"], "profiles": profile_metrics}
    (tmp_path / "batch_report.json").write_text(json.dumps(report), encoding="utf-8")
    (tmp_path / "sensitivity_summary.md").write_text("Pilot and archived scope exclusions are preserved. Batch identifiability depends on control evidence and phenotype effect retention; global adjustment has a direction reversal and aggressive normalization risks over-correction and erasing signal. This descriptive analysis has limitations.\n", encoding="utf-8")
    (tmp_path / "run_manifest.json").write_text(json.dumps({"input_sha256": exp["hashes"], "rules_version": exp["rules_version"], "deterministic": True}), encoding="utf-8")
    ok, errors = verifier.verify(tmp_path, root / "data", root / "verifier_only/reference.json")
    assert ok, errors


def test_eb008_reference_shape_passes(tmp_path):
    verifier, root = load("eb008-stock-route-001")
    exp = verifier.expected(root / "data")
    fields = ["route_id", "target", "score", "usable_stock", "stock_ok", "evidence_quorum", "reaction_valid", "failed_gates", "accepted"]
    lines = ["\t".join(fields)]
    for row in exp["routes"]:
        lines.append("\t".join([
            row["route_id"], row["target"], str(row["score"]),
            json.dumps({key: value["usable"] for key, value in row["material_status"].items()}, sort_keys=True),
            str(row["stock_ok"]).lower(), json.dumps(row["evidence_quorum"], sort_keys=True),
            str(row["reaction_valid"]).lower(), ",".join(row["failed_gates"]), str(row["accepted"]).lower(),
        ]))
    (tmp_path / "route_table.tsv").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (tmp_path / "stock_compliance.json").write_text(json.dumps({"usable_stock": exp["usable_stock"], "selected_route_ids": exp["accepted_routes"], "routes": exp["routes"]}), encoding="utf-8")
    evidence = [{"route_id": row["route_id"], "step": row["step"], "source_id": row["source_id"], "source_status": row["source_status"], "independence_group": row["source_independence_group"], "included": str(row["included"]).lower()} for row in exp["joined_evidence"]]
    fields = list(evidence[0])
    (tmp_path / "route_evidence.tsv").write_text("\t".join(fields) + "\n" + "\n".join("\t".join(str(row[field]).lower() for field in fields) for row in evidence) + "\n", encoding="utf-8")
    (tmp_path / "approval_gate.md").write_text("Human chemist review of the evidence-source join, precedent, chemoselectivity, stereochemistry and protection evidence is required; computational selection is not experimental proof. Retracted and wrong-target sources are excluded.\n", encoding="utf-8")
    ok, errors = verifier.verify(tmp_path, root / "data", root / "verifier_only/reference.json")
    assert ok, errors


def test_eb008_documented_equivalent_route_fields_pass(tmp_path):
    verifier, root = load("eb008-stock-route-001")
    exp = verifier.expected(root / "data")
    gate_text = {
        "R-A": "none",
        "R-B": "stock availability (M-9 unavailable)",
        "R-C": "precedent scope; chemoselectivity; protection strategy",
        "R-D": "stereochemistry unresolved",
    }
    validity = {row["route_id"]: "valid under supplied rules" if row["reaction_valid"] else "invalid under supplied rules" for row in exp["routes"]}
    (tmp_path / "route_table.tsv").write_text(
        "route_id\tusable_stock\tstock_ok\tevidence_quorum\treaction_valid\tfailed_gates\taccepted\n"
        + "\n".join(
            f"{row['route_id']}\t{{}}\t{str(row['stock_ok']).lower()}\t{json.dumps(row['evidence_quorum'], sort_keys=True)}\t{str(row['reaction_valid']).lower()}\t{gate_text[row['route_id']]}\t{str(row['accepted']).lower()}"
            for row in exp["routes"]
        )
        + "\n",
        encoding="utf-8",
    )
    routes = [
        {"route_id": row["route_id"], "stock_available": row["stock_ok"], "accepted": row["accepted"]}
        for row in exp["routes"]
    ]
    (tmp_path / "stock_compliance.json").write_text(json.dumps({"usable_stock": exp["usable_stock"], "selected_route_ids": exp["accepted_routes"], "routes": routes}), encoding="utf-8")
    evidence = [{"route_id": row["route_id"], "step": row["step"], "source_id": row["source_id"], "source_status": row["source_status"], "independence_group": row["source_independence_group"], "included": str(row["included"]).lower()} for row in exp["joined_evidence"]]
    fields = list(evidence[0])
    (tmp_path / "route_evidence.tsv").write_text("\t".join(fields) + "\n" + "\n".join("\t".join(str(row[field]).lower() for field in fields) for row in evidence) + "\n", encoding="utf-8")
    (tmp_path / "approval_gate.md").write_text("Human chemist review of precedent and stereochemistry is required; computational selection is not experimental proof.\n", encoding="utf-8")
    ok, errors = verifier.verify(tmp_path, root / "data", root / "verifier_only/reference.json")
    assert ok, errors


def test_eb010_reference_shape_passes(tmp_path):
    verifier, root = load("eb010-next-batch-001")
    exp = verifier.expected(root / "data")
    candidates = {row["candidate_id"]: row for row in csv.DictReader((root / "data/candidates.csv").open())}
    fields = ["candidate_id", "scope", "group", "material_cost", "predicted_gain", "uncertainty", "failure_probability", "candidate_utility"]
    lines = [",".join(fields)]
    nominal = exp["best_batch"]["candidate_utilities"]["nominal"]
    for candidate_id in exp["reference_batch"]:
        row = candidates[candidate_id]
        lines.append(",".join(str(row.get(field, nominal.get(candidate_id))) for field in fields))
    (tmp_path / "next_batch.csv").write_text("\n".join(lines) + "\n", encoding="utf-8")
    best = exp["best_batch"]
    (tmp_path / "constraint_check.json").write_text(json.dumps({"legal": True, "material_cost": exp["material_cost"], "group_coverage": best["groups"], "incompatible_pairs": best["incompatible_pairs"], "scenario_utilities": best["scenario_utilities"], "robust_batch_utility": best["robust_batch_utility"], "rules_version": exp["rules_version"]}), encoding="utf-8")
    (tmp_path / "uncertainty_table.tsv").write_text("candidate_id\tscope\tuncertainty\tselected\n" + "\n".join(f"{candidate}\t{candidates[candidate]['scope']}\t{candidates[candidate]['uncertainty']}\t{str(candidate in exp['reference_batch']).lower()}" for candidate in exp["candidate_ids"]) + "\n", encoding="utf-8")
    (tmp_path / "selection_rationale.md").write_text("The robust scenario planning recommendation balances exploration uncertainty, exploitation, failure risk, correlation redundancy and budget feasibility; it is not an experimental result.\n", encoding="utf-8")
    ok, errors = verifier.verify(tmp_path, root / "data", root / "verifier_only/reference.json")
    assert ok, errors


def test_scientific_difficulty_modules_match_compiled_contracts():
    expected = {
        "eb003-failure-recovery-003": ({"judgment_claim_preserving_recovery", "compute_failure_recovery", "tool_version_and_interface_drift"}, "advanced"),
        "eb005-batch-normalization-002": ({"judgment_batch_identifiability", "math_hierarchical_batch_sensitivity", "complexity_replicates_and_batches"}, "advanced"),
        "eb008-stock-route-001": ({"judgment_route_feasibility", "judgment_evidence_quality", "safety_human_approval_gate"}, "advanced"),
        "eb010-next-batch-001": ({"judgment_value_of_information", "math_batch_acquisition_under_uncertainty", "horizon_branching_experiments"}, "advanced"),
    }
    report = json.loads((ROOT / "candidate_pools/enterprise-v1/contracts/batch_compile_report.json").read_text())
    records = {row["task_id"]: row for row in report["tasks"]}
    for task_id, (primary_modules, band) in expected.items():
        card = json.loads((ROOT / "benchmarks" / task_id / "quality/difficulty_card.json").read_text())
        with (ROOT / "candidate_pools/enterprise-v1/contracts" / f"{task_id}.toml").open("rb") as handle:
            contract = tomllib.load(handle)
        selected_modules = {module for values in contract["modules"].values() for module in values}
        assert set(card["matched_modules"]["primary"]) <= selected_modules
        assert records[task_id]["band"] == band
        assert records[task_id]["control_calibration_status"] == "CALIBRATED"
        assert records[task_id]["model_trial_status"] == "TARGET_TRIAL_COMPLETE"
        assert card["difficulty_hypothesis"]["difficulty_boundary"]
