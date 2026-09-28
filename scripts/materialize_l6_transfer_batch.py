#!/usr/bin/env python3
"""Materialize cross-domain held-outs for the L6 evidence-routing module."""

from __future__ import annotations

import json
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "benchmarks/eb013-evidence-budget-routing-002"


SPECS = {
    "eb010-stop-uncertainty-002": {
        "title": "Adaptive stop-rule evidence routing under uncertainty",
        "role": "experimental_design_scientist",
        "decision": "select a prospective monitoring policy before deciding continue, stop, or review",
        "error": "a fixed follow-up can hide plateau or disagreement and waste another experimental batch",
        "claim": "A simulated stop policy is a planning aid, not proof of real-world improvement.",
        "rules_version": "l6.2-stop-uncertainty-v1",
        "critical_thresholds": {"improvement": 0.25, "model_disagreement": 0.25},
        "initial_uncertainty": {"improvement": 0.80, "model_disagreement": 0.70, "replication": 0.45},
        "winner_stage1": "S-UNCERTAINTY",
        "winner_policy": {"plateau": "S-REPLICATE", "discordant": "S-RECONCILE"},
        "stage1": [
            {"request_id": "S-UNCERTAINTY", "stage": 1, "cost": 3.0, "correlation_group": "G0", "covers": {"improvement": 0.25, "model_disagreement": 0.20}, "outcomes": {"plateau": {"improvement": 0.20}, "discordant": {"model_disagreement": 0.15}}, "status": "current", "future_outcome": False, "dependency_ids": [], "nominal_value": 0.90},
            {"request_id": "S-GAIN", "stage": 1, "cost": 2.0, "correlation_group": "G1", "covers": {"improvement": 0.45, "model_disagreement": 0.05}, "outcomes": {"gain": {}, "no_gain": {}}, "status": "current", "future_outcome": False, "dependency_ids": [], "nominal_value": 1.20},
            {"request_id": "S-CHEAP", "stage": 1, "cost": 1.0, "correlation_group": "G2", "covers": {"improvement": 0.20, "model_disagreement": 0.10}, "outcomes": {"screen_positive": {}, "screen_negative": {}}, "status": "current", "future_outcome": False, "dependency_ids": [], "nominal_value": 1.35},
        ],
        "stage2": [
            {"request_id": "S-REPLICATE", "stage": 2, "cost": 2.0, "correlation_group": "G3", "covers": {"improvement": 0.35, "model_disagreement": 0.35}, "allowed_observations": ["plateau"], "status": "current", "future_outcome": False, "dependency_ids": ["S-UNCERTAINTY"], "nominal_value": 0.82},
            {"request_id": "S-RECONCILE", "stage": 2, "cost": 2.0, "correlation_group": "G4", "covers": {"improvement": 0.40, "model_disagreement": 0.40}, "allowed_observations": ["discordant"], "status": "current", "future_outcome": False, "dependency_ids": ["S-UNCERTAINTY"], "nominal_value": 0.80},
            {"request_id": "S-FIXED", "stage": 2, "cost": 1.0, "correlation_group": "G5", "covers": {"improvement": 0.30, "model_disagreement": 0.30}, "allowed_observations": ["plateau", "discordant"], "status": "current", "future_outcome": False, "dependency_ids": ["S-UNCERTAINTY"], "nominal_value": 1.05},
            {"request_id": "S-GAIN-CHECK", "stage": 2, "cost": 2.0, "correlation_group": "G6", "covers": {"model_disagreement": 0.30}, "allowed_observations": ["gain", "no_gain"], "status": "current", "future_outcome": False, "dependency_ids": ["S-GAIN"], "nominal_value": 0.91},
            {"request_id": "S-POST", "stage": 2, "cost": 1.0, "correlation_group": "G7", "covers": {"improvement": 0.80, "model_disagreement": 0.70}, "allowed_observations": ["plateau", "discordant"], "status": "current", "future_outcome": True, "dependency_ids": [], "nominal_value": 1.50},
        ],
        "audit_terms": ["observation", "stage 1", "stage 2", "dependency", "budget", "future", "human review", "not experimental proof"],
    },
    "eb011-reproduction-manifest-001": {
        "title": "Adaptive reproduction remediation under manifest drift",
        "role": "computational_chemist_or_method_auditor",
        "decision": "select a diagnostic rerun and observation-conditioned remediation policy",
        "error": "a fixed remediation can conceal topology or parameter drift and make reported errors unauditable",
        "claim": "Reproduction status does not validate the underlying biological claim.",
        "rules_version": "l6.2-reproduction-remediation-v1",
        "critical_thresholds": {"energy_error": 0.25, "configuration_drift": 0.25},
        "initial_uncertainty": {"energy_error": 0.90, "configuration_drift": 0.75, "nondeterminism": 0.40},
        "winner_stage1": "D-MANIFEST",
        "winner_policy": {"topology_mismatch": "D-REBUILD", "parameter_drift": "D-PIN"},
        "stage1": [
            {"request_id": "D-MANIFEST", "stage": 1, "cost": 2.0, "correlation_group": "G0", "covers": {"energy_error": 0.25, "configuration_drift": 0.30}, "outcomes": {"topology_mismatch": {"energy_error": 0.15}, "parameter_drift": {"configuration_drift": 0.15}}, "status": "current", "future_outcome": False, "dependency_ids": [], "nominal_value": 0.88},
            {"request_id": "D-NOMINAL", "stage": 1, "cost": 1.0, "correlation_group": "G1", "covers": {"energy_error": 0.50, "configuration_drift": 0.05}, "outcomes": {"reported_match": {}, "reported_mismatch": {}}, "status": "current", "future_outcome": False, "dependency_ids": [], "nominal_value": 1.25},
            {"request_id": "D-ARCHIVE", "stage": 1, "cost": 1.0, "correlation_group": "G2", "covers": {"energy_error": 0.55, "configuration_drift": 0.40}, "outcomes": {"legacy_match": {}, "legacy_mismatch": {}}, "status": "archived", "future_outcome": False, "dependency_ids": [], "nominal_value": 1.40},
        ],
        "stage2": [
            {"request_id": "D-REBUILD", "stage": 2, "cost": 3.0, "correlation_group": "G3", "covers": {"energy_error": 0.40, "configuration_drift": 0.35}, "allowed_observations": ["topology_mismatch"], "status": "current", "future_outcome": False, "dependency_ids": ["D-MANIFEST"], "nominal_value": 0.85},
            {"request_id": "D-PIN", "stage": 2, "cost": 2.0, "correlation_group": "G4", "covers": {"energy_error": 0.55, "configuration_drift": 0.35}, "allowed_observations": ["parameter_drift"], "status": "current", "future_outcome": False, "dependency_ids": ["D-MANIFEST"], "nominal_value": 0.83},
            {"request_id": "D-CROSSCHECK", "stage": 2, "cost": 2.0, "correlation_group": "G5", "covers": {"energy_error": 0.35, "configuration_drift": 0.30}, "allowed_observations": ["topology_mismatch", "parameter_drift"], "status": "current", "future_outcome": False, "dependency_ids": ["D-MANIFEST"], "nominal_value": 1.10},
            {"request_id": "D-REPORT", "stage": 2, "cost": 1.0, "correlation_group": "G6", "covers": {"configuration_drift": 0.30}, "allowed_observations": ["reported_match", "reported_mismatch"], "status": "current", "future_outcome": False, "dependency_ids": ["D-NOMINAL"], "nominal_value": 1.00},
            {"request_id": "D-POST", "stage": 2, "cost": 1.0, "correlation_group": "G7", "covers": {"energy_error": 0.90, "configuration_drift": 0.75}, "allowed_observations": ["topology_mismatch", "parameter_drift"], "status": "current", "future_outcome": True, "dependency_ids": [], "nominal_value": 1.60},
        ],
        "audit_terms": ["observation", "stage 1", "stage 2", "dependency", "budget", "future", "human review", "not experimental proof"],
    },
}


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def replace_tree(task: Path, task_id: str, title: str) -> None:
    for path in task.rglob("*"):
        if not path.is_file() or path.suffix == ".pyc":
            continue
        text = path.read_text(encoding="utf-8")
        text = text.replace("eb013-evidence-budget-routing-002", task_id)
        text = text.replace("Two-stage evidence budget routing under observed uncertainty", title)
        text = text.replace("L6-TRANCHE-012", "L6.2-TRANCHE-014")
        path.write_text(text, encoding="utf-8")


def materialize(task_id: str, spec: dict[str, object]) -> None:
    task = ROOT / "benchmarks" / task_id
    if task.exists():
        raise FileExistsError(f"refusing to overwrite existing task: {task}")
    shutil.copytree(SOURCE, task, ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "sop_preflight.json", "calibration_results.json"))
    replace_tree(task, task_id, str(spec["title"]))

    scenario_path = task / "scenario-card.yaml"
    scenario = scenario_path.read_text(encoding="utf-8")
    judgments = (
        "scientific_judgments:\n"
        "  - distinguish the declared observation states before choosing a follow-up\n"
        "  - minimize worst-case critical residual rather than nominal request value\n"
        "  - preserve prospective evidence and human-review boundaries\n"
    )
    scenario = scenario.replace("difficulty_modules:\n", judgments + "difficulty_modules:\n", 1)
    scenario_path.write_text(scenario, encoding="utf-8")

    rules = {
        "rules_version": spec["rules_version"],
        "stage1_budget": 3.0,
        "total_budget": 5.0,
        "critical_thresholds": spec["critical_thresholds"],
        "initial_uncertainty": spec["initial_uncertainty"],
        "objective": "minimize worst-case maximum critical residual, then worst-case cost, then lexical policy",
        "correlation_rule": "within one correlation group only the largest reduction per uncertainty counts",
        "required_scope": "current",
        "required_network": "off",
        "claim_boundary": spec["claim"],
    }
    write_json(task / "data/rules.json", rules)
    write_json(task / "data/inputs/stage1_requests.json", {"requests": spec["stage1"]})
    write_json(task / "data/inputs/stage2_requests.json", {"requests": spec["stage2"]})
    write_json(task / "data/inputs/run_manifest.json", {
        "schema_version": "two-stage-evidence-manifest.v1",
        "network": "off",
        "decision_date": "2026-09-22",
        "input_files": ["inputs/stage1_requests.json", "inputs/stage2_requests.json", "rules.json"],
        "future_outcome_visible": False,
    })
    write_json(task / "verifier_only/reference.json", {
        "selected_stage1_request_id": spec["winner_stage1"],
        "selected_stage2_policy": spec["winner_policy"],
        "rules_version": spec["rules_version"],
        "status": "verifier_only",
    })
    (task / "instruction.md").write_text(f'''# {spec["title"]}

Use only the supplied nested JSON bundle. Choose a stage-1 request before observing its declared outcome. After that observation, choose exactly one dependency-valid stage-2 request allowed for that observation. The stage-1 cost plus the largest stage-2 cost must remain within the total budget. Ignore archived requests, future outcomes, and requests with missing prerequisites.

The trial workspace is not a git repository. Do not run git commands, inspect parent directories, or search outside `data/`; use shell commands only to read the supplied files and write the five required artifacts.

For every observation state, subtract the stage-1 and selected stage-2 reductions plus the declared observation adjustment. Within one correlation group, only the largest reduction per uncertainty counts. A policy is eligible only if every observation state reaches every critical threshold. Select the eligible policy by lowest worst-case maximum critical residual, then lowest worst-case cost, then lexical stage-1 request ID and stage-2 mapping. {spec["claim"]}

Write exactly `outputs/plan.json`, `outputs/route.tsv`, `outputs/decision.json`, `outputs/provenance.json`, and `outputs/audit.md`. Include `stage1_request_id`, `stage2_policy`, `worst_case_max_critical_residual`, `worst_case_cost`, and complete `policies`. `route.tsv` must contain one row per policy state. Record all input SHA-256 values, the rules version, `network="off"`, and `deterministic=true`. The audit must explain observation gating, stages, dependencies, budget, future-outcome exclusion, human review, and why the result is not experimental proof.
''', encoding="utf-8")

    difficulty = json.loads((task / "quality/difficulty_card.json").read_text(encoding="utf-8"))
    difficulty.update({
        "primary_module": "math_minimax_evidence_route_selection",
        "secondary_modules": ["horizon_two_stage_acquisition", "judgment_evidence_route_selection"],
        "supporting_modules": ["math_correlation_adjusted_reduction", "retrieval_provenance_temporal_boundary"],
        "held_out_variants": ["observation label swap", "stage-2 budget contraction", "dependency repair", "critical threshold shift"],
        "decision_flip_controls": ["fixed-stage2 shortcut", "future nominal winner", "dominated threshold-crossing policy", "missing prerequisite"],
        "status": "REVIEW_REQUIRED",
    })
    write_json(task / "quality/difficulty_card.json", difficulty)
    enterprise = json.loads((task / "quality/enterprise_value_card.json").read_text(encoding="utf-8"))
    enterprise["enterprise_reality"] = {"decision": spec["decision"], "error_consequence": spec["error"], "human_owner": spec["role"]}
    write_json(task / "quality/enterprise_value_card.json", enterprise)
    for filename, key in (("model_trial_card.json", "run_records"), ("model_trial_results.json", "records")):
        path = task / "quality" / filename
        payload = json.loads(path.read_text(encoding="utf-8"))
        payload.update({"target_model_status": "NOT_RUN", "status": "NOT_RUN", key: []})
        write_json(path, payload)
    sop_path = task / "quality/sop_card.json"
    sop = json.loads(sop_path.read_text(encoding="utf-8"))
    sop.update({"control_status": "NOT_RUN", "model_trial_status": "NOT_RUN", "release_status": "BLOCKED", "release_blockers": ["controls", "baselines", "target-model trial", "fixed-container replay", "practitioner review"], "status": "REVIEW_REQUIRED"})
    write_json(sop_path, sop)
    control_path = task / "quality/control_plan_card.json"
    control = json.loads(control_path.read_text(encoding="utf-8"))
    control.update({"calibration_status": "NOT_RUN", "status": "REVIEW_REQUIRED"})
    write_json(control_path, control)

    tests = f'''import importlib.util\nfrom pathlib import Path\nTASK=Path(__file__).resolve().parents[1]\nspec=importlib.util.spec_from_file_location("verifier",TASK/"verifier.py"); verifier=importlib.util.module_from_spec(spec); assert spec and spec.loader; spec.loader.exec_module(verifier)\ndef test_oracle_selects_declared_adaptive_policy():\n exp=verifier.expected(TASK/"data"); assert exp["selected_stage1_request_id"]=={spec["winner_stage1"]!r}; assert exp["selected_stage2_policy"]=={spec["winner_policy"]!r}\ndef test_oracle_is_deterministic():\n assert verifier.expected(TASK/"data")==verifier.expected(TASK/"data")\ndef test_winner_is_not_a_fixed_stage2_shortcut():\n exp=verifier.expected(TASK/"data"); assert len(set(exp["selected_stage2_policy"].values()))>1\n'''
    (task / "tests/test_verifier.py").write_text(tests, encoding="utf-8")

    source = task_id.split("-", 1)[0].upper()
    contract = (ROOT / "candidate_pools/enterprise-v1/contracts/eb013-evidence-budget-routing-002.toml").read_text(encoding="utf-8")
    contract = contract.replace("eb013-evidence-budget-routing-002", task_id).replace("Two-stage evidence budget routing under observed uncertainty", str(spec["title"])).replace("L6-TRANCHE-012", "L6.2-TRANCHE-014")
    (ROOT / f"candidate_pools/enterprise-v1/contracts/{task_id}.toml").write_text(contract, encoding="utf-8")

    brief_path = ROOT / f"candidate_pools/enterprise-v1/question_briefs/{task_id}.json"
    brief = json.loads(brief_path.read_text(encoding="utf-8"))
    brief.update({
        "status": "MATERIALIZED_CALIBRATION_READY",
        "required_artifacts": ["plan.json", "route.tsv", "decision.json", "provenance.json", "audit.md"],
        "reusable_modules": ["math_minimax_evidence_route_selection", "horizon_two_stage_acquisition", "judgment_evidence_route_selection"],
        "claim_boundary": spec["claim"],
        "release_blockers": ["target-model trial", "fixed-container replay", "practitioner review"],
    })
    write_json(brief_path, brief)


def main() -> None:
    if not SOURCE.is_dir():
        raise FileNotFoundError(f"source task missing: {SOURCE}")
    for task_id, spec in SPECS.items():
        materialize(task_id, spec)
    print(json.dumps({"materialized": sorted(SPECS), "tranche": "TRANCHE-014"}, indent=2))


if __name__ == "__main__":
    main()
