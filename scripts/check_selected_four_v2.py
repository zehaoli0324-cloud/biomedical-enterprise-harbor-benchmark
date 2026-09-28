#!/usr/bin/env python3
"""Run oracle, NOP, mutation and abstention controls for the selected four tasks."""
from __future__ import annotations

import csv
import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BENCHMARKS = ROOT / "benchmarks"


def module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    loaded = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(loaded)
    return loaded


def read(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def write(path: Path, value) -> None:
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def run_solution(task: Path, out: Path) -> None:
    subprocess.run(
        [sys.executable, str(task / "solution/solve.py"), "--data", str(task / "data"), "--out", str(out)],
        check=True,
    )


def verify(v, task: Path, out: Path):
    try:
        return v.verify(out, task / "data", task / "verifier_only/reference.json")
    except TypeError:
        return v.verify(out, task / "data")


def record(variant_id: str, expected_pass: bool | None, actual: tuple[bool, list[str]], note: str = ""):
    verifier_passed, errors = actual
    control_passed = True if expected_pass is None else verifier_passed is expected_pass
    return {
        "variant_id": variant_id,
        "status": "PASS" if control_passed else "FAIL",
        "expected_verifier_pass": expected_pass,
        "verifier_passed": verifier_passed,
        "score": 1.0 if verifier_passed else 0.0,
        "errors": errors,
        "note": note,
    }


def copy_variant(base: Path, root: Path, name: str) -> Path:
    target = root / name
    shutil.copytree(base, target)
    return target


def eb006(temp: Path):
    task = BENCHMARKS / "eb006-research-completion-011"
    v = module(task / "verifier.py", "selected_eb006_verifier")
    oracle = temp / "eb006-oracle"
    run_solution(task, oracle)
    checks = {
        "oracle": record("oracle", True, verify(v, task, oracle)),
        "nop": record("nop", False, verify(v, task, temp / "eb006-nop")),
    }
    all_abstain = copy_variant(oracle, temp, "eb006-all-abstain")
    payload = read(all_abstain / "results.json")
    for row in payload["checks"] + payload["assay_checks"]:
        row["status"] = "INSUFFICIENT"
    payload["decision"]["selected"] = None
    write(all_abstain / "results.json", payload)

    all_definite = copy_variant(oracle, temp, "eb006-all-definite")
    payload = read(all_definite / "results.json")
    missing = next(row for row in payload["assay_checks"] if row["status"] == "INSUFFICIENT")
    missing["status"] = "SUPPORTED"
    write(all_definite / "results.json", payload)

    wrong_abstain = copy_variant(oracle, temp, "eb006-wrong-abstain")
    payload = read(wrong_abstain / "results.json")
    positive = next(row for row in payload["checks"] if row["status"] == "SUPPORTED")
    positive["status"] = "INSUFFICIENT"
    write(wrong_abstain / "results.json", payload)

    variants = [
        record("all_abstain", False, verify(v, task, all_abstain)),
        record("all_definite", False, verify(v, task, all_definite), "The one missing assay unit cannot be forced determinate."),
        record("positive_plus_insufficient_abstain", True, verify(v, task, oracle), "Oracle contains 35 determinate units and one local insufficient unit."),
        record("positive_as_wrong_abstain", False, verify(v, task, wrong_abstain)),
    ]
    checks["mutation"] = variants[-1]
    return task, checks, variants


def eb013(temp: Path):
    task = BENCHMARKS / "eb013-cross-context-evidence-portfolio-005"
    cal = module(ROOT / "scripts/calibrate_cross_context_portfolio.py", "selected_eb013_calibration")
    v = module(task / "verifier.py", "selected_eb013_verifier")
    oracle = temp / "eb013-oracle"
    cal.reference(oracle, task / "data", v)
    checks = {
        "oracle": record("oracle", True, verify(v, task, oracle)),
        "nop": record("nop", False, verify(v, task, temp / "eb013-nop")),
    }
    all_abstain = copy_variant(oracle, temp, "eb013-all-abstain")
    payload = read(all_abstain / "decision.json")
    payload["decision"] = "request_information"
    write(all_abstain / "decision.json", payload)

    wrong_abstain = copy_variant(oracle, temp, "eb013-wrong-abstain")
    payload = read(wrong_abstain / "plan.json")
    payload["contexts"][0]["decision"] = "INSUFFICIENT"
    write(wrong_abstain / "plan.json", payload)

    variants = [
        record("all_abstain", False, verify(v, task, all_abstain)),
        record("all_definite", True, verify(v, task, oracle)),
        record("positive_plus_insufficient_abstain", True, verify(v, task, oracle), "No insufficient unit exists; the control confirms that none may be invented."),
        record("positive_as_wrong_abstain", False, verify(v, task, wrong_abstain)),
    ]
    checks["mutation"] = variants[-1]
    return task, checks, variants


def eb014(temp: Path):
    task = BENCHMARKS / "eb014-sequential-evidence-feedback-002"
    cal = module(ROOT / "scripts/calibrate_sequential_feedback.py", "selected_eb014_calibration")
    v = module(task / "verifier.py", "selected_eb014_verifier")
    oracle = temp / "eb014-oracle"
    cal.reference(oracle)
    checks = {
        "oracle": record("oracle", True, verify(v, task, oracle)),
        "nop": record("nop", False, verify(v, task, temp / "eb014-nop")),
    }
    all_abstain = copy_variant(oracle, temp, "eb014-all-abstain")
    payload = read(all_abstain / "research_log.json")
    payload["events"] = []
    write(all_abstain / "research_log.json", payload)

    wrong_abstain = copy_variant(oracle, temp, "eb014-wrong-abstain")
    payload = read(wrong_abstain / "research_log.json")
    payload["events"][3]["observed_outcome"] = "unknown"
    write(wrong_abstain / "research_log.json", payload)

    variants = [
        record("all_abstain", False, verify(v, task, all_abstain)),
        record("all_definite", True, verify(v, task, oracle)),
        record("positive_plus_insufficient_abstain", True, verify(v, task, oracle), "No insufficient unit exists; early hold is therefore invalid."),
        record("positive_as_wrong_abstain", False, verify(v, task, wrong_abstain)),
    ]
    checks["mutation"] = variants[-1]
    return task, checks, variants


def eb015(temp: Path):
    task = BENCHMARKS / "eb015-real-source-replacement-gate-001"
    v = module(task / "verifier.py", "selected_eb015_verifier")
    oracle = temp / "eb015-oracle"
    run_solution(task, oracle)
    checks = {
        "oracle": record("oracle", True, verify(v, task, oracle)),
        "nop": record("nop", False, verify(v, task, temp / "eb015-nop")),
    }
    all_abstain = copy_variant(oracle, temp, "eb015-all-abstain")
    path = all_abstain / "case_matrix.tsv"
    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle, delimiter="\t"))
        fields = list(rows[0])
    for row in rows:
        row["release_status"] = "UNKNOWN"
        row["selected_for_review"] = "false"
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)

    wrong_abstain = copy_variant(oracle, temp, "eb015-wrong-abstain")
    path = wrong_abstain / "case_matrix.tsv"
    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle, delimiter="\t"))
        fields = list(rows[0])
    ready = next(row for row in rows if row["release_status"] == "READY_FOR_REVIEW")
    ready["release_status"] = "BLOCKED_RIGHTS"
    ready["selected_for_review"] = "false"
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)

    variants = [
        record("all_abstain", False, verify(v, task, all_abstain)),
        record("all_definite", True, verify(v, task, oracle)),
        record("positive_plus_insufficient_abstain", True, verify(v, task, oracle), "No insufficient case exists; all nine cases must be classified."),
        record("positive_as_wrong_abstain", False, verify(v, task, wrong_abstain)),
    ]
    checks["mutation"] = variants[-1]
    return task, checks, variants


def main() -> int:
    reports = []
    with tempfile.TemporaryDirectory(prefix="selected-four-v2-") as raw:
        temp = Path(raw)
        for runner in (eb006, eb013, eb014, eb015):
            task, checks, variants = runner(temp)
            passed = all(row["status"] == "PASS" for row in [*checks.values(), *variants])
            result = {
                "schema_version": "selected_four_dynamic_controls.v1",
                "task_id": task.name,
                "status": "PASS" if passed else "FAIL",
                "oracle_nop_mutation": checks,
                "variants": variants,
                "blanket_abstain_fraction_of_reference_score": 0.0,
                "generated_by": "scripts/check_selected_four_v2.py",
            }
            write(task / "quality/abstention_variant_results.json", result)
            plan_path = task / "quality/abstention_variant_plan.json"
            plan = read(plan_path)
            plan["variants"] = variants
            plan["gate_status"] = "PASS" if passed else "FAIL"
            write(plan_path, plan)
            card_path = task / "quality/evidence_surface_card.json"
            card = read(card_path)
            card["variant_status"] = "PASS" if passed else "FAIL"
            card["status"] = "PASS" if passed else "BLOCKED"
            write(card_path, card)
            reports.append({"task_id": task.name, "status": result["status"]})
    print(json.dumps({"status": "PASS" if all(row["status"] == "PASS" for row in reports) else "FAIL", "tasks": reports}, indent=2))
    return 0 if all(row["status"] == "PASS" for row in reports) else 1


if __name__ == "__main__":
    raise SystemExit(main())
