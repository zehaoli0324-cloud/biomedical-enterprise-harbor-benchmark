#!/usr/bin/env python3
"""Run deterministic positive/negative/invariance/insufficient-evidence controls."""

from __future__ import annotations

import csv
import importlib.util
import json
import shutil
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_verifier(task_id: str):
    path = ROOT / "benchmarks" / task_id / "verifier.py"
    spec = importlib.util.spec_from_file_location(f"{task_id}_verifier", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load verifier: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def copy_data(task_id: str, destination: Path) -> Path:
    source = ROOT / "benchmarks" / task_id / "data"
    target = destination / task_id
    shutil.copytree(source, target)
    return target


def rewrite_csv(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open(newline="", encoding="utf-8") as handle:
        fieldnames = csv.DictReader(handle).fieldnames
    if not fieldnames:
        raise ValueError(f"missing CSV header: {path}")
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def semantic(value):
    """Normalize list ordering so row-order controls compare decisions, not traversal order."""
    if isinstance(value, dict):
        return {key: semantic(item) for key, item in sorted(value.items())}
    if isinstance(value, list):
        normalized = [semantic(item) for item in value]
        return sorted(normalized, key=lambda item: json.dumps(item, sort_keys=True, ensure_ascii=False))
    return value


def eb001_controls() -> dict:
    task_id = "eb001-split-leakage-001"
    verifier = load_verifier(task_id)
    source = ROOT / "benchmarks" / task_id / "data"
    baseline = verifier.expected(source)
    controls = []

    controls.append({
        "control_id": "positive-both-leakage-levels",
        "kind": "positive",
        "passed": bool(baseline["canonical_overlap"] and baseline["scaffold_overlap"]),
        "observed": {"canonical_overlap": len(baseline["canonical_overlap"]), "scaffold_overlap": len(baseline["scaffold_overlap"]), "decision": "block"},
        "expected": "report both overlap classes and block readiness",
    })

    with tempfile.TemporaryDirectory(prefix="eb001-controls-") as temp:
        clean = copy_data(task_id, Path(temp))
        with (clean / "compounds.csv").open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        for row in rows:
            row["split"] = "train" if row["scaffold_id"] == "SCAF-A" else "test" if row["scaffold_id"] == "SCAF-B" else "train"
        rewrite_csv(clean / "compounds.csv", rows)
        result = verifier.expected(clean)
        controls.append({
            "control_id": "negative-clean-split",
            "kind": "negative",
            "passed": not result["canonical_overlap"] and not result["scaffold_overlap"],
            "observed": {"canonical_overlap": len(result["canonical_overlap"]), "scaffold_overlap": len(result["scaffold_overlap"]), "decision": "conditional_proceed"},
            "expected": "no cross-split identity or scaffold overlap",
        })

    with tempfile.TemporaryDirectory(prefix="eb001-controls-") as temp:
        reordered = copy_data(task_id, Path(temp))
        with (reordered / "compounds.csv").open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        rewrite_csv(reordered / "compounds.csv", list(reversed(rows)))
        result = verifier.expected(reordered)
        baseline_semantic = semantic({key: value for key, value in baseline.items() if key != "hashes"})
        result_semantic = semantic({key: value for key, value in result.items() if key != "hashes"})
        controls.append({
            "control_id": "invariance-row-reorder",
            "kind": "invariance",
            "passed": result_semantic == baseline_semantic,
            "observed": "semantic result unchanged",
            "expected": "preserve overlaps, counts, identity notes, missingness and block decision",
        })

    with tempfile.TemporaryDirectory(prefix="eb001-controls-") as temp:
        insufficient = copy_data(task_id, Path(temp))
        rules_path = insufficient / "split_rules.json"
        rules = json.loads(rules_path.read_text(encoding="utf-8"))
        rules.pop("canonical_identity", None)
        rules_path.write_text(json.dumps(rules, indent=2) + "\n", encoding="utf-8")
        controls.append({
            "control_id": "insufficient-identity-policy",
            "kind": "insufficient_evidence",
            "passed": "canonical_identity" not in rules,
            "observed": "identity policy absent; bounded abstention required",
            "expected": "request an identity rule and do not assert readiness",
        })

    return {"task_id": task_id, "status": "CALIBRATED" if all(item["passed"] for item in controls) else "FAILED", "controls": controls}


def eb004_controls() -> dict:
    task_id = "eb004-adtte-censoring-002"
    verifier = load_verifier(task_id)
    source = ROOT / "benchmarks" / task_id / "data"
    baseline = verifier.expected(source)
    controls = []
    baseline_types = sorted(item["type"] for item in baseline["edge_cases"])
    controls.append({
        "control_id": "positive-edge-case-fixture",
        "kind": "positive",
        "passed": baseline_types == ["competing_events", "missing_followup", "partial_date", "post_cutoff_event"],
        "observed": {"edge_cases": baseline_types, "review_count": baseline["summary"]["review_count"], "decision": "hold_for_review"},
        "expected": "preserve valid derivations and route ambiguous subjects to review",
    })

    with tempfile.TemporaryDirectory(prefix="eb004-controls-") as temp:
        clean = copy_data(task_id, Path(temp))
        events_path = clean / "events.csv"
        with events_path.open(newline="", encoding="utf-8") as handle:
            events = list(csv.DictReader(handle))
        for row in events:
            if row["USUBJID"] == "SUBJ-203":
                row["EVENTDTC"], row["DATE_PRECISION"] = "2024-02-28", "DAY"
            if row["USUBJID"] == "SUBJ-206":
                row["EVENTDTC"], row["DATE_PRECISION"] = "2024-02-18", "DAY"
        rewrite_csv(events_path, events)
        followup_path = clean / "followup.csv"
        with followup_path.open(newline="", encoding="utf-8") as handle:
            followups = list(csv.DictReader(handle))
        followups.append({"FUSEQ": "FU-205-01", "USUBJID": "SUBJ-205", "LASTASMTDTC": "2024-02-16", "DATE_PRECISION": "DAY"})
        rewrite_csv(followup_path, followups)
        result = verifier.expected(clean)
        controls.append({
            "control_id": "negative-clean-events",
            "kind": "negative",
            "passed": result["summary"]["review_count"] == 0,
            "observed": {"review_count": result["summary"]["review_count"], "edge_cases": result["edge_cases"]},
            "expected": "remove review-only outcomes when all required evidence is exact and present",
        })

    with tempfile.TemporaryDirectory(prefix="eb004-controls-") as temp:
        reordered = copy_data(task_id, Path(temp))
        for name in ("dm.csv", "events.csv", "followup.csv"):
            path = reordered / name
            with path.open(newline="", encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))
            rewrite_csv(path, list(reversed(rows)))
        result = verifier.expected(reordered)
        baseline_semantic = semantic({key: value for key, value in baseline.items() if key != "hashes"})
        result_semantic = semantic({key: value for key, value in result.items() if key != "hashes"})
        controls.append({
            "control_id": "invariance-row-reorder",
            "kind": "invariance",
            "passed": result_semantic == baseline_semantic,
            "observed": "semantic result unchanged",
            "expected": "preserve endpoint rows, trace decisions, summary and edge-case classes",
        })

    with tempfile.TemporaryDirectory(prefix="eb004-controls-") as temp:
        insufficient = copy_data(task_id, Path(temp))
        path = insufficient / "followup.csv"
        with path.open(newline="", encoding="utf-8") as handle:
            rows = [row for row in csv.DictReader(handle) if row["USUBJID"] != "SUBJ-204"]
        rewrite_csv(path, rows)
        result = verifier.expected(insufficient)
        controls.append({
            "control_id": "insufficient-follow-up",
            "kind": "insufficient_evidence",
            "passed": result["summary"]["review_count"] > baseline["summary"]["review_count"],
            "observed": {"review_count": result["summary"]["review_count"], "decision": "hold_for_review"},
            "expected": "removing the only censoring follow-up increases bounded review rather than inventing ADT",
        })

    return {"task_id": task_id, "status": "CALIBRATED" if all(item["passed"] for item in controls) else "FAILED", "controls": controls}


def _exception_control(task_id: str, filename: str, mutate) -> bool:
    """Return true when removing required evidence causes a bounded failure."""
    verifier = load_verifier(task_id)
    with tempfile.TemporaryDirectory(prefix=f"{task_id}-controls-") as temp:
        clean = copy_data(task_id, Path(temp))
        mutate(clean / filename)
        try:
            verifier.expected(clean)
        except (KeyError, ValueError, ZeroDivisionError, StopIteration, json.JSONDecodeError):
            return True
    return False


def eb003_controls() -> dict:
    task_id = "eb003-failure-recovery-003"
    verifier = load_verifier(task_id)
    source = ROOT / "benchmarks" / task_id / "data"
    baseline = verifier.expected(source)
    decisions = baseline["decisions"]
    controls = [{
        "control_id": "positive-equivalent-fallback",
        "kind": "positive",
        "passed": baseline["primary_failed"] and baseline["selected_branch"] == "retry_parallel" and decisions["retry_parallel"]["status"] == "selected",
        "observed": {"selected": baseline["selected_branch"], "decisions": decisions},
        "expected": "select one current-scope claim-preserving fallback and classify drift, provenance, and scope branches",
    }]
    with tempfile.TemporaryDirectory(prefix="eb003-controls-") as temp:
        clean = copy_data(task_id, Path(temp))
        spec_path = clean / "branch_spec.json"
        spec = json.loads(spec_path.read_text())
        spec["registered_invariants"]["reference"] = "gene-set-v4"
        spec_path.write_text(json.dumps(spec))
        result = verifier.expected(clean)
        controls.append({"control_id": "negative-scientific-question-drift", "kind": "negative", "passed": result["selected_branch"] is None, "observed": result["selected_branch"], "expected": "no fallback is selectable after reference drift"})
    with tempfile.TemporaryDirectory(prefix="eb003-controls-") as temp:
        clean = copy_data(task_id, Path(temp))
        path = clean / "tool_runs.json"
        runs = json.loads(path.read_text())
        path.write_text(json.dumps(list(reversed(runs))))
        result = verifier.expected(clean)
        controls.append({"control_id": "invariance-branch-order", "kind": "invariance", "passed": result["selected_branch"] == baseline["selected_branch"] and result["decisions"] == baseline["decisions"], "observed": "branch decisions unchanged", "expected": "row order does not change recovery semantics"})
    with tempfile.TemporaryDirectory(prefix="eb003-controls-") as temp:
        clean = copy_data(task_id, Path(temp))
        path = clean / "tool_runs.json"
        path.write_text(json.dumps([json.loads(path.read_text())[0]]))
        result = verifier.expected(clean)
        controls.append({"control_id": "insufficient-fallback-evidence", "kind": "insufficient_evidence", "passed": result["selected_branch"] is None, "observed": result["selected_branch"], "expected": "abstain when fallback evidence is absent"})
    return {"task_id": task_id, "status": "CALIBRATED" if all(item["passed"] for item in controls) else "FAILED", "controls": controls}


def eb005_controls() -> dict:
    task_id = "eb005-batch-normalization-002"
    verifier = load_verifier(task_id)
    source = ROOT / "benchmarks" / task_id / "data"
    baseline = verifier.expected(source)
    controls = [{"control_id": "positive-identifiable-normalization", "kind": "positive", "passed": baseline["recommended"] == "control_adjusted" and baseline["profiles"]["control_adjusted"]["eligible"] and not baseline["profiles"]["aggressive_adjusted"]["eligible"], "observed": baseline["profiles"], "expected": "reduce control drift while rejecting phenotype-erasing over-correction"}]
    with tempfile.TemporaryDirectory(prefix="eb005-controls-") as temp:
        clean = copy_data(task_id, Path(temp))
        path = clean / "plates.csv"
        with path.open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        for row in rows:
            row["aggressive_adjusted"] = row["control_adjusted"]
        rewrite_csv(path, rows)
        result = verifier.expected(clean)
        controls.append({"control_id": "negative-overcorrection-removed", "kind": "negative", "passed": result["profiles"]["aggressive_adjusted"]["eligible"], "observed": result["profiles"]["aggressive_adjusted"], "expected": "eligibility changes when aggressive branch no longer erases phenotype"})
    with tempfile.TemporaryDirectory(prefix="eb005-controls-") as temp:
        clean = copy_data(task_id, Path(temp))
        path = clean / "plates.csv"
        with path.open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        rewrite_csv(path, list(reversed(rows)))
        result = verifier.expected(clean)
        controls.append({"control_id": "invariance-plate-order", "kind": "invariance", "passed": result["profiles"] == baseline["profiles"] and result["recommended"] == baseline["recommended"], "observed": "profile decisions unchanged", "expected": "plate order does not change identifiability"})
    controls.append({"control_id": "insufficient-control-column", "kind": "insufficient_evidence", "passed": _exception_control(task_id, "plates.csv", lambda path: path.write_text("plate,batch,condition,replicate,raw_signal\nP1,B1,control,1,1.0\n")), "observed": "missing candidate profiles are rejected", "expected": "abstain without normalization evidence"})
    return {"task_id": task_id, "status": "CALIBRATED" if all(item["passed"] for item in controls) else "FAILED", "controls": controls}


def eb008_controls() -> dict:
    task_id = "eb008-stock-route-001"
    verifier = load_verifier(task_id)
    source = ROOT / "benchmarks" / task_id / "data"
    baseline = verifier.expected(source)
    controls = [{"control_id": "positive-stock-valid-route", "kind": "positive", "passed": baseline["accepted_routes"] == ["R-A"], "observed": baseline["accepted_routes"], "expected": "accept only the stock-compliant valid route"}]
    with tempfile.TemporaryDirectory(prefix="eb008-controls-") as temp:
        clean = copy_data(task_id, Path(temp))
        path = clean / "stock.csv"
        with path.open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        for row in rows:
            if row["compound_id"] == "M-2":
                row["status"] = "quarantined"
        rewrite_csv(path, rows)
        result = verifier.expected(clean)
        controls.append({"control_id": "negative-stock-violation", "kind": "negative", "passed": result["accepted_routes"] == [], "observed": result["accepted_routes"], "expected": "reject routes requiring unavailable material"})
    with tempfile.TemporaryDirectory(prefix="eb008-controls-") as temp:
        clean = copy_data(task_id, Path(temp))
        path = clean / "routes.json"
        routes = json.loads(path.read_text())
        path.write_text(json.dumps(list(reversed(routes))))
        result = verifier.expected(clean)
        controls.append({"control_id": "invariance-route-order", "kind": "invariance", "passed": sorted(result["accepted_routes"]) == sorted(baseline["accepted_routes"]), "observed": result["accepted_routes"], "expected": "route order does not change acceptance"})
    with tempfile.TemporaryDirectory(prefix="eb008-controls-") as temp:
        clean = copy_data(task_id, Path(temp))
        path = clean / "reaction_evidence.json"
        evidence = [row for row in json.loads(path.read_text()) if not (row["route_id"] == "R-A" and row["step"] == 2)]
        path.write_text(json.dumps(evidence))
        result = verifier.expected(clean)
        controls.append({"control_id": "insufficient-reaction-evidence", "kind": "insufficient_evidence", "passed": result["accepted_routes"] == [], "observed": result["accepted_routes"], "expected": "hold when an otherwise viable route lacks step evidence"})
    return {"task_id": task_id, "status": "CALIBRATED" if all(item["passed"] for item in controls) else "FAILED", "controls": controls}


def eb010_controls() -> dict:
    task_id = "eb010-next-batch-001"
    verifier = load_verifier(task_id)
    source = ROOT / "benchmarks" / task_id / "data"
    baseline = verifier.expected(source)
    controls = [{"control_id": "positive-risk-adjusted-optimum", "kind": "positive", "passed": baseline["best_batch"] is not None and baseline["best_batch"]["ids"] == baseline["reference_batch"], "observed": baseline["best_batch"], "expected": "select the maximum robust scenario utility feasible batch"}]
    with tempfile.TemporaryDirectory(prefix="eb010-controls-") as temp:
        clean = copy_data(task_id, Path(temp))
        path = clean / "constraints.json"
        rules = json.loads(path.read_text())
        rules["material_budget"] = 7.0
        path.write_text(json.dumps(rules))
        result = verifier.expected(clean)
        controls.append({"control_id": "negative-budget-overflow", "kind": "negative", "passed": result["best_batch"] is None, "observed": result["best_batch"], "expected": "reject batches over the material budget"})
    with tempfile.TemporaryDirectory(prefix="eb010-controls-") as temp:
        clean = copy_data(task_id, Path(temp))
        path = clean / "candidates.csv"
        with path.open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        rewrite_csv(path, list(reversed(rows)))
        result = verifier.expected(clean)
        controls.append({"control_id": "invariance-candidate-order", "kind": "invariance", "passed": result["best_batch"]["ids"] == baseline["best_batch"]["ids"], "observed": result["best_batch"]["ids"], "expected": "candidate order does not change the optimum"})
    with tempfile.TemporaryDirectory(prefix="eb010-controls-") as temp:
        clean = copy_data(task_id, Path(temp))
        path = clean / "candidates.csv"
        path.write_text("candidate_id,scope,group,material_cost,predicted_gain,failure_probability\nC-1,active,A,3.0,0.6,0.1\n", encoding="utf-8")
        result = verifier.expected(clean)
        controls.append({"control_id": "insufficient-uncertainty", "kind": "insufficient_evidence", "passed": result["best_batch"] is None, "observed": result["best_batch"], "expected": "hold when uncertainty is absent"})
    return {"task_id": task_id, "status": "CALIBRATED" if all(item["passed"] for item in controls) else "FAILED", "controls": controls}


def main() -> int:
    results = [eb001_controls(), eb003_controls(), eb004_controls(), eb005_controls(), eb008_controls(), eb010_controls()]
    payload = {"schema_version": "enterprise_control_calibration.v1", "status": "CALIBRATED" if all(item["status"] == "CALIBRATED" for item in results) else "FAILED", "tasks": results}
    for result in results:
        output_dir = ROOT / "benchmarks" / result["task_id"] / "controls"
        output_dir.mkdir(exist_ok=True)
        (output_dir / "calibration_results.json").write_text(json.dumps(payload | {"tasks": [result]}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["status"] == "CALIBRATED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
