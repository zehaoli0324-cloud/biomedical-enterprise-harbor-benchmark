#!/usr/bin/env python3
"""Run author-side baseline submissions without exposing hidden truth to agents."""

from __future__ import annotations

import csv
import importlib.util
import json
import shutil
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
STRATEGIES = ("reference_solution", "simple_legal_baseline", "always_abstain", "template_or_keyword")
SCIENTIFIC_JUDGMENT_TASKS = {
    "eb003-failure-recovery-003",
    "eb005-batch-normalization-002",
    "eb008-stock-route-001",
    "eb010-next-batch-001",
}


def load_verifier(task_id: str):
    path = ROOT / "benchmarks" / task_id / "verifier.py"
    spec = importlib.util.spec_from_file_location(f"{task_id}_baseline_verifier", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load verifier: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, str]], delimiter: str = ",") -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, delimiter=delimiter)
        writer.writeheader()
        writer.writerows(rows)


def write_eb001_reference(verifier, data: Path, output: Path) -> None:
    exp = verifier.expected(data)
    output.mkdir(parents=True, exist_ok=True)
    report = {key: exp[key] for key in ("summary", "canonical_overlap", "scaffold_overlap", "identity_notes", "missing_measurements", "hashes", "rules_version")}
    report.update({"schema_version": "1.0", "input_sha256": exp["hashes"], "readiness": {"decision": "blocked", "reason": "canonical or scaffold overlap"}})
    (output / "split_audit.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    write_csv(output / "structure_identity.tsv", ["compound_id", "canonical_smiles", "scaffold_id", "split", "identity_class", "evidence"], [
        {"compound_id": row["compound_id"], "canonical_smiles": row["canonical_smiles"], "scaffold_id": row["scaffold_id"], "split": row["split"], "identity_class": row["identity_note"], "evidence": "compounds.csv+split_rules.json"}
        for row in verifier.read_csv(data / "compounds.csv")
    ], delimiter="\t")
    (output / "readiness_report.md").write_text("# Enterprise validation\n\nCanonical and scaffold overlap are present; salt identity and missing measurements are preserved. Synthetic fixture; block model comparison.\n", encoding="utf-8")
    (output / "run_manifest.json").write_text(json.dumps({"input_sha256": exp["hashes"], "rules_version": exp["rules_version"], "tool_version": "baseline-reference-v1", "deterministic": True}, indent=2) + "\n", encoding="utf-8")


def write_eb004_reference(verifier, data: Path, output: Path) -> None:
    exp = verifier.expected(data)
    output.mkdir(parents=True, exist_ok=True)
    write_csv(output / "adtte.csv", verifier.FIELDS, exp["rows"])
    trace_fields = ["USUBJID", "source_record", "event_type", "raw_date", "date_precision", "rule_id", "selected_value"]
    write_csv(output / "event_trace.csv", trace_fields, exp["trace"])
    report = {"schema_version": "1.0", "input_sha256": exp["hashes"], "rules_version": exp["rules_version"], "summary": exp["summary"], "edge_cases": exp["edge_cases"], "handoff": {"decision": "hold_for_review"}, "claim_boundary": "Synthetic fixture; not sponsor data and not efficacy evidence."}
    (output / "censoring_audit.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    (output / "run_manifest.json").write_text(json.dumps({"input_sha256": exp["hashes"], "rules_version": exp["rules_version"], "tool_version": "baseline-reference-v1", "deterministic": True}, indent=2) + "\n", encoding="utf-8")


def write_eb003_reference(verifier, data: Path, output: Path) -> None:
    exp = verifier.expected(data)
    output.mkdir(parents=True, exist_ok=True)
    events = []
    for branch, decision in exp["decisions"].items():
        events.append({"event": "branch_review", "branch": branch, "status": decision["status"], "failed_invariants": decision["failed_invariants"]})
    (output / "execution_log.jsonl").write_text("".join(json.dumps(row) + "\n" for row in events), encoding="utf-8")
    (output / "failure_recovery.md").write_text("# Recovery\n\nThe primary left partial output. The current-scope fallback is selected only after question, estimand, cohort, reference, version, digest, tool major version, and required provenance checks. Drifted branches, missing-digest branches, pilot and archived scope distractors are excluded. Human review is required and this is not a causal result.\n", encoding="utf-8")
    (output / "claim_ledger.tsv").write_text(f"claim\tstatus\tevidence\tblocker\treview_boundary\noperational recovery\tbounded\t{exp['selected_branch']}\t\tnot causal; human review\n", encoding="utf-8")
    (output / "run_manifest.json").write_text(json.dumps({"input_sha256": exp["hashes"], "rules_version": exp["rules_version"], "deterministic": True}, indent=2) + "\n", encoding="utf-8")


def write_eb005_reference(verifier, data: Path, output: Path) -> None:
    exp = verifier.expected(data)
    output.mkdir(parents=True, exist_ok=True)
    rows = [{**row, "qc_pass": str(row["qc_pass"]).lower()} for row in exp["joined_rows"]]
    write_csv(output / "normalization_comparison.tsv", list(rows[0]), rows, delimiter="\t")
    report = {"recommended": exp["recommended"], "evidence_complete": exp["evidence_complete"], "cell_counts": exp["cell_counts"], "excluded_plates": exp["excluded_plates"], "profiles": exp["profiles"]}
    (output / "batch_report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    (output / "sensitivity_summary.md").write_text("# Sensitivity\n\nPilot and archived scope exclusions are preserved after the metadata join. Batch identifiability uses control evidence and phenotype effect retention. The global branch has a direction reversal, while the aggressive branch is over-correction that erases phenotype signal. This descriptive analysis has limitations and does not confirm mechanism.\n", encoding="utf-8")
    (output / "run_manifest.json").write_text(json.dumps({"input_sha256": exp["hashes"], "rules_version": exp["rules_version"], "deterministic": True}, indent=2) + "\n", encoding="utf-8")


def write_eb008_reference(verifier, data: Path, output: Path) -> None:
    exp = verifier.expected(data)
    output.mkdir(parents=True, exist_ok=True)
    fields = ["route_id", "target", "score", "usable_stock", "stock_ok", "evidence_quorum", "reaction_valid", "failed_gates", "accepted"]
    rows = []
    for row in exp["routes"]:
        rows.append({
            "route_id": row["route_id"], "target": row["target"], "score": row["score"],
            "usable_stock": json.dumps({key: value["usable"] for key, value in row["material_status"].items()}, sort_keys=True),
            "stock_ok": str(row["stock_ok"]).lower(),
            "evidence_quorum": json.dumps(row["evidence_quorum"], sort_keys=True),
            "reaction_valid": str(row["reaction_valid"]).lower(),
            "failed_gates": ";".join(row["failed_gates"]),
            "accepted": str(row["accepted"]).lower(),
        })
    write_csv(output / "route_table.tsv", fields, rows, delimiter="\t")
    (output / "stock_compliance.json").write_text(json.dumps({"usable_stock": exp["usable_stock"], "routes": exp["routes"], "selected_route_ids": exp["accepted_routes"]}, indent=2) + "\n", encoding="utf-8")
    evidence = []
    for row in exp["joined_evidence"]:
        evidence.append({
            "route_id": row["route_id"], "step": row["step"], "source_id": row["source_id"],
            "source_status": row["source_status"], "independence_group": row["source_independence_group"],
            "included": str(row["included"]).lower(),
        })
    write_csv(output / "route_evidence.tsv", list(evidence[0]), evidence, delimiter="\t")
    (output / "approval_gate.md").write_text("# Approval gate\n\nHuman chemist review remains required. The evidence-source join excludes retracted or wrong-target records, and computational precedent, chemoselectivity, stereochemistry and protection evidence are not experimental laboratory proof.\n", encoding="utf-8")


def write_eb010_reference(verifier, data: Path, output: Path) -> None:
    exp = verifier.expected(data)
    output.mkdir(parents=True, exist_ok=True)
    candidates = {row["candidate_id"]: row for row in csv.DictReader((data / "candidates.csv").open())}
    fields = ["candidate_id", "scope", "group", "material_cost", "predicted_gain", "uncertainty", "failure_probability", "candidate_utility"]
    nominal = exp["best_batch"]["candidate_utilities"]["nominal"]
    rows = [{**candidates[candidate_id], "candidate_utility": nominal[candidate_id]} for candidate_id in exp["reference_batch"]]
    write_csv(output / "next_batch.csv", fields, rows)
    best = exp["best_batch"]
    (output / "constraint_check.json").write_text(json.dumps({"legal": True, "material_cost": best["material_cost"], "group_coverage": best["groups"], "incompatible_pairs": best["incompatible_pairs"], "scenario_utilities": best["scenario_utilities"], "robust_batch_utility": best["robust_batch_utility"], "rules_version": exp["rules_version"]}, indent=2) + "\n", encoding="utf-8")
    uncertainty = [{"candidate_id": candidate_id, "scope": row["scope"], "uncertainty": row["uncertainty"], "selected": str(candidate_id in exp["reference_batch"]).lower()} for candidate_id, row in candidates.items()]
    write_csv(output / "uncertainty_table.tsv", list(uncertainty[0]), uncertainty, delimiter="\t")
    (output / "selection_rationale.md").write_text("# Selection\n\nThe robust scenario recommendation maximizes the worst-case utility before weighted mean. It balances exploration and exploitation, failure risk, correlation redundancy and budget feasibility while excluding pilot and archived candidates. This is a planning recommendation, not an experimental result.\n", encoding="utf-8")


REFERENCE_WRITERS = {
    "eb001-split-leakage-001": write_eb001_reference,
    "eb004-adtte-censoring-002": write_eb004_reference,
    "eb003-failure-recovery-003": write_eb003_reference,
    "eb005-batch-normalization-002": write_eb005_reference,
    "eb008-stock-route-001": write_eb008_reference,
    "eb010-next-batch-001": write_eb010_reference,
}


def mutate_baseline(task_id: str, strategy: str, output: Path) -> None:
    if task_id == "eb003-failure-recovery-003":
        if strategy == "simple_legal_baseline":
            events = [json.loads(line) for line in (output / "execution_log.jsonl").read_text().splitlines()]
            for row in events:
                if row["branch"] == "retry_parallel": row["status"] = "rejected"
                if row["branch"] == "retry_reference_refresh": row["status"] = "selected"
            (output / "execution_log.jsonl").write_text("".join(json.dumps(row) + "\n" for row in events), encoding="utf-8")
        elif strategy == "always_abstain":
            shutil.rmtree(output)
            output.mkdir()
        elif strategy == "template_or_keyword":
            (output / "execution_log.jsonl").write_text('{"event":"done","branch":"primary","status":"failed"}\n', encoding="utf-8")
        return
    if task_id == "eb005-batch-normalization-002":
        if strategy == "simple_legal_baseline":
            report = json.loads((output / "batch_report.json").read_text())
            report["recommended"] = "aggressive_adjusted"
            (output / "batch_report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        elif strategy == "always_abstain":
            shutil.rmtree(output)
            output.mkdir()
        elif strategy == "template_or_keyword":
            report = json.loads((output / "batch_report.json").read_text())
            report["profiles"]["control_adjusted"]["effect_retention_fraction"] = 1.0
            (output / "batch_report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        return
    if task_id == "eb008-stock-route-001":
        if strategy == "simple_legal_baseline":
            report = json.loads((output / "stock_compliance.json").read_text())
            report["selected_route_ids"] = ["R-B"]
            (output / "stock_compliance.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        elif strategy == "always_abstain":
            shutil.rmtree(output)
            output.mkdir()
        elif strategy == "template_or_keyword":
            lines = (output / "route_evidence.tsv").read_text().splitlines()
            (output / "route_evidence.tsv").write_text("\n".join(lines[:-1]) + "\n", encoding="utf-8")
        return
    if task_id == "eb010-next-batch-001":
        if strategy == "simple_legal_baseline":
            rows = list(csv.DictReader((output / "next_batch.csv").open()))
            candidates = {row["candidate_id"]: row for row in csv.DictReader((ROOT / "benchmarks" / task_id / "data/candidates.csv").open())}
            fields = list(rows[0])
            alternative = []
            for candidate_id in ("C-1", "C-3", "C-4"):
                row = candidates[candidate_id]
                alternative.append({**row, "candidate_utility": 0})
            write_csv(output / "next_batch.csv", fields, alternative)
        elif strategy == "always_abstain":
            shutil.rmtree(output)
            output.mkdir()
        elif strategy == "template_or_keyword":
            rows = list(csv.DictReader((output / "next_batch.csv").open()))
            rows[0]["candidate_id"] = "C-5"
            write_csv(output / "next_batch.csv", list(rows[0]), rows)
        return
    if strategy == "simple_legal_baseline":
        for path in output.glob("*.csv"):
            path.unlink()
        for name in ("structure_identity.tsv", "event_trace.csv", "run_manifest.json"):
            path = output / name
            if path.exists():
                path.unlink()
    elif strategy == "always_abstain":
        for path in output.glob("*.csv"):
            path.unlink()
        (output / "run_manifest.json").write_text("{}\n", encoding="utf-8")
    elif strategy == "template_or_keyword":
        if task_id == "eb001-split-leakage-001":
            report_path = output / "split_audit.json"
            report = json.loads(report_path.read_text(encoding="utf-8"))
            report["canonical_overlap"] = []
            report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        else:
            path = output / "adtte.csv"
            with path.open(newline="", encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))
            rows[0]["CNSR"] = "1" if rows[0]["CNSR"] == "0" else "0"
            write_csv(path, list(rows[0]), rows)


def run_task(task_id: str) -> dict:
    verifier = load_verifier(task_id)
    task = ROOT / "benchmarks" / task_id
    data = task / "data"
    reference = task / "verifier_only" / "reference.json"
    records = []
    with tempfile.TemporaryDirectory(prefix=f"{task_id}-baselines-") as temp:
        root = Path(temp)
        for strategy in STRATEGIES:
            output = root / strategy
            REFERENCE_WRITERS[task_id](verifier, data, output)
            mutate_baseline(task_id, strategy, output)
            passed, errors = verifier.verify(output, data, reference)
            if passed:
                attribution = None
            elif strategy == "simple_legal_baseline" and task_id in SCIENTIFIC_JUDGMENT_TASKS:
                attribution = "scientific_judgment"
            elif strategy == "simple_legal_baseline":
                attribution = "artifact_completeness"
            elif strategy == "always_abstain":
                attribution = "delivery_failure"
            else:
                attribution = "shortcut_or_calculation"
            records.append({
                "strategy": strategy,
                "status": "pass" if passed else "verifier_fail",
                "passed": passed,
                "error_count": len(errors),
                "failure_attribution": attribution,
            })
    return {"task_id": task_id, "protocol_version": "enterprise-model-trial.v1", "status": "BASELINES_COMPLETE", "target_model_status": "NOT_RUN", "records": records}


def main() -> int:
    task_ids = (
        "eb001-split-leakage-001",
        "eb003-failure-recovery-003",
        "eb004-adtte-censoring-002",
        "eb005-batch-normalization-002",
        "eb008-stock-route-001",
        "eb010-next-batch-001",
    )
    results = [run_task(task_id) for task_id in task_ids]
    for result in results:
        output = ROOT / "benchmarks" / result["task_id"] / "quality" / "model_trial_results.json"
        previous = json.loads(output.read_text(encoding="utf-8")) if output.is_file() else {}
        historical_runs = previous.get("historical_target_model_runs") or previous.get("run_records")
        if historical_runs:
            result["historical_target_model_runs"] = historical_runs
        for field in (
            "historical_task_version",
            "historical_target_model_status",
            "historical_trial_archive",
            "current_task_version",
            "target_model",
            "rerun_required_for",
            "current_target_model_run",
        ):
            if previous.get(field) is not None:
                result[field] = previous[field]
        if previous.get("current_target_model_run"):
            result["target_model_status"] = previous.get("target_model_status", "PASS")
            result["status"] = previous.get("status", "TARGET_TRIAL_COMPLETE")
        output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        card_path = output.parent / "model_trial_card.json"
        card = json.loads(card_path.read_text(encoding="utf-8"))
        target_records = [row for row in card.get("run_records", []) if row.get("strategy") == "target_model"]
        card["run_records"] = result["records"] + target_records
        card["target_model_status"] = result["target_model_status"]
        card["status"] = "BASELINES_COMPLETE"
        card_path.write_text(json.dumps(card, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "BASELINES_COMPLETE", "tasks": results}, ensure_ascii=False, indent=2))
    return 0 if all(item["records"][0]["passed"] for item in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
