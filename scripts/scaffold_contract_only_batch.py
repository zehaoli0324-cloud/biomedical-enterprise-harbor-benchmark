#!/usr/bin/env python3
"""Scaffold the first cross-workflow batch as honest contract-only tasks."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


BATCH = [
    {
        "id": "eb001-split-leakage-001",
        "source": "EB001",
        "title": "Molecular identity and scaffold leakage audit before ADME model comparison",
        "domain": "biomedical_enterprise",
        "stage": "discovery_and_lead_optimization",
        "role": "DMPK_or_computational_chemist",
        "object": "small molecules and canonical structures",
        "question": "Is the proposed ADME train/test split independent at the molecule and scaffold level, or must model comparison be held?",
        "decision": "handoff a leakage-free split or stop before modeling",
        "unit": "molecule and canonical structure",
        "handoff": [("measurement_table", "curated_split", "split_audit.json", "every molecule identity and split assignment is accounted for"), ("curated_split", "prediction", "split_manifest.json", "no canonical structure or scaffold crosses the declared boundary")],
        "consequence": "leakage inflates benchmark performance and misdirects compound selection",
        "failures": [("duplicate-structure", "same canonical structure appears under multiple IDs", "report identity overlap and block readiness"), ("scaffold-overlap", "a scaffold crosses train/test", "report the overlap and distinguish molecule from scaffold policy"), ("stereo-conflict", "stereochemistry or salt normalization changes identity", "preserve the conflict and request a rule decision")],
        "artifacts": ["outputs/split_audit.json", "outputs/structure_identity.tsv", "outputs/readiness_report.md", "outputs/run_manifest.json"],
        "modules": {"scenario": ["scenario_reproducibility_audit"], "judgment": ["judgment_experimental_unit", "judgment_uncertainty_and_stop_rules"], "compute": ["compute_data_schema_discovery"], "noise": ["noise_metadata_conflict", "noise_missing_and_duplicate_inputs"], "data": ["data_text_and_metadata"], "data_complexity": ["complexity_replicates_and_batches"], "environment": ["environment_offline_setup"], "math": ["math_model_selection_and_sensitivity"], "horizon": ["horizon_checkpointed_workflow"], "safety": ["safety_human_approval_gate"]},
        "levels": [4, 4, 3, 1, 1, 4, 3, 3, 1, 2, 3, 2],
        "tags": ["molecule-identity", "scaffold-split", "leakage"],
        "rationale": "The model can compute overlap easily but must first choose the independent unit and stop when identity rules are unresolved.",
    },
    {
        "id": "eb003-failure-recovery-003",
        "source": "EB003",
        "title": "Computational biology tool failure recovery with claim-preserving handoff",
        "domain": "biomedical_enterprise",
        "stage": "computational_biology_support",
        "role": "bioinformatics_or_research_analyst",
        "object": "multimodal omics and sequence input bundle",
        "question": "After a version-pinned tool branch fails or returns partial output, can the analyst recover without changing the scientific question or overclaiming?",
        "decision": "recover with an equivalent route, or stop and request the minimum missing information",
        "unit": "analysis branch and artifact state",
        "handoff": [("validated_inputs", "analysis", "execution_log.jsonl", "every branch has a version, parameters, status, and output locator"), ("analysis", "claim_ledger", "failure_recovery.md", "downstream claims only use valid recovered artifacts")],
        "consequence": "silent fallback or parameter drift makes results incomparable and unauditable",
        "failures": [("partial-output", "a tool writes an incomplete table with exit status zero", "detect incomplete output and prevent downstream use"), ("interface-drift", "the pinned tool rejects a legacy argument", "record the failure and choose an equivalent pinned route or stop"), ("timeout", "one branch exceeds the resource budget", "preserve the failed state and report a bounded fallback")],
        "artifacts": ["outputs/execution_log.jsonl", "outputs/failure_recovery.md", "outputs/claim_ledger.tsv", "outputs/run_manifest.json"],
        "modules": {"scenario": ["scenario_reproducibility_audit"], "judgment": ["judgment_uncertainty_and_stop_rules", "judgment_causal_boundary"], "compute": ["compute_multistage_analysis", "compute_failure_recovery"], "tooling": ["tool_branching_pipeline", "tool_version_and_interface_drift", "tool_adversarial_failure"], "noise": ["noise_metadata_conflict"], "data": ["data_multimodal_join"], "data_complexity": ["complexity_sparse_or_missing"], "environment": ["environment_pinned_container", "environment_resource_budget"], "math": ["math_model_selection_and_sensitivity"], "horizon": ["horizon_checkpointed_workflow", "horizon_end_to_end_claim"], "safety": ["safety_human_approval_gate"]},
        "levels": [4, 5, 4, 4, 1, 4, 4, 4, 4, 3, 5, 3],
        "tags": ["failure-recovery", "version-drift", "claim-ledger"],
        "rationale": "Difficulty comes from preserving state and claim permissions across a failed branch, not from adding more tools.",
    },
    {
        "id": "eb004-adtte-censoring-002",
        "source": "EB004",
        "title": "ADTTE event and censoring derivation under a prespecified cutoff",
        "domain": "biomedical_enterprise",
        "stage": "clinical_statistics",
        "role": "statistical_programmer",
        "object": "subject-parameter-event records from synthetic SDTM-like domains",
        "question": "Which event and censoring dates are valid for the frozen ADTTE endpoint rule, and which records require review?",
        "decision": "handoff ADTTE or hold ambiguous event/censoring records",
        "unit": "subject-parameter-event record",
        "handoff": [("ADSL", "ADTTE", "event_trace.csv", "each date and status cites the source record and endpoint rule"), ("ADTTE", "table_or_analysis", "censoring_audit.json", "ambiguous dates are separated from valid derivations")],
        "consequence": "incorrect censoring changes the survival estimand and downstream table",
        "failures": [("post-cutoff-event", "event date falls after analysis cutoff", "apply the rule and record cutoff handling"), ("partial-date", "only year/month is available", "use the declared partial-date policy or hold"), ("competing-event", "a competing event conflicts with the primary endpoint", "preserve endpoint-specific status and request review")],
        "artifacts": ["outputs/adtte.csv", "outputs/event_trace.csv", "outputs/censoring_audit.json", "outputs/run_manifest.json"],
        "modules": {"scenario": ["scenario_reproducibility_audit"], "judgment": ["judgment_experimental_unit", "judgment_uncertainty_and_stop_rules", "judgment_causal_boundary"], "compute": ["compute_data_schema_discovery", "compute_multistage_analysis"], "noise": ["noise_metadata_conflict", "noise_missing_and_duplicate_inputs"], "data": ["data_text_and_metadata"], "data_complexity": ["complexity_sparse_or_missing"], "environment": ["environment_offline_setup"], "math": ["math_basic_units_and_rates", "math_statistics_and_multiple_testing"], "horizon": ["horizon_checkpointed_workflow", "horizon_end_to_end_claim"], "safety": ["safety_human_approval_gate", "safety_genetic_or_clinical_boundary"]},
        "levels": [4, 5, 3, 1, 1, 4, 3, 3, 1, 3, 4, 3],
        "tags": ["adtte", "event-censoring", "estimand"],
        "rationale": "The same calendar arithmetic can produce different endpoint meanings; the task tests endpoint rules, partial dates, and bounded handoff.",
    },
    {
        "id": "eb005-batch-normalization-002",
        "source": "EB005",
        "title": "Cell Painting normalization choice under controlled batch confounding",
        "domain": "biomedical_enterprise",
        "stage": "high_content_screening",
        "role": "image_analysis_or_phenomics_scientist",
        "object": "plate-level morphological profiles and replicate aggregates",
        "question": "Which normalization and replicate aggregation choice removes batch effects without erasing a reproducible phenotype?",
        "decision": "select a defensible preprocessing branch, or hold when the mechanism is not identifiable",
        "unit": "plate-level replicate aggregate",
        "handoff": [("images_and_metadata", "profiles", "metadata_join_audit.tsv", "plate, perturbation, replicate, and control identities are aligned"), ("profiles", "batch_diagnostics", "batch_report.json", "normalization choice and sensitivity are auditable")],
        "consequence": "over-correction erases biology while under-correction creates false hits",
        "failures": [("batch-confounding", "treatment and plate are aligned", "report non-identifiability and avoid causal language"), ("control-drift", "negative controls shift across plates", "compare normalization branches and retain diagnostics"), ("replicate-imbalance", "one condition has fewer valid replicates", "use the declared unit and report uncertainty")],
        "artifacts": ["outputs/normalization_comparison.tsv", "outputs/batch_report.json", "outputs/sensitivity_summary.md", "outputs/run_manifest.json"],
        "modules": {"scenario": ["scenario_omics_analysis"], "judgment": ["judgment_experimental_unit", "judgment_uncertainty_and_stop_rules", "judgment_causal_boundary"], "compute": ["compute_multistage_analysis"], "noise": ["noise_metadata_conflict", "noise_missing_and_duplicate_inputs"], "data": ["data_images_and_structures", "data_text_and_metadata"], "data_complexity": ["complexity_replicates_and_batches", "complexity_sparse_or_missing"], "environment": ["environment_offline_setup"], "math": ["math_model_selection_and_sensitivity", "math_statistics_and_multiple_testing"], "horizon": ["horizon_checkpointed_workflow", "horizon_end_to_end_claim"], "safety": ["safety_human_approval_gate"]},
        "levels": [5, 5, 4, 2, 1, 5, 4, 4, 1, 4, 4, 3],
        "tags": ["cell-painting", "batch-confounding", "normalization"],
        "rationale": "The agent must compare competing preprocessing branches and distinguish a stable phenotype from a batch artifact.",
    },
    {
        "id": "eb008-stock-route-001",
        "source": "EB008",
        "title": "Retrosynthesis route selection under stock and reaction validity constraints",
        "domain": "biomedical_enterprise",
        "stage": "medicinal_chemistry",
        "role": "medicinal_chemist_or_design_scientist",
        "object": "target molecule and candidate retrosynthesis routes",
        "question": "Which routes satisfy target structure, allowed stock, reaction validity, and search-budget constraints for human chemistry review?",
        "decision": "handoff a computationally valid route, or stop/request a constraint decision",
        "unit": "target molecule and route",
        "handoff": [("target_and_constraints", "search", "configuration.json", "target, stock, policy, and budget are frozen"), ("search", "structure_validation", "route_table.tsv", "every route passes independent structural and stock checks")],
        "consequence": "an invalid or unavailable route wastes chemistry review time and can trigger unsafe constraint relaxation",
        "failures": [("stock-violation", "a route uses a reagent outside the allowed stock", "flag and exclude the route"), ("invalid-reaction", "a generated step fails structural validation", "retain failure evidence and do not count it as solved"), ("search-exhaustion", "the budget ends without a valid route", "report no-route and preserve the budget")],
        "artifacts": ["outputs/route_table.tsv", "outputs/stock_compliance.json", "outputs/route_evidence.tsv", "outputs/approval_gate.md"],
        "modules": {"scenario": ["scenario_structure_design"], "judgment": ["judgment_evidence_quality", "judgment_uncertainty_and_stop_rules", "judgment_causal_boundary"], "compute": ["compute_data_schema_discovery", "compute_failure_recovery"], "tooling": ["tool_branching_pipeline", "tool_adversarial_failure"], "noise": ["noise_metadata_conflict", "noise_red_herring_records"], "data": ["data_text_and_metadata", "data_images_and_structures"], "data_complexity": ["complexity_sparse_or_missing"], "environment": ["environment_resource_budget", "environment_offline_setup"], "math": ["math_model_selection_and_sensitivity"], "horizon": ["horizon_checkpointed_workflow", "horizon_end_to_end_claim"], "safety": ["safety_human_approval_gate", "safety_genetic_or_clinical_boundary"]},
        "levels": [4, 4, 4, 4, 1, 4, 4, 3, 2, 3, 4, 4],
        "tags": ["retrosynthesis", "stock-constraints", "human-approval"],
        "rationale": "A high route score is insufficient; the decision requires independent structure, stock, and failure checks before human review.",
    },
    {
        "id": "eb010-next-batch-001",
        "source": "EB010",
        "title": "Next-batch experimental design under feasibility and budget constraints",
        "domain": "biomedical_enterprise",
        "stage": "closed_loop_experimental_optimization",
        "role": "experimental_design_scientist",
        "object": "candidate experiments and closed-loop state",
        "question": "Which next batch is legal under the search space, material budget, and feasibility constraints, and what evidence supports selecting it?",
        "decision": "select a feasible next batch, stop, or request human review",
        "unit": "candidate experiment and batch",
        "handoff": [("completed_experiments", "next_batch", "next_batch.csv", "all selected experiments satisfy hard constraints and budget"), ("next_batch", "approval", "selection_rationale.md", "trade-offs, uncertainty, and stop conditions are explicit")],
        "consequence": "an invalid or proxy-gamed batch wastes scarce experimental capacity",
        "failures": [("constraint-violation", "candidate exceeds material or search-space limits", "exclude it and report the violated constraint"), ("duplicate-experiment", "the proposed batch repeats an existing experiment", "detect duplicate identity and preserve budget"), ("uncertain-state", "outcome coverage is insufficient for a confident next action", "choose hold/request-information rather than fabricate improvement")],
        "artifacts": ["outputs/next_batch.csv", "outputs/constraint_check.json", "outputs/uncertainty_table.tsv", "outputs/selection_rationale.md"],
        "modules": {"scenario": ["scenario_reproducibility_audit"], "judgment": ["judgment_experimental_unit", "judgment_uncertainty_and_stop_rules"], "compute": ["compute_data_schema_discovery", "compute_multistage_analysis"], "noise": ["noise_metadata_conflict", "noise_missing_and_duplicate_inputs"], "data": ["data_text_and_metadata"], "data_complexity": ["complexity_replicates_and_batches", "complexity_sparse_or_missing"], "environment": ["environment_offline_setup", "environment_resource_budget"], "math": ["math_model_selection_and_sensitivity"], "horizon": ["horizon_branching_experiments", "horizon_end_to_end_claim"], "safety": ["safety_human_approval_gate"]},
        "levels": [4, 5, 4, 2, 1, 4, 3, 4, 2, 4, 5, 3],
        "tags": ["closed-loop", "next-batch", "budget-constraint"],
        "rationale": "The task requires a legal action under uncertainty and budget, not a retrospective leaderboard ranking.",
    },
]

DIMENSIONS = ["scientific_scenario", "scientific_judgment", "computational_difficulty", "tool_call_complexity", "retrieval_complexity", "information_noise_complexity", "data_type_complexity", "data_complexity", "environment_complexity", "mathematical_complexity", "long_horizon_complexity", "safety_risk"]


def _yaml_list(values: list[str]) -> str:
    return "[" + ", ".join(f'"{value}"' for value in values) + "]"


def write_task(root: Path, item: dict, candidate_card_path: str) -> None:
    benchmark_dir = root / "benchmarks" / item["id"]
    benchmark_dir.mkdir(parents=True, exist_ok=True)
    handoff_yaml = "\n".join(
        f"  - from: {source}\n    to: {target}\n    artifact: {artifact}\n    invariant: {invariant}"
        for source, target, artifact, invariant in item["handoff"]
    )
    failure_yaml = "\n".join(
        f"  - id: {item['id']}-{index + 1}\n    trigger: {trigger}\n    expected_behavior: {behavior}\n    verifier_signal: pending_independent_verifier"
        for index, (name, trigger, behavior) in enumerate(item["failures"])
    )
    card = f"""scenario_id: {item['id']}\nstatus: contract_only\nsource_scenarios: [{item['source']}]\ndomain: {item['domain']}\nstage: {item['stage']}\nresearch_role: {item['role']}\nscientific_context:\n  object: {item['object']}\n  question: {item['question']}\n  decision: {item['decision']}\n  consequence_of_error: {item['consequence']}\nscientific_judgments:\n  - independent_unit_and_handoff\n  - competing_choice_and_stop_rule\n  - claim_boundary_and_evidence_quality\nworkflow_handoffs:\n{handoff_yaml}\nrequired_artifacts:\n""" + "\n".join(f"  - {artifact}" for artifact in item["artifacts"]) + f"""\nfailure_injections:\n{failure_yaml}\nrelease_gates:\n  scientific_reality: pass\n  observability: pending\n  verifiability: pending\n  naive_resistance: pending\n  reproducibility: pending\n  enterprise_value: pending\n  training_value: not_run\nopen_questions:\n  - Freeze the task-specific public input version and redistribution terms.\n  - Author an independent oracle or expert-equivalence rubric.\n  - Run positive, negative, invariance, and insufficient-evidence controls.\n"""
    (benchmark_dir / "scenario-card.yaml").write_text(card, encoding="utf-8")

    instruction = f"""# Contract-only task: {item['title']}\n\nYou are acting as a {item['role']} in the {item['stage']} workflow. The enterprise decision is:\n\n> {item['question']}\n\nThe task must preserve the independent unit (`{item['unit']}`), record the handoff, and stop or request review when the evidence is insufficient. It must not turn a computational result into a clinical, efficacy, safety, synthesizability, or causal claim.\n\nThis package is currently `contract_only`. The final agent-visible data bundle, hidden oracle, verifier, and resource-pinned environment are not yet attached. When materialized, the agent must record input checksums, versions, parameters, failures, and deterministic rerun information.\n\nRequired artifact contract:\n\n""" + "\n".join(f"- `{artifact}`" for artifact in item["artifacts"]) + "\n\nRelease blockers are listed in the linked enterprise quality cards and must remain explicit until independently tested.\n"
    (benchmark_dir / "instruction.md").write_text(instruction, encoding="utf-8")
    expected = "# Expected artifacts\n\nThis contract-only package reserves the following artifacts:\n\n" + "\n".join(f"- `{artifact}`" for artifact in item["artifacts"]) + "\n\nThe schema, hidden truth route, accepted equivalence classes, negative matrix, and verifier signals are pending materialization.\n"
    (benchmark_dir / "expected_artifacts.md").write_text(expected, encoding="utf-8")
    task = f"""id: {item['id']}\nversion: \"0.1.0\"\nstatus: contract_only\ntitle: \"{item['title']}\"\ndomain: {item['domain']}\nstage: {item['stage']}\nscenario_ids: [{item['source']}]\nscenario_card: scenario-card.yaml\nscientific_decision:\n  question: {item['question']}\n  target_claim_boundary: {item['consequence']}; this contract does not establish an experimental, clinical, or commercial conclusion.\n  consequence_of_error: {item['consequence']}\nagent_visible_inputs:\n  - path: data/\n    format: task-specific bundle\n    contract: pending frozen public or synthetic fixture\nconstraints:\n  network: \"off\"\n  compute:\n    cpu_seconds: 120\n    memory_mb: 1024\n  provenance:\n    record_input_checksum: true\n    record_tool_version: true\n    deterministic_output: true\n  safety:\n    scope: contract-only enterprise workflow analysis\n    prohibited: do not overstate computational evidence or use the task as clinical, efficacy, safety, or wet-lab authorization\nrequired_outputs:\n""" + "\n".join(f"  - id: {Path(artifact).stem}\n    path: {artifact}\n    required_fields: [schema_version]" for artifact in item["artifacts"]) + f"""\nhidden_truth:\n  status: not_authored\n  policy: verifier-only when materialized\nprovenance:\n  source_benchmark: {item['source']}\n  data_status: source workflow observed; task fixture pending\nquality_cards:\n  candidate_set: candidate_pools/enterprise-v1/{item['source']}-candidate-set.json\n  question_brief: candidate_pools/enterprise-v1/question_briefs/{item['id']}.json\n"""
    task = task.replace(
        f"candidate_pools/enterprise-v1/{item['source']}-candidate-set.json",
        candidate_card_path,
    )
    (benchmark_dir / "task.yaml").write_text(task, encoding="utf-8")

    config_dir = root / "candidate_pools" / "enterprise-v1" / "contracts"
    config_dir.mkdir(parents=True, exist_ok=True)
    dimensions = []
    for name, level in zip(DIMENSIONS, item["levels"]):
        dimensions.append(f"[difficulty.{name}]\nlevel = {level}\nweight = 1.0\nrationale = \"{item['rationale']}\"\ntags = {_yaml_list(item['tags'])}\n")
    modules = "\n".join(f"{category} = {_yaml_list(values)}" for category, values in item["modules"].items())
    config = f"""[task]\nid = \"{item['id']}\"\ntitle = \"{item['title']}\"\ndomain = \"{item['domain']}\"\nsource_scenarios = [\"{item['source']}\"]\n\n[scenario]\ncard = \"../../../benchmarks/{item['id']}/scenario-card.yaml\"\n\n""" + "\n".join(dimensions) + f"""[modules]\n{modules}\n\n[data]\ntypes = [\"csv\", \"json\", \"markdown\"]\n\n[constraints]\nnetwork = \"off\"\ncpu_seconds = 120\nmemory_mb = 1024\nrequires_input_checksum = true\nrequires_deterministic_output = true\n"""
    (config_dir / f"{item['id']}.toml").write_text(config, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("."))
    args = parser.parse_args()
    root = args.root.resolve()
    matrix = json.loads((root / "candidate_pools/enterprise-v1/manifest.json").read_text(encoding="utf-8"))
    candidate_cards = {entry["benchmark_id"]: entry["path"] for entry in matrix["cards"]}
    for item in BATCH:
        write_task(root, item, candidate_cards[item["source"]])
    task_records = []
    for item in BATCH:
        materialized = all(
            path.exists()
            for path in (
                root / "benchmarks" / item["id"] / "data",
                root / "benchmarks" / item["id"] / "verifier.py",
                root / "benchmarks" / item["id"] / "verifier_only" / "reference.json",
            )
        )
        task_records.append({"id": item["id"], "source": item["source"], "status": "ready_for_calibration" if materialized else "contract_only"})
    batch_status = "MIXED_CALIBRATION_AND_CONTRACT" if any(item["status"] == "ready_for_calibration" for item in task_records) else "CONTRACT_ONLY"
    manifest = {
        "schema_version": "enterprise_contract_batch.v1",
        "batch_id": "TRANCHE-001",
        "status": batch_status,
        "task_count": len(BATCH),
        "source_ledger": "candidate_pools/enterprise-v1/source_ledger.json",
        "tasks": task_records,
        "release_policy": "no task is runnable until data, oracle, verifier, controls, and model trial are independently materialized",
    }
    out = root / "candidate_pools/enterprise-v1/contracts/manifest.json"
    out.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"scaffolded {len(BATCH)} contract-only task packages")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
