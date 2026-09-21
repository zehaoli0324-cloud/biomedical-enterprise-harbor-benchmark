#!/usr/bin/env python3
"""Run controls and author-side baselines for EB006 signal/noise task."""

from __future__ import annotations

import csv
import importlib.util
import json
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "eb006-signal-noise-004"
TASK = ROOT / "benchmarks" / TASK_ID
STRATEGIES = ("reference_solution", "simple_legal_baseline", "always_abstain", "template_or_keyword")


def load_verifier():
    spec = importlib.util.spec_from_file_location("eb006_verifier", TASK / "verifier.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_json(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def reference(verifier, out: Path) -> None:
    exp = verifier.expected(TASK / "data")
    write_json(out / "signal_noise_report.json", exp)
    with (out / "replicate_diagnostics.tsv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["perturbation", "plate", "replicate", "raw_signal", "adjusted_signal", "control_status"], delimiter="\t")
        writer.writeheader()
        with (TASK / "data/profiles.csv").open(newline="", encoding="utf-8") as source:
            writer.writerows(csv.DictReader(source))
    (out / "profile_review_gate.md").write_text(
        "Signal survives technical noise checks; human review remains required; this is not mechanism.\n",
        encoding="utf-8",
    )


def run_controls(verifier) -> dict:
    exp = verifier.expected(TASK / "data")
    controls = []
    with tempfile.TemporaryDirectory(prefix="eb006-controls-") as temp:
        root = Path(temp)
        out = root / "positive"
        out.mkdir()
        reference(verifier, out)
        ok, errors = verifier.verify(out, TASK / "data", TASK / "verifier_only/reference.json")
        controls.append({"control_id": "positive-reference-signal", "kind": "positive", "passed": ok, "errors": errors})

        negative = root / "negative"
        negative.mkdir()
        reference(verifier, negative)
        report = json.loads((negative / "signal_noise_report.json").read_text())
        report["control_drift"] = exp["control_drift"] + 0.1
        write_json(negative / "signal_noise_report.json", report)
        ok, errors = verifier.verify(negative, TASK / "data", TASK / "verifier_only/reference.json")
        controls.append({"control_id": "negative-control-drift", "kind": "negative", "passed": not ok, "errors": errors})

        invariant = root / "invariance"
        invariant.mkdir()
        reference(verifier, invariant)
        lines = (invariant / "replicate_diagnostics.tsv").read_text().splitlines()
        (invariant / "replicate_diagnostics.tsv").write_text("\n".join([lines[0], *reversed(lines[1:])]) + "\n", encoding="utf-8")
        ok, errors = verifier.verify(invariant, TASK / "data", TASK / "verifier_only/reference.json")
        controls.append({"control_id": "invariance-replicate-order", "kind": "invariance", "passed": ok, "errors": errors})

        insufficient = root / "insufficient"
        insufficient.mkdir()
        reference(verifier, insufficient)
        report = json.loads((insufficient / "signal_noise_report.json").read_text())
        report.pop("input_sha256")
        write_json(insufficient / "signal_noise_report.json", report)
        ok, errors = verifier.verify(insufficient, TASK / "data", TASK / "verifier_only/reference.json")
        controls.append({"control_id": "insufficient-provenance", "kind": "insufficient_evidence", "passed": not ok, "errors": errors})
    return {"task_id": TASK_ID, "status": "CALIBRATED" if all(item["passed"] for item in controls) else "FAILED", "controls": controls}


def run_baselines(verifier) -> dict:
    records = []
    with tempfile.TemporaryDirectory(prefix="eb006-baselines-") as temp:
        root = Path(temp)
        for strategy in STRATEGIES:
            out = root / strategy
            out.mkdir()
            reference(verifier, out)
            if strategy == "simple_legal_baseline":
                (out / "replicate_diagnostics.tsv").unlink()
            elif strategy == "always_abstain":
                for path in out.iterdir():
                    path.unlink()
            elif strategy == "template_or_keyword":
                report = json.loads((out / "signal_noise_report.json").read_text())
                report["adjusted_effect"] = 0.0
                write_json(out / "signal_noise_report.json", report)
            passed, errors = verifier.verify(out, TASK / "data", TASK / "verifier_only/reference.json")
            attribution = None if passed else ("artifact_completeness" if strategy == "simple_legal_baseline" else "claim_boundary_or_abstention" if strategy == "always_abstain" else "calculation_or_tool")
            records.append({"strategy": strategy, "status": "pass" if passed else "verifier_fail", "passed": passed, "error_count": len(errors), "failure_attribution": attribution, "errors": errors})
    return {"task_id": TASK_ID, "protocol_version": "enterprise-model-trial.v1", "status": "BASELINES_COMPLETE", "target_model_status": "NOT_RUN", "records": records}


def main() -> None:
    verifier = load_verifier()
    controls = run_controls(verifier)
    baselines = run_baselines(verifier)
    write_json(TASK / "controls/calibration_results.json", {"schema_version": "enterprise_control_calibration.v1", **controls})
    write_json(TASK / "quality/model_trial_results.json", baselines)
    card_path = TASK / "quality/control_plan_card.json"
    card = json.loads(card_path.read_text())
    card["calibration_status"] = controls["status"]
    card_path.write_text(json.dumps(card, ensure_ascii=False, indent=2) + "\n")
    trial_path = TASK / "quality/model_trial_card.json"
    trial = json.loads(trial_path.read_text())
    trial.update({"status": baselines["status"], "target_model_status": "NOT_RUN", "run_records": baselines["records"]})
    trial_path.write_text(json.dumps(trial, ensure_ascii=False, indent=2) + "\n")
    sop_path = TASK / "quality/sop_card.json"
    sop = json.loads(sop_path.read_text())
    sop.update({"control_status": controls["status"], "model_trial_status": baselines["status"]})
    sop_path.write_text(json.dumps(sop, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"controls": controls, "baselines": baselines}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
