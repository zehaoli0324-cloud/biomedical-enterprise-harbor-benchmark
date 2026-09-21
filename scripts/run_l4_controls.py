#!/usr/bin/env python3
"""Run deterministic controls for the materialized L4 tranche."""

from __future__ import annotations

import csv
import importlib.util
import json
import shutil
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TASKS = (
    "eb003-recovery-chain-005",
    "eb005-normalization-hierarchy-003",
    "eb008-route-portfolio-002",
    "eb010-next-batch-002",
    "eb011-measurement-request-005",
    "eb012-cross-handoff-audit-001",
)


def load(task_id):
    path = ROOT / "benchmarks" / task_id / "verifier.py"
    spec = importlib.util.spec_from_file_location(task_id, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def submission(path: Path, verifier, data: Path) -> None:
    expected = verifier.expected(data)
    (path / "decision.json").write_text(json.dumps({"decision": expected["decision"], "rules_version": expected["rules_version"]}))
    fields = ["entity", "outcome", "decision", "provenance", "uncertainty", "claim_boundary"]
    with (path / "evidence.tsv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, delimiter="\t")
        writer.writeheader()
        for entity in expected["entities"]:
            writer.writerow({"entity": entity, "outcome": expected["outcomes"][entity], "decision": expected["decision"], "provenance": f"case.json#{entity}", "uncertainty": "bounded fixture", "claim_boundary": "not experimental proof"})
    (path / "review.md").write_text("Human review remains required; stop on missing evidence. This is not experimental proof.\n")
    (path / "manifest.json").write_text(json.dumps({"input_sha256": expected["hashes"], "rules_version": expected["rules_version"], "deterministic": True}))


def mutate_case(data: Path, task_id: str) -> None:
    case = json.loads((data / "case.json").read_text())
    if case["kind"] == "recovery":
        case["branches"][0]["side_effect"] = "irreversible"
    elif case["kind"] == "normalization":
        next(row for row in case["profiles"] if row["profile"] == "hierarchical")["metadata_complete"] = False
    elif case["kind"] == "route":
        next(row for row in case["routes"] if row["route_id"] == "R-A")["evidence_status"] = "retracted"
    elif case["kind"] == "batch":
        rules = json.loads((data / "rules.json").read_text())
        rules["budget"] = 5.0
        (data / "rules.json").write_text(json.dumps(rules))
        return
    elif case["kind"] == "measurement":
        next(row for row in case["options"] if row["measurement_id"] == "M-02")["feasible"] = False
    elif case["kind"] == "handoff":
        for row in case["artifacts"]:
            row["hash_ok"] = True
    (data / "case.json").write_text(json.dumps(case))


def run_task(task_id: str) -> dict:
    verifier = load(task_id)
    root = ROOT / "benchmarks" / task_id
    baseline = verifier.expected(root / "data")
    controls = []
    with tempfile.TemporaryDirectory(prefix=f"{task_id}-controls-") as temp:
        out = Path(temp) / "positive"
        out.mkdir()
        submission(out, verifier, root / "data")
        passed, errors = verifier.verify(out, root / "data", root / "verifier_only/reference.json")
        controls.append({"control_id": "positive-reference", "kind": "positive", "passed": passed, "errors": errors})

        missing = Path(temp) / "missing"
        missing.mkdir()
        submission(missing, verifier, root / "data")
        evidence = list(csv.DictReader((missing / "evidence.tsv").open(newline=""), delimiter="\t"))
        (missing / "evidence.tsv").write_text("\t".join(evidence[0]) + "\n" + "\n".join("\t".join(str(value) for key, value in row.items()) for row in evidence[:-1]) + "\n")
        passed, errors = verifier.verify(missing, root / "data", root / "verifier_only/reference.json")
        controls.append({"control_id": "insufficient-evidence", "kind": "insufficient_evidence", "passed": not passed, "errors": errors})

        reordered = Path(temp) / "reordered"
        shutil.copytree(root / "data", reordered)
        case = json.loads((reordered / "case.json").read_text())
        for key in ("branches", "profiles", "routes", "candidates", "options", "artifacts"):
            if key in case:
                case[key] = list(reversed(case[key]))
        (reordered / "case.json").write_text(json.dumps(case))
        reordered_expected = verifier.expected(reordered)
        controls.append({"control_id": "invariance-row-order", "kind": "invariance", "passed": reordered_expected["decision"] == baseline["decision"], "observed": reordered_expected["decision"]})

        flipped = Path(temp) / "flipped"
        shutil.copytree(root / "data", flipped)
        mutate_case(flipped, task_id)
        flipped_expected = verifier.expected(flipped)
        controls.append({"control_id": "single-factor-decision-flip", "kind": "negative", "passed": flipped_expected["decision"] != baseline["decision"], "observed": flipped_expected["decision"], "baseline": baseline["decision"]})
    return {"task_id": task_id, "status": "CALIBRATED" if all(item["passed"] for item in controls) else "FAILED", "controls": controls}


def main() -> int:
    results = [run_task(task_id) for task_id in TASKS]
    payload = {"schema_version": "enterprise_control_calibration.v1", "status": "CALIBRATED" if all(item["status"] == "CALIBRATED" for item in results) else "FAILED", "tasks": results}
    for result in results:
        path = ROOT / "benchmarks" / result["task_id"] / "controls" / "calibration_results.json"
        path.parent.mkdir(exist_ok=True)
        path.write_text(json.dumps(payload | {"tasks": [result]}, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["status"] == "CALIBRATED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
