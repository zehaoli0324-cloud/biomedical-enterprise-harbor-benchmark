#!/usr/bin/env python3
"""Run author-side controls for the L5 closed-loop replay fixture."""

from __future__ import annotations

import csv
import importlib.util
import json
import shutil
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TASK = "eb010-closed-loop-replay-003"


def load():
    path = ROOT / "benchmarks" / TASK / "verifier.py"
    spec = importlib.util.spec_from_file_location("l5_verifier", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def write_reference(verifier, output: Path, data: Path) -> None:
    exp = verifier.expected(data)
    output.mkdir(parents=True, exist_ok=True)
    (output / "policy.json").write_text(json.dumps({
        "selected_policy": exp["selected_policy"],
        "policies": exp["policies"],
        "rules_version": exp["rules_version"],
        "claim_boundary": "planning_only_not_experimental_proof",
        "human_review_required": True,
    }) + "\n")
    with (output / "replay.tsv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["replay_id", "policy_id", "observed_gain"], delimiter="\t")
        writer.writeheader()
        writer.writerows(exp["replays"])
    (output / "audit.md").write_text("Stage order, budget, future outcome boundary, seed stability, stop rule and human review are audited. This is not experimental proof.\n")
    (output / "manifest.json").write_text(json.dumps({"input_sha256": exp["hashes"], "rules_version": exp["rules_version"], "deterministic": True}) + "\n")


def main() -> int:
    verifier = load()
    task = ROOT / "benchmarks" / TASK
    controls = []
    with tempfile.TemporaryDirectory(prefix="l5-replay-controls-") as temp:
        root = Path(temp)
        positive = root / "positive"
        write_reference(verifier, positive, task / "data")
        passed, errors = verifier.verify(positive, task / "data", task / "verifier_only/reference.json")
        controls.append({"control_id": "positive-reference", "kind": "positive", "passed": passed, "errors": errors})

        leakage = root / "leakage"
        shutil.copytree(positive, leakage)
        report = json.loads((leakage / "policy.json").read_text())
        report["policies"]["policy_safe"]["future_outcome_leakage"] = True
        (leakage / "policy.json").write_text(json.dumps(report))
        passed, errors = verifier.verify(leakage, task / "data", task / "verifier_only/reference.json")
        controls.append({"control_id": "negative-future-leakage", "kind": "negative", "passed": not passed, "errors": errors})

        invariant = root / "invariant"
        shutil.copytree(positive, invariant)
        rows = list(csv.DictReader((invariant / "replay.tsv").open(newline=""), delimiter="\t"))
        rows.reverse()
        with (invariant / "replay.tsv").open("w", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=["replay_id", "policy_id", "observed_gain"], delimiter="\t")
            writer.writeheader()
            writer.writerows(rows)
        passed, errors = verifier.verify(invariant, task / "data", task / "verifier_only/reference.json")
        controls.append({"control_id": "invariance-replay-order", "kind": "invariance", "passed": passed, "errors": errors})

        missing = root / "missing"
        shutil.copytree(positive, missing)
        manifest = json.loads((missing / "manifest.json").read_text()); manifest.pop("input_sha256"); (missing / "manifest.json").write_text(json.dumps(manifest))
        passed, errors = verifier.verify(missing, task / "data", task / "verifier_only/reference.json")
        controls.append({"control_id": "insufficient-provenance", "kind": "insufficient_evidence", "passed": not passed, "errors": errors})

    result = {"schema_version": "enterprise_control_calibration.v1", "task_id": TASK, "status": "CALIBRATED" if all(row["passed"] for row in controls) else "FAILED", "controls": controls}
    (task / "controls/calibration_results.json").write_text(json.dumps(result, indent=2) + "\n")
    plan_path = task / "quality/control_plan_card.json"
    plan = json.loads(plan_path.read_text())
    plan["calibration_status"] = result["status"]
    plan["status"] = result["status"]
    plan_path.write_text(json.dumps(plan, indent=2) + "\n")
    sop_path = task / "quality/sop_card.json"
    sop = json.loads(sop_path.read_text())
    sop["control_status"] = result["status"]
    sop_path.write_text(json.dumps(sop, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    return 0 if result["status"] == "CALIBRATED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
