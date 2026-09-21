#!/usr/bin/env python3
"""Run controls and author-side trials for the L4 tranche."""

from __future__ import annotations

import csv
import importlib.util
import json
import shutil
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TASKS = [
    "eb003-recovery-chain-005",
    "eb005-normalization-hierarchy-003",
    "eb008-route-portfolio-002",
    "eb010-next-batch-002",
    "eb011-measurement-request-005",
    "eb012-cross-handoff-audit-001",
]


def load(task_id):
    task = ROOT / "benchmarks" / task_id
    spec = importlib.util.spec_from_file_location(task_id.replace("-", "_"), task / "verifier.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(module)
    return task, module


def reference(task: Path, verifier, out: Path) -> None:
    exp = verifier.expected(task / "data")
    out.mkdir(parents=True, exist_ok=True)
    (out / "decision.json").write_text(json.dumps({"decision": exp["decision"], "details": exp["decisions"], "rules_version": exp["rules_version"]}, indent=2) + "\n", encoding="utf-8")
    entities = exp.get("entities", ["decision", "provenance", "uncertainty", "claim_boundary"])
    outcomes = exp.get("outcomes", {entity: "preserved" for entity in entities})
    rows = [{"entity": entity, "outcome": str(outcomes.get(entity, "preserved")), "decision": exp["decision"], "provenance": "case.json+rules.json", "uncertainty": "preserved", "claim_boundary": "planning_only"} for entity in entities]
    with (out / "evidence.tsv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), delimiter="\t")
        writer.writeheader(); writer.writerows(rows)
    (out / "review.md").write_text("Human review remains required. Stop when a binding invariant is missing. This is not experimental proof.\n", encoding="utf-8")
    (out / "manifest.json").write_text(json.dumps({"input_sha256": exp["hashes"], "rules_version": exp["rules_version"], "deterministic": True}, indent=2) + "\n", encoding="utf-8")


def run_one(task_id: str) -> dict:
    task, verifier = load(task_id)
    controls = []
    with tempfile.TemporaryDirectory(prefix=f"{task_id}-controls-") as temp:
        root = Path(temp)
        positive = root / "positive"; reference(task, verifier, positive)
        passed, errors = verifier.verify(positive, task / "data", task / "verifier_only/reference.json")
        controls.append({"control_id": "positive-reference", "kind": "positive", "passed": passed, "errors": errors})
        negative = root / "negative"; shutil.copytree(positive, negative)
        report = json.loads((negative / "decision.json").read_text()); report["decision"] = "wrong_decision"; (negative / "decision.json").write_text(json.dumps(report) + "\n")
        passed, errors = verifier.verify(negative, task / "data", task / "verifier_only/reference.json")
        controls.append({"control_id": "negative-decision-flip", "kind": "negative", "passed": not passed, "errors": errors})
        invariant = root / "invariant"; shutil.copytree(positive, invariant)
        rows = list(csv.DictReader((invariant / "evidence.tsv").open(newline=""), delimiter="\t")); rows.reverse()
        with (invariant / "evidence.tsv").open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0]), delimiter="\t"); writer.writeheader(); writer.writerows(rows)
        passed, errors = verifier.verify(invariant, task / "data", task / "verifier_only/reference.json")
        controls.append({"control_id": "invariance-row-order", "kind": "invariance", "passed": passed, "errors": errors})
        insufficient = root / "insufficient"; shutil.copytree(positive, insufficient)
        manifest = json.loads((insufficient / "manifest.json").read_text()); manifest.pop("input_sha256"); (insufficient / "manifest.json").write_text(json.dumps(manifest) + "\n")
        passed, errors = verifier.verify(insufficient, task / "data", task / "verifier_only/reference.json")
        controls.append({"control_id": "insufficient-provenance", "kind": "insufficient_evidence", "passed": not passed, "errors": errors})
    calibration = {"schema_version": "enterprise_control_calibration.v1", "task_id": task_id, "status": "CALIBRATED" if all(row["passed"] for row in controls) else "FAILED", "controls": controls}
    (task / "controls/calibration_results.json").write_text(json.dumps(calibration, indent=2) + "\n", encoding="utf-8")
    records = []
    for strategy in ("reference_solution", "simple_legal_baseline", "always_abstain", "template_or_keyword"):
        with tempfile.TemporaryDirectory(prefix=f"{task_id}-baseline-") as temp:
            out = Path(temp) / strategy; reference(task, verifier, out)
            if strategy == "simple_legal_baseline": (out / "decision.json").unlink()
            elif strategy == "always_abstain": shutil.rmtree(out); out.mkdir()
            elif strategy == "template_or_keyword":
                report = json.loads((out / "decision.json").read_text()); report["decision"] = "wrong_decision"; (out / "decision.json").write_text(json.dumps(report) + "\n")
            passed, errors = verifier.verify(out, task / "data", task / "verifier_only/reference.json")
            records.append({"strategy": strategy, "status": "pass" if passed else "verifier_fail", "passed": passed, "error_count": len(errors), "failure_attribution": None if passed else "artifact_completeness" if strategy == "simple_legal_baseline" else "delivery_failure" if strategy == "always_abstain" else "method_choice", "errors": errors})
    trial = {"task_id": task_id, "protocol_version": "enterprise-model-trial.v1", "status": "BASELINES_COMPLETE", "target_model_status": "NOT_RUN", "records": records}
    (task / "quality/model_trial_results.json").write_text(json.dumps(trial, indent=2) + "\n", encoding="utf-8")
    card = json.loads((task / "quality/model_trial_card.json").read_text()); card.update({"status": "BASELINES_COMPLETE", "target_model_status": "NOT_RUN", "run_records": records}); (task / "quality/model_trial_card.json").write_text(json.dumps(card, indent=2) + "\n", encoding="utf-8")
    sop = json.loads((task / "quality/sop_card.json").read_text()); sop.update({"control_status": calibration["status"], "model_trial_status": "BASELINES_COMPLETE"}); (task / "quality/sop_card.json").write_text(json.dumps(sop, indent=2) + "\n", encoding="utf-8")
    control_card = json.loads((task / "quality/control_plan_card.json").read_text()); control_card["calibration_status"] = calibration["status"]; (task / "quality/control_plan_card.json").write_text(json.dumps(control_card, indent=2) + "\n", encoding="utf-8")
    return {"task_id": task_id, "calibration": calibration["status"], "baseline": trial["status"], "target_model": "NOT_RUN"}


def main():
    results = [run_one(task_id) for task_id in TASKS]
    print(json.dumps({"status": "CALIBRATED" if all(row["calibration"] == "CALIBRATED" for row in results) else "FAILED", "tasks": results}, indent=2))


if __name__ == "__main__":
    main()
