#!/usr/bin/env python3
"""Run controls and author baselines for the L5.3 distributional-stress task."""

from __future__ import annotations

import csv
import importlib.util
import json
import shutil
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "eb010-distributional-policy-stress-006"
TASK = ROOT / "benchmarks" / TASK_ID


def load_verifier():
    spec = importlib.util.spec_from_file_location("distributional_stress_verifier", TASK / "verifier.py")
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def write_reference(verifier, output: Path, data: Path) -> None:
    exp = verifier.expected(data)
    output.mkdir(parents=True, exist_ok=True)
    report = {
        "selected_policy": exp["selected_policy"],
        "rules_version": exp["rules_version"],
        "claim_boundary": "planning_only_not_experimental_proof",
        "human_review_required": True,
        "profile_best_expected": exp["profile_best_expected"],
        "profile_winners": exp["profile_winners"],
        "leave_one_profile_out_winners": exp["leave_one_profile_out_winners"],
        "policies": exp["policies"],
    }
    (output / "policy.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    branch_fields = ["policy_id", "scenario_id", "observation", "site", "action", "total_cost", "utility", "eligible", "blockers"]
    with (output / "branches.tsv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=branch_fields, delimiter="\t")
        writer.writeheader()
        for pid, policy in exp["policies"].items():
            for sid, branch in policy["branches"].items():
                writer.writerow({"policy_id": pid, "scenario_id": sid, **branch, "eligible": str(policy["eligible"]).lower(), "blockers": ";".join(policy["blockers"])})
    profile_fields = ["policy_id", "profile", "expected_utility", "lower_tail_cvar", "regret"]
    with (output / "profiles.tsv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=profile_fields, delimiter="\t")
        writer.writeheader()
        for pid, policy in exp["policies"].items():
            for profile, metrics in policy["profiles"].items():
                writer.writerow({"policy_id": pid, "profile": profile, **metrics})
    (output / "manifest.json").write_text(json.dumps({"input_sha256": exp["hashes"], "rules_version": exp["rules_version"], "deterministic": True}, indent=2) + "\n", encoding="utf-8")
    (output / "audit.md").write_text("Distribution shift uses lower-tail CVaR and profile regret. Leave-one-profile-out checks stability. Future outcome and budget are hard gates. Human review remains required; this is not experimental proof.\n", encoding="utf-8")


def result(verifier, output: Path, data: Path) -> tuple[bool, list[str]]:
    return verifier.verify(output, data, TASK / "verifier_only/reference.json")


def main() -> int:
    verifier = load_verifier()
    controls = []
    with tempfile.TemporaryDirectory(prefix="l53-controls-") as temp:
        root = Path(temp)
        positive = root / "positive"
        write_reference(verifier, positive, TASK / "data")
        passed, errors = result(verifier, positive, TASK / "data")
        controls.append({"control_id": "positive-reference", "kind": "positive", "passed": passed, "errors": errors})

        nominal = root / "nominal"
        shutil.copytree(positive, nominal)
        report = json.loads((nominal / "policy.json").read_text(encoding="utf-8"))
        report["selected_policy"] = "P-NOMINAL"
        (nominal / "policy.json").write_text(json.dumps(report), encoding="utf-8")
        passed, errors = result(verifier, nominal, TASK / "data")
        controls.append({"control_id": "negative-nominal-winner", "kind": "negative", "passed": not passed, "errors": errors})

        invariant = root / "invariant"
        shutil.copytree(positive, invariant)
        rows = list(csv.DictReader((invariant / "profiles.tsv").open(encoding="utf-8", newline=""), delimiter="\t"))
        rows.reverse()
        with (invariant / "profiles.tsv").open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0]), delimiter="\t")
            writer.writeheader()
            writer.writerows(rows)
        passed, errors = result(verifier, invariant, TASK / "data")
        controls.append({"control_id": "invariance-row-order", "kind": "invariance", "passed": passed, "errors": errors})

        missing = root / "missing"
        shutil.copytree(positive, missing)
        manifest = json.loads((missing / "manifest.json").read_text(encoding="utf-8"))
        manifest["input_sha256"].pop("inputs/scenarios.json")
        (missing / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
        passed, errors = result(verifier, missing, TASK / "data")
        controls.append({"control_id": "insufficient-manifest", "kind": "insufficient_evidence", "passed": not passed, "errors": errors})

        exp = verifier.expected(TASK / "data")
        controls.append({"control_id": "adversarial-over-budget", "kind": "adversarial", "passed": not exp["policies"]["P-OVERRUN"]["eligible"] and exp["selected_policy"] == "P-ADAPT"})

        reordered_data = root / "data-reordered"
        shutil.copytree(TASK / "data", reordered_data)
        rules = json.loads((reordered_data / "rules.json").read_text(encoding="utf-8"))
        rules["weight_profiles"] = dict(reversed(list(rules["weight_profiles"].items())))
        (reordered_data / "rules.json").write_text(json.dumps(rules), encoding="utf-8")
        reordered = verifier.expected(reordered_data)
        controls.append({"control_id": "metamorphic-profile-order", "kind": "metamorphic", "passed": reordered["selected_policy"] == exp["selected_policy"] and reordered["policies"] == exp["policies"]})

    calibration = {"schema_version": "enterprise_control_calibration.v1", "task_id": TASK_ID, "status": "CALIBRATED" if all(row["passed"] for row in controls) else "FAILED", "controls": controls}
    (TASK / "controls/calibration_results.json").parent.mkdir(exist_ok=True)
    (TASK / "controls/calibration_results.json").write_text(json.dumps(calibration, indent=2) + "\n", encoding="utf-8")

    records = []
    for strategy in ("reference_solution", "simple_legal_baseline", "always_abstain", "template_or_keyword"):
        with tempfile.TemporaryDirectory(prefix="l53-baseline-") as temp:
            output = Path(temp) / "outputs"
            write_reference(verifier, output, TASK / "data")
            if strategy == "simple_legal_baseline":
                report = json.loads((output / "policy.json").read_text(encoding="utf-8"))
                report["selected_policy"] = "P-NOMINAL"
                (output / "policy.json").write_text(json.dumps(report), encoding="utf-8")
            elif strategy == "always_abstain":
                shutil.rmtree(output)
                output.mkdir()
            elif strategy == "template_or_keyword":
                report = json.loads((output / "policy.json").read_text(encoding="utf-8"))
                report["policies"] = {"P-ADAPT": report["policies"]["P-ADAPT"]}
                (output / "policy.json").write_text(json.dumps(report), encoding="utf-8")
            passed, errors = result(verifier, output, TASK / "data")
            records.append({"strategy": strategy, "status": "pass" if passed else "verifier_fail", "passed": passed, "error_count": len(errors), "failure_attribution": None if passed else ("artifact_completeness" if strategy == "always_abstain" else "method_choice"), "errors": errors})

    results = {"task_id": TASK_ID, "protocol_version": "enterprise-model-trial.v1", "status": "BASELINES_COMPLETE", "target_model_status": "NOT_RUN", "records": records}
    (TASK / "quality/model_trial_results.json").write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
    card_path = TASK / "quality/model_trial_card.json"
    card = json.loads(card_path.read_text(encoding="utf-8"))
    card.update({"status": "BASELINES_COMPLETE", "target_model_status": "NOT_RUN", "run_records": records})
    card_path.write_text(json.dumps(card, indent=2) + "\n", encoding="utf-8")
    plan_path = TASK / "quality/control_plan_card.json"
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    plan.update({"calibration_status": calibration["status"], "status": calibration["status"]})
    plan_path.write_text(json.dumps(plan, indent=2) + "\n", encoding="utf-8")
    sop_path = TASK / "quality/sop_card.json"
    sop = json.loads(sop_path.read_text(encoding="utf-8"))
    sop.update({"control_status": calibration["status"], "model_trial_status": "BASELINES_COMPLETE"})
    sop_path.write_text(json.dumps(sop, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"calibration": calibration, "baselines": results}, indent=2))
    return 0 if calibration["status"] == "CALIBRATED" and records[0]["passed"] and all(not row["passed"] for row in records[1:]) else 1


if __name__ == "__main__":
    raise SystemExit(main())
