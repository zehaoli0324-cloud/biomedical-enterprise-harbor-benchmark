#!/usr/bin/env python3
"""Fail-closed SOP preflight for an enterprise Harbor task package.

The check is intentionally independent of any model provider.  A structural
pass means that a task is ready for calibration/preflight only; it never
upgrades a task to READY_FOR_HARBOR.  Target-model infrastructure failures are
reported as blockers and are never counted as model difficulty evidence.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


REQUIRED_FILES = (
    "task.yaml",
    "instruction.md",
    "verifier.py",
    "verifier_only/reference.json",
)
REQUIRED_STRATEGIES = {
    "reference_solution",
    "simple_legal_baseline",
    "always_abstain",
    "template_or_keyword",
    "target_model",
}
REQUIRED_CONTROL_KINDS = {"positive", "negative", "invariance", "insufficient_evidence"}
INFRA_FAILURES = {
    "TIMEOUT_INFRASTRUCTURE",
    "agent_not_run",
    "infrastructure_adapter_timeout",
    "provider_error",
}


def _load_json(path: Path) -> dict[str, Any] | None:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return value if isinstance(value, dict) else None


def _check(checks: list[dict[str, Any]], name: str, passed: bool, detail: str) -> None:
    checks.append({"check": name, "status": "PASS" if passed else "BLOCKER", "detail": detail})


def _required_output_paths(task_text: str) -> list[str]:
    paths: list[str] = []
    in_outputs = False
    for raw in task_text.splitlines():
        line = raw.strip()
        if line == "required_outputs:":
            in_outputs = True
            continue
        if in_outputs and line and not line.startswith("-"):
            break
        if in_outputs and "path:" in line:
            value = line.split("path:", 1)[1].strip().rstrip("}").strip().strip('"').strip("'")
            value = value.split(", required_fields:", 1)[0].strip()
            if value:
                paths.append(value.rstrip(","))
    return paths


def evaluate(package: Path) -> dict[str, Any]:
    package = package.resolve()
    checks: list[dict[str, Any]] = []
    pretrial_blockers: list[str] = []
    release_blockers: list[str] = []

    for relative in REQUIRED_FILES:
        present = (package / relative).is_file() and (package / relative).stat().st_size > 0
        _check(checks, f"file:{relative}", present, "present" if present else "missing_or_empty")
        if not present:
            pretrial_blockers.append(f"file:{relative}")

    data_dir = package / "data"
    tests_dir = package / "tests"
    _check(checks, "data_nonempty", data_dir.is_dir() and any(data_dir.iterdir()), str(data_dir))
    _check(checks, "tests_present", tests_dir.is_dir() and any(tests_dir.iterdir()), str(tests_dir))
    if not data_dir.is_dir() or not any(data_dir.iterdir()):
        pretrial_blockers.append("data_nonempty")
    if not tests_dir.is_dir() or not any(tests_dir.iterdir()):
        pretrial_blockers.append("tests_present")

    task_path = package / "task.yaml"
    task_text = task_path.read_text(encoding="utf-8", errors="replace") if task_path.is_file() else ""
    instruction_text = (package / "instruction.md").read_text(encoding="utf-8", errors="replace") if (package / "instruction.md").is_file() else ""
    outputs = _required_output_paths(task_text)
    _check(checks, "required_outputs_declared", bool(outputs), str(outputs))
    if not outputs:
        pretrial_blockers.append("required_outputs_declared")
    for output in outputs:
        declared = output in instruction_text
        under_outputs = output.startswith("outputs/")
        _check(checks, f"output:{output}", declared and under_outputs, "instruction_reference_and_outputs_path")
        if not declared or not under_outputs:
            pretrial_blockers.append(f"output:{output}")
    for hidden in ("verifier_only/", "verifier.py", "tests/"):
        _check(checks, f"hidden_boundary:{hidden}", hidden not in instruction_text, "not_named_in_instruction" if hidden not in instruction_text else "hidden_path_leak")
        if hidden in instruction_text:
            pretrial_blockers.append(f"hidden_boundary:{hidden}")

    quality = package / "quality"
    controls = _load_json(quality / "control_plan_card.json")
    control_kinds = {item.get("kind") for item in (controls or {}).get("controls", []) if isinstance(item, dict)}
    controls_ok = REQUIRED_CONTROL_KINDS <= control_kinds and (controls or {}).get("calibration_status") in {"CALIBRATED", "PASS", "NOT_RUN", "REVIEW_REQUIRED"}
    _check(checks, "four_control_kinds", controls_ok, ",".join(sorted(control_kinds)))
    if not controls_ok:
        pretrial_blockers.append("four_control_kinds")

    trial_card = _load_json(quality / "model_trial_card.json")
    strategies = set((trial_card or {}).get("strategies", []))
    strategies_ok = REQUIRED_STRATEGIES <= strategies
    _check(checks, "five_trial_strategies", strategies_ok, ",".join(sorted(strategies)))
    if not strategies_ok:
        pretrial_blockers.append("five_trial_strategies")

    trial_results = _load_json(quality / "model_trial_results.json")
    records = (trial_results or {}).get("records") or (trial_card or {}).get("run_records") or []
    recorded_strategies = {item.get("strategy") for item in records if isinstance(item, dict)}
    baselines_ok = {"reference_solution", "simple_legal_baseline", "always_abstain", "template_or_keyword"} <= recorded_strategies
    _check(checks, "baseline_records_present", baselines_ok, ",".join(sorted(recorded_strategies)))
    if not baselines_ok:
        pretrial_blockers.append("baseline_records_present")
    target_status = (trial_results or {}).get("target_model_status") or (trial_card or {}).get("target_model_status") or "NOT_RUN"
    infra_blocked = target_status in INFRA_FAILURES or "TIMEOUT" in str(target_status).upper()
    card_status = (trial_card or {}).get("status")
    results_status = (trial_results or {}).get("status")
    attribution_ok = not infra_blocked or (card_status != "COMPLETE" and results_status != "COMPLETE")
    _check(checks, "target_model_status_attributed", attribution_ok, target_status)
    if not attribution_ok:
        pretrial_blockers.append("target_model_status_attributed")
    if infra_blocked:
        release_blockers.append("target_model_infrastructure")
    if target_status == "NOT_RUN":
        release_blockers.append("target_model_not_run")

    sop_card_path = quality / "sop_card.json"
    sop_card = _load_json(sop_card_path)
    _check(checks, "sop_card_present", sop_card is not None, str(sop_card_path))
    if sop_card is None:
        pretrial_blockers.append("sop_card_present")
    else:
        identity_ok = sop_card.get("task_id") == package.name and sop_card.get("schema_version") == "enterprise_harbor_sop_card.v1"
        _check(checks, "sop_card_identity", identity_ok, str(sop_card.get("schema_version")))
        if not identity_ok:
            pretrial_blockers.append("sop_card_identity")
        for field in ("source_status", "contract_status", "control_status", "model_trial_status", "independent_verifier_status", "release_status"):
            if not sop_card.get(field):
                pretrial_blockers.append(f"sop_card_field:{field}")
        audit = _load_json(quality / "independent_verifier_audit.json")
        audit_ok = (audit or {}).get("status") == "PASS" and (audit or {}).get("review_status") == "pass"
        _check(checks, "independent_verifier_audit", audit_ok, str((audit or {}).get("status", "missing")))
        if not audit_ok:
            pretrial_blockers.append("independent_verifier_audit")

    return {
        "schema_version": "enterprise_harbor_sop_preflight.v1",
        "task_id": (task_path.read_text(encoding="utf-8", errors="ignore").split("id:", 1)[1].splitlines()[0].strip() if "id:" in task_text else package.name),
        "package": str(package),
        "status": "BLOCKED" if pretrial_blockers else "PASS",
        "checks": checks,
        "blockers": sorted(set(pretrial_blockers)),
        "release_status": "BLOCKED" if release_blockers or pretrial_blockers else "REVIEW_REQUIRED",
        "release_blockers": sorted(set(release_blockers + pretrial_blockers)),
        "target_model_status": target_status,
        "target_model_infra_not_difficulty": infra_blocked,
        "release_permitted": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("package", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = evaluate(args.package)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "blockers": result["blockers"], "release_status": result["release_status"], "release_blockers": result["release_blockers"]}, ensure_ascii=False))
    return 0 if result["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
