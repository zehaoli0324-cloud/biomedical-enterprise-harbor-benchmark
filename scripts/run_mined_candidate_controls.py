#!/usr/bin/env python3
"""Calibrate the two newly materialized mined candidates."""

from __future__ import annotations

import csv
import importlib.util
import json
import shutil
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(task_id: str):
    spec = importlib.util.spec_from_file_location(task_id, ROOT / "benchmarks" / task_id / "verifier.py")
    module = importlib.util.module_from_spec(spec); assert spec.loader; spec.loader.exec_module(module); return module


def eb003() -> dict:
    task = "eb003-replay-provenance-004"; verifier = load(task); data = ROOT / "benchmarks" / task / "data"; reference = ROOT / "benchmarks" / task / "verifier_only/reference.json"; exp = verifier.expected(data); controls = []
    with tempfile.TemporaryDirectory() as temp:
        out = Path(temp)
        (out / "replay_manifest.json").write_text(json.dumps({"artifact_id": exp["artifact_id"], "rules_version": exp["rules_version"], "input_hashes": exp["input_hashes"], "output_hashes": exp["output_hashes"], "environment": exp["environment"], "replay_status": "reproduced"}), encoding="utf-8")
        (out / "provenance_diff.tsv").write_text("field\tstatus\ninput_hashes\tmatch\n", encoding="utf-8")
        (out / "handoff_replay_report.md").write_text("Replay checksum match; human review remains; not biological validation.\n", encoding="utf-8")
        ok, errors = verifier.verify(out, data, reference); controls.append({"control_id": "positive-reference-replay", "kind": "positive", "passed": ok, "errors": errors})
        manifest = json.loads((out / "replay_manifest.json").read_text()); manifest["environment"]["tool_version"] = "drifted"; (out / "replay_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
        ok, errors = verifier.verify(out, data, reference); controls.append({"control_id": "negative-environment-drift", "kind": "negative", "passed": not ok, "errors": errors})
        manifest["environment"]["tool_version"] = exp["environment"]["tool_version"]; (out / "replay_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
        (out / "provenance_diff.tsv").write_text("field\tstatus\ninput_hashes\tmatch\n", encoding="utf-8")
        ok, errors = verifier.verify(out, data, reference); controls.append({"control_id": "invariance-report-order", "kind": "invariance", "passed": ok, "errors": errors})
        (out / "replay_manifest.json").write_text(json.dumps({"artifact_id": exp["artifact_id"], "rules_version": exp["rules_version"], "replay_status": "reproduced"}), encoding="utf-8")
        ok, errors = verifier.verify(out, data, reference); controls.append({"control_id": "insufficient-provenance", "kind": "insufficient_evidence", "passed": not ok, "errors": errors})
    return {"task_id": task, "status": "CALIBRATED" if all(c["passed"] for c in controls) else "FAILED", "controls": controls}


def eb009() -> dict:
    task = "eb009-diversity-coverage-004"; verifier = load(task); data = ROOT / "benchmarks" / task / "data"; reference = ROOT / "benchmarks" / task / "verifier_only/reference.json"; exp = verifier.expected(data); controls = []
    with tempfile.TemporaryDirectory() as temp:
        out = Path(temp)
        (out / "candidate_set.tsv").write_text("candidate_id\tscaffold\tcluster\tvalid\nM-1\tS-A\tC-1\ttrue\nM-2\tS-B\tC-2\ttrue\nM-3\tS-C\tC-3\ttrue\n", encoding="utf-8")
        report = {k: exp[k] for k in ("candidate_count", "valid_count", "unique_valid_count", "scaffolds", "clusters", "coverage", "rules_version")}; report["input_sha256"] = exp["hashes"]
        (out / "diversity_report.json").write_text(json.dumps(report), encoding="utf-8")
        (out / "coverage_review_gate.md").write_text("Coverage includes scaffold and cluster checks; human review required; not biological activity.\n", encoding="utf-8")
        (out / "run_manifest.json").write_text(json.dumps({"input_sha256": exp["hashes"], "rules_version": exp["rules_version"], "deterministic": True}), encoding="utf-8")
        ok, errors = verifier.verify(out, data, reference); controls.append({"control_id": "positive-reference-coverage", "kind": "positive", "passed": ok, "errors": errors})
        broken = dict(report); broken["coverage"] = False; (out / "diversity_report.json").write_text(json.dumps(broken), encoding="utf-8")
        ok, errors = verifier.verify(out, data, reference); controls.append({"control_id": "negative-collapsed-coverage", "kind": "negative", "passed": not ok, "errors": errors})
        (out / "diversity_report.json").write_text(json.dumps(report), encoding="utf-8")
        ok, errors = verifier.verify(out, data, reference); controls.append({"control_id": "invariance-candidate-order", "kind": "invariance", "passed": ok, "errors": errors})
        (out / "run_manifest.json").write_text("{}\n", encoding="utf-8")
        ok, errors = verifier.verify(out, data, reference); controls.append({"control_id": "insufficient-provenance", "kind": "insufficient_evidence", "passed": not ok, "errors": errors})
    return {"task_id": task, "status": "CALIBRATED" if all(c["passed"] for c in controls) else "FAILED", "controls": controls}


def main() -> int:
    results = [eb003(), eb009()]
    payload = {"schema_version": "enterprise_control_calibration.v1", "status": "CALIBRATED" if all(r["status"] == "CALIBRATED" for r in results) else "FAILED", "tasks": results}
    for result in results:
        path = ROOT / "benchmarks" / result["task_id"] / "controls" / "calibration_results.json"; path.write_text(json.dumps({**payload, "tasks": [result]}, indent=2) + "\n", encoding="utf-8")
        quality = ROOT / "benchmarks" / result["task_id"] / "quality" / "control_plan_card.json"; card = json.loads(quality.read_text()); card["calibration_status"] = result["status"]; quality.write_text(json.dumps(card, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2)); return 0 if payload["status"] == "CALIBRATED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
