#!/usr/bin/env python3
"""Materialize the next mined enterprise candidate: EB006 signal/noise audit."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TASK = ROOT / "benchmarks/eb006-signal-noise-004"

VERIFIER = '''from __future__ import annotations
import argparse
import csv
import hashlib
import json
from pathlib import Path

def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def expected(data: Path) -> dict:
    rows = list(csv.DictReader((data / "profiles.csv").open(newline="", encoding="utf-8")))
    rules = json.loads((data / "rules.json").read_text(encoding="utf-8"))
    treated = [row for row in rows if row["control_status"] == "treated"]
    controls = [row for row in rows if row["control_status"] == "control"]
    raw_effect = round(sum(float(row["raw_signal"]) for row in treated) / len(treated) - sum(float(row["raw_signal"]) for row in controls) / len(controls), 4)
    adjusted_effect = round(sum(float(row["adjusted_signal"]) for row in treated) / len(treated) - sum(float(row["adjusted_signal"]) for row in controls) / len(controls), 4)
    control_drift = round(max(float(row["adjusted_signal"]) for row in controls) - min(float(row["adjusted_signal"]) for row in controls), 4)
    identifiable = adjusted_effect >= rules["minimum_adjusted_effect"] and len(treated) >= rules["minimum_replicates"] and control_drift <= rules["maximum_control_drift"]
    return {"raw_effect": raw_effect, "adjusted_effect": adjusted_effect, "control_drift": control_drift, "replicate_count": len(treated), "identifiable": identifiable, "decision": "proceed_to_profile_review" if identifiable else "hold_for_human_review", "rules_version": rules["rules_version"], "input_sha256": {name: sha(data / name) for name in ("profiles.csv", "rules.json")}, "claim_boundary": {"mechanism_established": False, "human_review_required": True}}

def verify(submission: Path, data: Path, reference: Path) -> tuple[bool, list[str]]:
    exp, errors = expected(data), []
    for name in ("signal_noise_report.json", "replicate_diagnostics.tsv", "profile_review_gate.md"):
        if not (submission / name).is_file(): errors.append("missing artifact: " + name)
    if errors: return False, errors
    report = json.loads((submission / "signal_noise_report.json").read_text(encoding="utf-8"))
    for key in ("raw_effect", "adjusted_effect", "control_drift", "replicate_count", "identifiable", "decision", "rules_version"):
        if report.get(key) != exp[key]: errors.append("signal/noise report mismatch: " + key)
    if report.get("input_sha256") != exp["input_sha256"]: errors.append("signal/noise report provenance mismatch")
    if report.get("claim_boundary") != exp["claim_boundary"]: errors.append("signal/noise report claim boundary mismatch")
    diagnostics = (submission / "replicate_diagnostics.tsv").read_text(encoding="utf-8").lower()
    for phrase in ("perturbation", "plate", "replicate", "raw_signal", "adjusted_signal", "control_status"):
        if phrase not in diagnostics: errors.append("replicate diagnostics missing " + phrase)
    gate = (submission / "profile_review_gate.md").read_text(encoding="utf-8").lower()
    for phrase in ("signal", "technical noise", "human review", "mechanism"):
        if phrase not in gate: errors.append("profile review gate missing " + phrase)
    return not errors, errors

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--submission", type=Path, required=True)
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--reference", type=Path, required=True)
    args = parser.parse_args()
    ok, errors = verify(args.submission, args.data, args.reference)
    print(json.dumps({"passed": ok, "errors": errors}))
    raise SystemExit(0 if ok else 1)
'''

def write(path: Path, value: str | dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(value, dict):
        path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    else:
        path.write_text(value, encoding="utf-8")

def main() -> None:
    write(TASK / "task.yaml", """id: eb006-signal-noise-004
version: "0.1.0"
status: ready_for_calibration
title: "Perturbation signal versus technical noise"
domain: biomedical_enterprise
agent_visible_inputs:
  - path: data/
    format: CSV and JSON
constraints:
  network: off
  provenance:
    record_input_checksum: true
    deterministic_output: true
required_outputs:
  - {id: signal_noise_report, path: outputs/signal_noise_report.json, required_fields: [raw_effect, adjusted_effect, control_drift, replicate_count, identifiable, decision, rules_version, input_sha256, claim_boundary]}
  - {id: replicate_diagnostics, path: outputs/replicate_diagnostics.tsv, required_fields: [perturbation, plate, replicate, raw_signal, adjusted_signal, control_status]}
  - {id: profile_review_gate, path: outputs/profile_review_gate.md, required_fields: [signal_result, technical_noise_result, human_review_decision, claim_boundary]}
hidden_truth:
  path: verifier_only/reference.json
  status: verifier_only
""")
    write(TASK / "scenario-card.yaml", """scenario_id: eb006-signal-noise-004
status: ready
source_scenarios: [EB006]
domain: biomedical_enterprise
scientific_decision: decide whether a perturbation phenotype survives technical-noise checks before profile review
scientific_judgments:
  - replicate_and_plate_signal_reconciliation
  - adjusted_effect_identifiability
  - analytical_claim_boundary
workflow_handoffs:
  - from: images_and_metadata
    to: signal_noise_diagnostics
    artifact: outputs/replicate_diagnostics.tsv
    invariant: preserve replicate and plate provenance
  - from: signal_noise_diagnostics
    to: profile_review
    artifact: outputs/profile_review_gate.md
    invariant: residual signal is not mechanism evidence
release_gates:
  scientific_reality: pass
  observability: pass
  verifiability: pass
  naive_resistance: pass
""")
    write(TASK / "instruction.md", """# Perturbation signal versus technical noise

Compare raw and nuisance-adjusted perturbation signal, preserve replicate-level provenance, and stop when the biological effect is not identifiable. A residual phenotype signal supports analytical triage only; it does not establish mechanism, target engagement, or efficacy.

Write exactly these files under outputs/:
- outputs/signal_noise_report.json with this contract: raw_effect, adjusted_effect, and control_drift are numbers; replicate_count is an integer; identifiable is a JSON boolean; decision is exactly proceed_to_profile_review or hold_for_human_review; rules_version is a string; input_sha256 is keyed by profiles.csv and rules.json; claim_boundary contains mechanism_established: false and human_review_required: true.
- outputs/replicate_diagnostics.tsv: columns perturbation, plate, replicate, raw_signal, adjusted_signal, and control_status.
- outputs/profile_review_gate.md: signal result, technical noise result, human review decision, and a bounded statement about mechanism, target engagement, and efficacy.
""")
    write(TASK / "expected_artifacts.md", """# Expected artifacts

Synthetic offline fixture. A residual signal supports profile triage only; it is not evidence of mechanism, target engagement, or efficacy.
""")
    write(TASK / "data/profiles.csv", """perturbation,plate,replicate,raw_signal,adjusted_signal,control_status
P-1,PLATE-1,1,1.20,1.05,treated
P-1,PLATE-2,2,1.18,1.04,treated
P-1,PLATE-3,1,1.00,1.00,control
P-1,PLATE-4,2,0.98,0.99,control
""")
    write(TASK / "data/rules.json", {"rules_version": "signal-noise-v1", "minimum_adjusted_effect": 0.03, "minimum_replicates": 2, "maximum_control_drift": 0.02})
    write(TASK / "verifier_only/reference.json", {"decision": "proceed_to_profile_review"})
    write(TASK / "verifier.py", VERIFIER)
    write(TASK / "tests/test_verifier.py", """import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("verifier", ROOT / "verifier.py")
verifier = importlib.util.module_from_spec(spec)
assert spec.loader
spec.loader.exec_module(verifier)

def test_expected_is_deterministic():
    assert verifier.expected(ROOT / "data") == verifier.expected(ROOT / "data")

def test_missing_submission_fails(tmp_path):
    ok, errors = verifier.verify(tmp_path, ROOT / "data", ROOT / "verifier_only/reference.json")
    assert not ok and errors
""")
    quality = TASK / "quality"
    cards = {
        "candidate_set_card.json": {"candidate_set_id": "CSET-EB006-SIGNAL-NOISE-004-001", "source_benchmark_id": "EB006", "candidates": [{"candidate_id": "eb006-signal-noise-004", "selection_status": "MATERIALIZED", "semantic_axes": ["method_choice", "data_multimodal_join", "stopping_rule"]}], "selection_gate": {"minimum_candidates": 3, "maximum_candidates": 5, "require_two_semantic_differences": True, "require_independent_review": True}, "status": "REVIEW_REQUIRED"},
        "enterprise_value_card.json": {"enterprise_value_card_id": "VALUE-EB006-SIGNAL-NOISE-004-001", "task_id": "eb006-signal-noise-004", "enterprise_reality": {"evidence_class": "B", "named_role": "image_analysis_or_phenomics_scientist", "decision": "decide whether a perturbation phenotype survives technical-noise checks before profile review", "downstream_action": "signal_noise_diagnostics->profile_review", "error_consequence": "technical variation can be mistaken for a biological hit", "human_owner": "domain_reviewer"}, "status": "REVIEW_REQUIRED"},
        "difficulty_card.json": {"difficulty_card_id": "DIFF-EB006-SIGNAL-NOISE-004-001", "task_id": "eb006-signal-noise-004", "difficulty_hypothesis": {"reasoning_chain": ["join replicate and plate evidence", "compare raw versus adjusted signal", "preserve uncertainty", "issue bounded handoff"], "target_failure_mechanism": "fluent shortcut mistakes plate noise for phenotype"}, "shortcut_probes": ["company-name matching", "always-proceed", "always-abstain", "template copying"], "status": "DRAFT"},
        "training_value_card.json": {"training_value_card_id": "TRAIN-EB006-SIGNAL-NOISE-004-001", "task_id": "eb006-signal-noise-004", "capability_targets": ["evidence reconciliation", "replicate reasoning", "claim boundary", "artifact completeness"], "error_labels": ["input_understanding", "method_choice", "calculation_or_tool", "claim_overreach", "delivery_failure"], "training_use": "EVAL_ONLY_UNTIL_CALIBRATED", "status": "REVIEW_REQUIRED"},
        "control_plan_card.json": {"control_plan_id": "CONTROL-EB006-SIGNAL-NOISE-004-001", "task_id": "eb006-signal-noise-004", "controls": [{"control_id": "positive-reference", "kind": "positive"}, {"control_id": "negative-noise-drift", "kind": "negative"}, {"control_id": "invariance-row-order", "kind": "invariance"}, {"control_id": "insufficient-controls", "kind": "insufficient_evidence"}], "single_factor_policy": True, "calibration_status": "NOT_RUN", "status": "REVIEW_REQUIRED"},
        "model_trial_card.json": {"model_trial_card_id": "TRIAL-EB006-SIGNAL-NOISE-004-001", "task_id": "eb006-signal-noise-004", "protocol_version": "enterprise-model-trial.v1", "strategies": ["reference_solution", "simple_legal_baseline", "always_abstain", "template_or_keyword", "target_model"], "target_model_status": "NOT_RUN", "status": "NOT_RUN", "run_records": []},
        "sop_card.json": {"schema_version": "enterprise_harbor_sop_card.v1", "task_id": "eb006-signal-noise-004", "sop_version": "enterprise-harbor-sop-v1.1", "source_status": "REVIEW_REQUIRED", "contract_status": "CONTRACT_ONLY", "control_status": "NOT_RUN", "model_trial_status": "NOT_RUN", "target_model_failure_policy": "infrastructure_failures_are_not_difficulty_evidence", "independent_verifier_status": "NOT_RUN", "release_status": "BLOCKED", "release_blockers": ["source/license/privacy review", "independent verifier contract audit", "control calibration", "author-side baselines", "target-model trial"]}
    }
    for name, value in cards.items():
        write(quality / name, value)
    write(TASK / "controls/calibration_results.json", {"schema_version": "enterprise_control_calibration.v1", "status": "NOT_RUN", "tasks": [{"task_id": "eb006-signal-noise-004", "status": "NOT_RUN"}]})
    print(TASK)

if __name__ == "__main__":
    main()
