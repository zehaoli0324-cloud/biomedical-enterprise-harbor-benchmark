#!/usr/bin/env python3
"""Calibrate controls for the discovery and semantic ambiguity task."""

from __future__ import annotations

import csv
import importlib.util
import json
import shutil
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "eb010-closed-loop-ambiguity-004"


def load():
    task = ROOT / "benchmarks" / TASK_ID
    spec = importlib.util.spec_from_file_location("ambiguity_verifier", task / "verifier.py")
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return task, module


def reference(task, verifier, output):
    exp = verifier.expected(task / "data")
    output.mkdir(parents=True, exist_ok=True)
    (output / "plan.json").write_text(json.dumps({"operations": ["inventory", "interpret", "screen", "replay", "decide"], "total_cost": 6.5, "network_used": False, "stop_condition": "eligible_record_selected"}))
    (output / "decision.json").write_text(json.dumps({
        "selected_record": exp["selected_record"],
        "rules_version": exp["rules_version"],
        "claim_boundary": "planning_only_not_experimental_proof",
        "human_review_required": True,
        "records": exp["records"],
    }))
    with (output / "evidence.tsv").open("w", newline="") as handle:
        fields = ["record_id", "semantic_status", "eligible", "blocker_reasons"]
        writer = csv.DictWriter(handle, fieldnames=fields, delimiter="\t")
        writer.writeheader()
        for record_id, row in exp["records"].items():
            writer.writerow({"record_id": record_id, "semantic_status": row["semantic_status"], "eligible": str(row["eligible"]).lower(), "blocker_reasons": ",".join(row["blocker_reasons"])})
    (output / "discovery.json").write_text(json.dumps({"discovered_files": exp["discovered_files"], "input_hashes": exp["hashes"], "network": exp["network"], "deterministic": True}))
    (output / "audit.md").write_text("The plan uses an operation workflow and stops after selecting. Ambiguous language is escalated for human review. Scope, future outcome, stability and budget are checked. This is not experimental proof.")


def main() -> int:
    task, verifier = load()
    controls = []
    with tempfile.TemporaryDirectory(prefix="l5-ambiguity-controls-") as temp:
        root = Path(temp)
        positive = root / "positive"; reference(task, verifier, positive)
        passed, errors = verifier.verify(positive, task / "data", task / "verifier_only/reference.json")
        controls.append({"control_id":"positive-reference","kind":"positive","passed":passed,"errors":errors})

        negative = root / "negative"; shutil.copytree(positive, negative)
        decision = json.loads((negative / "decision.json").read_text()); decision["selected_record"] = "P-BETA"; (negative / "decision.json").write_text(json.dumps(decision))
        passed, errors = verifier.verify(negative, task / "data", task / "verifier_only/reference.json")
        controls.append({"control_id":"negative-ambiguity-forced-winner","kind":"negative","passed":not passed,"errors":errors})

        invariant = root / "invariant"; shutil.copytree(positive, invariant)
        rows = list(csv.DictReader((invariant / "evidence.tsv").open(newline=""), delimiter="\t")); rows.reverse()
        with (invariant / "evidence.tsv").open("w", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0]), delimiter="\t"); writer.writeheader(); writer.writerows(rows)
        passed, errors = verifier.verify(invariant, task / "data", task / "verifier_only/reference.json")
        controls.append({"control_id":"invariance-input-order","kind":"invariance","passed":passed,"errors":errors})

        missing = root / "missing"; shutil.copytree(positive, missing)
        discovery = json.loads((missing / "discovery.json").read_text()); discovery["input_hashes"].pop("inputs/semantic_lexicon.json"); (missing / "discovery.json").write_text(json.dumps(discovery))
        passed, errors = verifier.verify(missing, task / "data", task / "verifier_only/reference.json")
        controls.append({"control_id":"insufficient-discovery-provenance","kind":"insufficient_evidence","passed":not passed,"errors":errors})

        adversarial_data = root / "adversarial-data"
        shutil.copytree(task / "data", adversarial_data)
        records = json.loads((adversarial_data / "inputs/policy_records.json").read_text())
        beta = next(row for row in records if row["record_id"] == "P-BETA")
        beta["replays"] = [9.9, 9.85]
        (adversarial_data / "inputs/policy_records.json").write_text(json.dumps(records))
        observed = verifier.expected(adversarial_data)
        controls.append({
            "control_id": "adversarial-high-utility-ambiguous",
            "kind": "adversarial",
            "passed": observed["selected_record"] != "P-BETA" and not observed["records"]["P-BETA"]["eligible"],
            "observed": observed["selected_record"],
        })

        metamorphic_data = root / "metamorphic-data"
        shutil.copytree(task / "data", metamorphic_data)
        records = json.loads((metamorphic_data / "inputs/policy_records.json").read_text())
        alpha = next(row for row in records if row["record_id"] == "P-ALPHA")
        alpha["label"] = "continue"
        alpha["narrative"] = "Continue when the signal is above 0.50."
        (metamorphic_data / "inputs/policy_records.json").write_text(json.dumps(records))
        observed = verifier.expected(metamorphic_data)
        controls.append({
            "control_id": "metamorphic-proceed-synonym",
            "kind": "metamorphic",
            "passed": observed["selected_record"] == verifier.expected(task / "data")["selected_record"] and observed["records"]["P-ALPHA"]["semantic_status"] == "proceed",
            "observed": observed["selected_record"],
        })
    result = {"schema_version":"enterprise_control_calibration.v1","task_id":TASK_ID,"status":"CALIBRATED" if all(item["passed"] for item in controls) else "FAILED","controls":controls}
    (task / "controls/calibration_results.json").write_text(json.dumps(result, indent=2) + "\n")
    plan = json.loads((task / "quality/control_plan_card.json").read_text()); plan["calibration_status"] = result["status"]; plan["status"] = result["status"]; (task / "quality/control_plan_card.json").write_text(json.dumps(plan, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    return 0 if result["status"] == "CALIBRATED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
