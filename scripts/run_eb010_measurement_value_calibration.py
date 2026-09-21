#!/usr/bin/env python3
"""Run controls and author-side baselines for EB010 measurement-value task."""

from __future__ import annotations

import csv
import importlib.util
import json
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "eb010-measurement-value-004"
TASK = ROOT / "benchmarks" / TASK_ID
STRATEGIES = ("reference_solution", "simple_legal_baseline", "always_abstain", "template_or_keyword")


def load_verifier():
    spec = importlib.util.spec_from_file_location("eb010_measurement_verifier", TASK / "verifier.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_json(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def reference(verifier, out: Path) -> None:
    exp = verifier.expected(TASK / "data")
    with (out / "measurement_priority.tsv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=verifier.FIELDS, delimiter="\t")
        writer.writeheader()
        for row in exp["rows"]:
            writer.writerow({**row, "eligible": str(row["eligible"]).lower(), "rank": "" if row["rank"] is None else row["rank"]})
    write_json(out / "information_value_audit.json", {key: exp[key] for key in ("selected_measurement_id", "eligible_count", "max_cost", "rules_version", "formula_id", "input_sha256", "claim_boundary")})
    selected = next(row for row in csv.DictReader((TASK / "data/measurement_options.csv").open(newline="", encoding="utf-8")) if row["measurement_id"] == exp["selected_measurement_id"])
    (out / "approval_request.md").write_text(
        f"# Measurement approval request\n\nSelect {exp['selected_measurement_id']} for {selected['uncertainty_addressed']}. "
        "The assay is feasible, uses no future-outcome data, and remains preferred after the redundancy adjustment. "
        "Human review is required. This ranking is a planning aid and is not evidence of experimental improvement.\n",
        encoding="utf-8",
    )


def run_controls(verifier) -> dict:
    controls = []
    with tempfile.TemporaryDirectory(prefix="eb010-measurement-controls-") as temp:
        root = Path(temp)
        positive = root / "positive"
        positive.mkdir()
        reference(verifier, positive)
        passed, errors = verifier.verify(positive, TASK / "data", TASK / "verifier_only/reference.json")
        controls.append({"control_id": "positive-reference", "kind": "positive", "passed": passed, "errors": errors})

        negative = root / "negative"
        negative.mkdir()
        reference(verifier, negative)
        rows = list(csv.DictReader((negative / "measurement_priority.tsv").open(newline="", encoding="utf-8"), delimiter="\t"))
        rows[0]["net_information_value"] = "0.000000"
        with (negative / "measurement_priority.tsv").open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=verifier.FIELDS, delimiter="\t")
            writer.writeheader()
            writer.writerows(rows)
        passed, errors = verifier.verify(negative, TASK / "data", TASK / "verifier_only/reference.json")
        controls.append({"control_id": "negative-corrupt-ranking", "kind": "negative", "passed": not passed, "errors": errors})

        invariant = root / "invariance"
        invariant.mkdir()
        reference(verifier, invariant)
        rows = list(csv.DictReader((invariant / "measurement_priority.tsv").open(newline="", encoding="utf-8"), delimiter="\t"))
        with (invariant / "measurement_priority.tsv").open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=verifier.FIELDS, delimiter="\t")
            writer.writeheader()
            writer.writerows(reversed(rows))
        passed, errors = verifier.verify(invariant, TASK / "data", TASK / "verifier_only/reference.json")
        controls.append({"control_id": "invariance-row-order", "kind": "invariance", "passed": passed, "errors": errors})

        insufficient = root / "insufficient"
        insufficient.mkdir()
        reference(verifier, insufficient)
        audit = json.loads((insufficient / "information_value_audit.json").read_text(encoding="utf-8"))
        audit.pop("input_sha256")
        write_json(insufficient / "information_value_audit.json", audit)
        passed, errors = verifier.verify(insufficient, TASK / "data", TASK / "verifier_only/reference.json")
        controls.append({"control_id": "insufficient-provenance", "kind": "insufficient_evidence", "passed": not passed, "errors": errors})
    return {"schema_version": "enterprise_control_calibration.v1", "task_id": TASK_ID, "status": "CALIBRATED" if all(item["passed"] for item in controls) else "FAILED", "controls": controls}


def run_baselines(verifier) -> dict:
    records = []
    with tempfile.TemporaryDirectory(prefix="eb010-measurement-baselines-") as temp:
        root = Path(temp)
        for strategy in STRATEGIES:
            out = root / strategy
            out.mkdir()
            reference(verifier, out)
            if strategy == "simple_legal_baseline":
                (out / "approval_request.md").unlink()
            elif strategy == "always_abstain":
                for path in out.iterdir():
                    path.unlink()
            elif strategy == "template_or_keyword":
                audit = json.loads((out / "information_value_audit.json").read_text(encoding="utf-8"))
                audit["selected_measurement_id"] = "M-04"
                write_json(out / "information_value_audit.json", audit)
            passed, errors = verifier.verify(out, TASK / "data", TASK / "verifier_only/reference.json")
            attribution = None if passed else "artifact_completeness" if strategy == "simple_legal_baseline" else "abstention" if strategy == "always_abstain" else "method_choice"
            records.append({"strategy": strategy, "status": "pass" if passed else "verifier_fail", "passed": passed, "error_count": len(errors), "failure_attribution": attribution, "errors": errors})
    return {"task_id": TASK_ID, "protocol_version": "enterprise-model-trial.v1", "status": "BASELINES_COMPLETE", "target_model_status": "NOT_RUN", "records": records}


def main() -> None:
    verifier = load_verifier()
    controls = run_controls(verifier)
    baselines = run_baselines(verifier)
    write_json(TASK / "controls/calibration_results.json", controls)
    write_json(TASK / "quality/model_trial_results.json", baselines)
    control_card_path = TASK / "quality/control_plan_card.json"
    control_card = json.loads(control_card_path.read_text(encoding="utf-8"))
    control_card["calibration_status"] = controls["status"]
    write_json(control_card_path, control_card)
    trial_card_path = TASK / "quality/model_trial_card.json"
    trial_card = json.loads(trial_card_path.read_text(encoding="utf-8"))
    trial_card.update({"status": baselines["status"], "target_model_status": "NOT_RUN", "run_records": baselines["records"]})
    write_json(trial_card_path, trial_card)
    sop_path = TASK / "quality/sop_card.json"
    sop = json.loads(sop_path.read_text(encoding="utf-8"))
    sop.update({"control_status": controls["status"], "model_trial_status": baselines["status"]})
    write_json(sop_path, sop)
    print(json.dumps({"controls": controls, "baselines": baselines}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
