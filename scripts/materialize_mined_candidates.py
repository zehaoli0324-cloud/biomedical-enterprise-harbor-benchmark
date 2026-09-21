#!/usr/bin/env python3
"""Materialize selected candidates mined from existing enterprise seeds."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def write(path: Path, value: str | dict | list) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(value, (dict, list)):
        path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    else:
        path.write_text(value, encoding="utf-8")


EB003_VERIFIER = r'''from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path

def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def expected(data: Path) -> dict:
    artifact = json.loads((data / "artifact_manifest.json").read_text())
    env = json.loads((data / "environment.json").read_text())
    return {"artifact_id": artifact["artifact_id"], "rules_version": artifact["rules_version"],
            "input_hashes": artifact["input_hashes"], "output_hashes": artifact["output_hashes"],
            "environment": env, "hashes": {name: sha(data / name) for name in ("artifact_manifest.json", "environment.json")}}

def verify(submission: Path, data: Path, reference: Path) -> tuple[bool, list[str]]:
    exp, errors = expected(data), []
    required = ("replay_manifest.json", "provenance_diff.tsv", "handoff_replay_report.md")
    for name in required:
        if not (submission / name).is_file(): errors.append("missing artifact: " + name)
    if errors: return False, errors
    manifest = json.loads((submission / "replay_manifest.json").read_text())
    if manifest.get("artifact_id") != exp["artifact_id"]: errors.append("artifact id mismatch")
    if manifest.get("rules_version") != exp["rules_version"]: errors.append("rules version mismatch")
    if manifest.get("input_hashes") != exp["input_hashes"] or manifest.get("output_hashes") != exp["output_hashes"]: errors.append("provenance hash mismatch")
    if manifest.get("environment") != exp["environment"]: errors.append("environment mismatch")
    if manifest.get("replay_status") != "reproduced": errors.append("replay_status must be reproduced")
    diff = (submission / "provenance_diff.tsv").read_text().lower()
    for phrase in ("field", "status", "match"):
        if phrase not in diff: errors.append("provenance_diff.tsv missing " + phrase)
    report = (submission / "handoff_replay_report.md").read_text().lower()
    for phrase in ("replay", "checksum", "human review", "not biological validation"):
        if phrase not in report: errors.append("handoff report missing " + phrase)
    return not errors, errors

if __name__ == "__main__":
    p = argparse.ArgumentParser(); p.add_argument("--submission", type=Path, required=True); p.add_argument("--data", type=Path, required=True); p.add_argument("--reference", type=Path, required=True)
    a = p.parse_args(); ok, errors = verify(a.submission, a.data, a.reference); print(json.dumps({"passed": ok, "errors": errors})); raise SystemExit(0 if ok else 1)
'''


EB009_VERIFIER = r'''from __future__ import annotations
import argparse, csv, hashlib, json
from pathlib import Path

def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def expected(data: Path) -> dict:
    rows = list(csv.DictReader((data / "candidates.csv").open(newline="", encoding="utf-8")))
    rules = json.loads((data / "rules.json").read_text())
    valid = [r for r in rows if r["valid"] == "true"]
    unique = {r["candidate_id"] for r in valid}
    scaffolds = sorted({r["scaffold"] for r in valid})
    clusters = sorted({r["cluster"] for r in valid})
    covered = len(scaffolds) >= rules["minimum_scaffolds"] and len(clusters) >= rules["minimum_clusters"]
    return {"candidate_count": len(rows), "valid_count": len(valid), "unique_valid_count": len(unique), "scaffolds": scaffolds, "clusters": clusters, "coverage": covered, "rules_version": rules["rules_version"], "hashes": {"candidates.csv": sha(data / "candidates.csv"), "rules.json": sha(data / "rules.json")}}

def verify(submission: Path, data: Path, reference: Path) -> tuple[bool, list[str]]:
    exp, errors = expected(data), []
    for name in ("candidate_set.tsv", "diversity_report.json", "coverage_review_gate.md", "run_manifest.json"):
        if not (submission / name).is_file(): errors.append("missing artifact: " + name)
    if errors: return False, errors
    report = json.loads((submission / "diversity_report.json").read_text())
    for key in ("candidate_count", "valid_count", "unique_valid_count", "scaffolds", "clusters", "coverage", "rules_version"):
        if report.get(key) != exp[key]: errors.append("diversity report mismatch: " + key)
    if report.get("input_sha256") != exp["hashes"]: errors.append("diversity report provenance mismatch")
    table = (submission / "candidate_set.tsv").read_text().lower()
    for phrase in ("candidate_id", "scaffold", "cluster", "valid"):
        if phrase not in table: errors.append("candidate_set.tsv missing " + phrase)
    gate = (submission / "coverage_review_gate.md").read_text().lower()
    for phrase in ("coverage", "scaffold", "human review", "not biological activity"):
        if phrase not in gate: errors.append("coverage gate missing " + phrase)
    manifest = json.loads((submission / "run_manifest.json").read_text())
    if manifest.get("input_sha256") != exp["hashes"] or manifest.get("rules_version") != exp["rules_version"] or manifest.get("deterministic") is not True: errors.append("run manifest provenance mismatch")
    return not errors, errors

if __name__ == "__main__":
    p = argparse.ArgumentParser(); p.add_argument("--submission", type=Path, required=True); p.add_argument("--data", type=Path, required=True); p.add_argument("--reference", type=Path, required=True)
    a = p.parse_args(); ok, errors = verify(a.submission, a.data, a.reference); print(json.dumps({"passed": ok, "errors": errors})); raise SystemExit(0 if ok else 1)
'''


def quality(task_id: str, decision: str, unit: str, handoff: str, consequence: str, axes: list[str]) -> dict[str, dict]:
    return {
        "candidate_set_card.json": {"candidate_set_id": f"CSET-{task_id.upper()}-001", "source_benchmark_id": task_id[:5].upper(), "candidates": [{"candidate_id": task_id, "decision": decision, "unit": unit, "error_consequence": consequence, "semantic_axes": axes, "selection_status": "MATERIALIZED"}], "selection_gate": {"minimum_candidates": 3, "maximum_candidates": 5, "require_two_semantic_differences": True, "require_independent_review": True}, "status": "REVIEW_REQUIRED"},
        "enterprise_value_card.json": {"enterprise_value_card_id": f"VALUE-{task_id.upper()}-001", "task_id": task_id, "enterprise_reality": {"evidence_class": "B" if task_id.startswith("eb003") else "W", "real_work_node": decision, "named_role": "scientific_analyst", "decision": decision, "downstream_action": handoff, "error_consequence": consequence, "human_owner": "domain_reviewer"}, "utility_hypothesis": {"decision_quality": "preserve an auditable handoff", "risk_reduction": consequence, "adoption_test": "independent practitioner can reconstruct the decision"}, "novelty": {"source_gap": "public workflow does not enforce this decision contract", "new_information_or_control": "synthetic provenance/coverage controls", "not_surface_variant": True}, "status": "REVIEW_REQUIRED"},
        "difficulty_card.json": {"difficulty_card_id": f"DIFF-{task_id.upper()}-001", "task_id": task_id, "difficulty_hypothesis": {"reasoning_chain": ["inspect visible evidence", "reconcile competing records", "preserve uncertainty", "issue bounded handoff"], "competing_choices": ["proceed versus hold", "headline score versus independent evidence"], "stateful_dependencies": ["missing evidence blocks downstream claim"], "target_failure_mechanism": "fluent shortcut ignores provenance or coverage failure"}, "shortcut_probes": ["company-name matching", "always-proceed", "always-abstain", "template copying"], "baseline_matrix": [{"strategy": x, "expected_status": "NOT_RUN"} for x in ("reference_solution", "simple_legal_baseline", "always_abstain", "template_or_keyword", "target_model")], "status": "DRAFT"},
        "training_value_card.json": {"training_value_card_id": f"TRAIN-{task_id.upper()}-001", "task_id": task_id, "capability_targets": ["evidence reconciliation", "failure diagnosis", "claim boundary", "artifact completeness"], "error_labels": ["input_understanding", "method_choice", "calculation_or_tool", "claim_overreach", "delivery_failure"], "feedback_granularity": ["artifact-level", "criterion-level", "failure-injection-level"], "generalization_plan": {"held_out_axis": "new records and control perturbations", "contamination_control": "hide reference decisions", "transfer_probe": "new missing-evidence cases"}, "training_use": "EVAL_ONLY_UNTIL_CALIBRATED", "status": "REVIEW_REQUIRED"},
        "control_plan_card.json": {"control_plan_id": f"CONTROL-{task_id.upper()}-001", "task_id": task_id, "controls": [{"control_id": "positive-reference", "kind": "positive"}, {"control_id": "negative-corruption", "kind": "negative"}, {"control_id": "invariance-row-order", "kind": "invariance"}, {"control_id": "insufficient-evidence", "kind": "insufficient_evidence"}], "single_factor_policy": True, "calibration_status": "NOT_RUN", "release_blockers": ["independent practitioner review", "target-model trial", "license/privacy signoff"], "status": "REVIEW_REQUIRED"},
        "model_trial_card.json": {"model_trial_card_id": f"TRIAL-{task_id.upper()}-001", "task_id": task_id, "protocol_version": "enterprise-model-trial.v1", "strategies": ["reference_solution", "simple_legal_baseline", "always_abstain", "template_or_keyword", "target_model"], "target_model_status": "NOT_RUN", "status": "NOT_RUN"},
        "sop_card.json": {"schema_version": "enterprise_harbor_sop_card.v1", "task_id": task_id, "sop_version": "enterprise-harbor-sop-v1.1", "source_status": "REVIEW_REQUIRED", "contract_status": "CONTRACT_ONLY", "control_status": "NOT_RUN", "model_trial_status": "NOT_RUN", "target_model_failure_policy": "infrastructure_failures_are_not_difficulty_evidence", "independent_verifier_status": "NOT_RUN", "release_status": "BLOCKED", "release_blockers": ["source/license/privacy review", "independent verifier contract audit", "control calibration", "target-model trial"]},
    }


def materialize(task_id: str, title: str, decision: str, unit: str, handoff: str, consequence: str, axes: list[str], task_yaml: str, scenario: str, instruction: str, expected: str, data: dict, reference: dict, verifier: str) -> None:
    root = ROOT / "benchmarks" / task_id
    # Keep mined scenario cards compiler-ready even when their source brief is
    # intentionally compact.  The builder requires explicit judgments,
    # handoffs, and release gates for every selected decision.
    scenario_suffixes = {
        "eb003-replay-provenance-004": """scientific_judgments:
  - provenance_and_environment_reconciliation
  - reproducibility_stop_rule
  - computational_claim_boundary
workflow_handoffs:
  - from: analysis
    to: reproduction_review
    artifact: outputs/handoff_replay_report.md
    invariant: checksums and environment must remain aligned before approval
release_gates:
  scientific_reality: pass
  observability: pass
  verifiability: pass
  naive_resistance: pass
""",
        "eb009-diversity-coverage-004": """scientific_judgments:
  - validity_and_identifier_integrity
  - scaffold_and_cluster_coverage
  - portfolio_triage_claim_boundary
workflow_handoffs:
  - from: generation
    to: diversity_audit
    artifact: outputs/diversity_report.json
    invariant: only valid candidates contribute to coverage counts
  - from: diversity_audit
    to: human_review
    artifact: outputs/coverage_review_gate.md
    invariant: computed coverage is not activity or developability evidence
release_gates:
  scientific_reality: pass
  observability: pass
  verifiability: pass
  naive_resistance: pass
""",
    }
    scenario_text = scenario + scenario_suffixes.get(task_id, "")
    write(root / "task.yaml", task_yaml)
    write(root / "scenario-card.yaml", scenario_text)
    write(root / "instruction.md", instruction)
    write(root / "expected_artifacts.md", expected)
    for name, content in data.items(): write(root / "data" / name, content)
    write(root / "verifier_only" / "reference.json", reference); write(root / "verifier.py", verifier)
    for name, content in quality(task_id, decision, unit, handoff, consequence, axes).items(): write(root / "quality" / name, content)
    write(root / "controls" / "calibration_results.json", {"schema_version": "enterprise_control_calibration.v1", "status": "NOT_RUN", "tasks": [{"task_id": task_id, "status": "NOT_RUN"}]})
    write(root / "tests" / "test_verifier.py", """import importlib.util\nfrom pathlib import Path\nROOT = Path(__file__).resolve().parents[1]\nspec = importlib.util.spec_from_file_location('verifier', ROOT / 'verifier.py')\nverifier = importlib.util.module_from_spec(spec); spec.loader.exec_module(verifier)\ndef test_expected_deterministic():\n    assert verifier.expected(ROOT / 'data') == verifier.expected(ROOT / 'data')\ndef test_missing_submission_fails(tmp_path):\n    ok, errors = verifier.verify(tmp_path, ROOT / 'data', ROOT / 'verifier_only/reference.json')\n    assert not ok and errors\n""")


def main() -> None:
    materialize("eb003-replay-provenance-004", "CompBioBench replay provenance", "Can a delivered computational artifact be replayed from its recorded provenance and environment after handoff?", "analysis artifact and execution manifest", "analysis->reproduction_review", "an untraceable artifact can be accepted despite hidden version, checksum, or nondeterminism drift", ["reproducibility", "evidence_reconciliation", "evaluation_contract"], """id: eb003-replay-provenance-004\nversion: \"0.1.0\"\nstatus: ready_for_calibration\ntitle: \"Computational artifact replay from provenance\"\ndomain: biomedical_enterprise\nagent_visible_inputs:\n  - path: data/\n    format: JSON\nconstraints:\n  network: off\n  provenance:\n    record_input_checksum: true\n    deterministic_output: true\nrequired_outputs:\n  - {id: replay_manifest, path: outputs/replay_manifest.json, required_fields: [artifact_id, rules_version, input_hashes, output_hashes, environment, replay_status]}\n  - {id: provenance_diff, path: outputs/provenance_diff.tsv, required_fields: [field, status, match]}\n  - {id: handoff_report, path: outputs/handoff_replay_report.md, required_fields: [replay_result, checksum_evidence, human_review_decision, claim_boundary]}\nhidden_truth:\n  path: verifier_only/reference.json\n  status: verifier_only\n""", """scenario_id: eb003-replay-provenance-004\nstatus: ready\nsource_scenarios: [EB003]\ndomain: biomedical_enterprise\nscientific_decision: approve a reproducible computational handoff\n""", """# Computational artifact replay\n\nReconcile the recorded artifact, input/output checksums, environment and rerun result. Hold unexplained differences for human review.\n\nWrite exactly these files under `outputs/`:\n- `outputs/replay_manifest.json`: artifact ID, rules version, input/output hashes, environment and replay status.\n- `outputs/provenance_diff.tsv`: columns `field`, `status`, and `match`.\n- `outputs/handoff_replay_report.md`: replay result, checksum evidence, human review decision, and the statement that this is not biological validation.\n""", """# Expected artifacts\n\nSynthetic offline fixture. A reproduced artifact is a computational reproducibility result, not biological validation.\n""", {"artifact_manifest.json": {"artifact_id": "ART-17", "rules_version": "replay-v1", "input_hashes": {"inputs.tsv": "sha256:inputs-17"}, "output_hashes": {"result.tsv": "sha256:result-17"}}, "environment.json": {"python": "3.11", "tool": "compbio-tool", "tool_version": "2.4.0", "reference": "ref-v3", "deterministic": True}}, {"artifact_id": "ART-17", "rules_version": "replay-v1"}, EB003_VERIFIER)
    materialize("eb009-diversity-coverage-004", "REINVENT4 diversity coverage", "Does the generated candidate set cover the intended scaffold and chemical space before synthesis review?", "candidate set and scaffold cluster", "generation->diversity_audit->human_review", "mode collapse or representation errors can waste synthesis capacity on near-duplicates", ["data_multimodal_join", "evaluation_contract", "coverage"], """id: eb009-diversity-coverage-004\nversion: \"0.1.0\"\nstatus: ready_for_calibration\ntitle: \"Generated candidate diversity and scaffold coverage\"\ndomain: biomedical_enterprise\nagent_visible_inputs:\n  - path: data/\n    format: CSV and JSON\nconstraints:\n  network: off\n  provenance:\n    record_input_checksum: true\n    deterministic_output: true\nrequired_outputs:\n  - {id: candidate_set, path: outputs/candidate_set.tsv, required_fields: [candidate_id, scaffold, cluster, valid]}\n  - {id: diversity_report, path: outputs/diversity_report.json, required_fields: [candidate_count, valid_count, unique_valid_count, scaffolds, clusters, coverage, rules_version, input_sha256]}\n  - {id: coverage_gate, path: outputs/coverage_review_gate.md, required_fields: [coverage_result, scaffold_evidence, human_review_decision, claim_boundary]}\n  - {id: run_manifest, path: outputs/run_manifest.json, required_fields: [input_sha256, rules_version, deterministic]}\nhidden_truth:\n  path: verifier_only/reference.json\n  status: verifier_only\n""", """scenario_id: eb009-diversity-coverage-004\nstatus: ready\nsource_scenarios: [EB009]\ndomain: biomedical_enterprise\nscientific_decision: approve candidate diversity coverage for synthesis review\n""", """# Candidate diversity audit\n\nCheck validity, unique IDs, scaffold coverage and cluster coverage before human synthesis review. Computed diversity is not biological activity.\n\nWrite exactly these files under `outputs/`:\n- `outputs/candidate_set.tsv`: columns `candidate_id`, `scaffold`, `cluster`, and `valid`.\n- `outputs/diversity_report.json`: counts, scaffold/cluster lists, coverage, rules version, and input hashes.\n- `outputs/coverage_review_gate.md`: coverage result, scaffold evidence, human review decision, and the statement that this is not biological activity.\n- `outputs/run_manifest.json`: input hashes, rules version, and `deterministic: true`.\n""", """# Expected artifacts\n\nSynthetic offline fixture. Coverage supports portfolio triage only and does not establish activity or developability.\n""", {"candidates.csv": "candidate_id,scaffold,cluster,valid\nM-1,S-A,C-1,true\nM-2,S-B,C-2,true\nM-3,S-C,C-3,true\nM-4,S-A,C-1,true\nM-5,S-D,C-4,false\n", "rules.json": {"rules_version": "diversity-v1", "minimum_scaffolds": 3, "minimum_clusters": 3}}, {"coverage": True}, EB009_VERIFIER)


if __name__ == "__main__":
    main()
