#!/usr/bin/env python3
"""Generate draft enterprise card bundles from the registry.

The generated cards are intentionally review-blocked scaffolds. They preserve
source attribution and the original benchmark contract, but never infer a
scientific truth route or grant Harbor release readiness.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
from pathlib import Path


BASE_CARD_NAMES = ("source", "benchmark", "workflow", "transformation", "data", "evaluation", "risk", "harbor", "review")
QUALITY_CARD_NAMES = ("candidate_set", "enterprise_value", "control_plan", "difficulty", "training_value", "model_trial")
CARD_NAMES = BASE_CARD_NAMES + QUALITY_CARD_NAMES


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def slug(value: str) -> str:
    value = re.sub(r"[^a-zA-Z0-9]+", "-", value).strip("-").lower()
    return value[:48] or "benchmark"


def build_cards(benchmark: dict, workflow: dict | None, retrieved_at: str) -> dict[str, dict]:
    benchmark_id = benchmark["benchmark_id"]
    task_id = f"{slug(benchmark_id)}-candidate-001"
    source_id = benchmark["source_id"]
    workflow = workflow or {
        "workflow_id": f"WF-{benchmark_id}-UNRESOLVED",
        "benchmark_ids": [benchmark_id],
        "enterprise_stage": "unresolved",
        "role": "unresolved",
        "object": benchmark.get("object", "unresolved"),
        "business_decision": benchmark.get("decision", "unresolved"),
        "handoffs": ["input->analysis->decision"],
        "independent_unit": "unresolved",
        "claim_boundary": "Benchmark score does not establish enterprise or clinical validity.",
        "status": "candidate",
    }
    business_decision = workflow.get("business_decision", benchmark.get("decision", "unresolved"))
    role = workflow.get("role", "unresolved")
    stage = workflow.get("enterprise_stage", "unresolved")
    handoff = workflow.get("handoffs", ["input->analysis->decision"])
    error_consequence = "; ".join(workflow.get("failure_consequences", ["downstream decision may be wrong"]))
    candidate_prefix = slug(benchmark_id)
    return {
        "source": {
            "source_id": source_id,
            "organization": benchmark.get("organization", ""),
            "url": benchmark.get("source_url", ""),
            "kind": benchmark.get("enterprise_role", "unknown"),
            "authenticity": benchmark.get("authenticity_class", "S"),
            "evidence_status": benchmark.get("evidence_status", "observed"),
            "retrieved_at": retrieved_at,
            "commit_or_version": None,
            "license_status": benchmark.get("license_status", "verify_pending"),
            "evidence_locators": ["registry/enterprise_benchmarks.jsonl"],
            "unresolved_questions": ["freeze an official commit or version", "verify data and model redistribution terms", "confirm enterprise participation scope"],
        },
        "benchmark": dict(benchmark),
        "workflow": dict(workflow),
        "transformation": {
            "schema_version": "enterprise_transformation_card.v1",
            "transformation_id": f"TX-{benchmark_id}-DRAFT",
            "source_benchmark_id": benchmark_id,
            "derived_task_id": task_id,
            "status": "DRAFT",
            "changed_dimensions": ["business_decision", "failure_mode", "evaluation_contract"],
            "semantic_changed_dimensions": [],
            "surface_only_changes": [],
            "scientific_decision_changed": False,
            "truth_or_failure_changed": False,
            "transformation_primitives": [],
            "evidence": {},
            "accepted_alternatives": [],
            "scientific_rationale": None,
            "release_status": "REVIEW_REQUIRED",
        },
        "data": {
            "data_card_id": f"DATA-{benchmark_id}-DRAFT",
            "source_benchmark_id": benchmark_id,
            "data_kind": "source_data_status_pending",
            "lineage": [benchmark.get("source_url", "")],
            "visibility": {"agent": benchmark.get("inputs", []), "verifier": ["hidden truth to be authored"], "author": ["source files and license evidence"]},
            "truth_scope": "Not yet established; do not infer labels, units, or external validity.",
            "status": "DRAFT",
        },
        "evaluation": {
            "evaluation_card_id": f"EVAL-{benchmark_id}-DRAFT",
            "task_id": task_id,
            "independent_unit": workflow.get("independent_unit", "unresolved"),
            "metrics": benchmark.get("evaluation", {}).get("metrics", []),
            "truth_route": ["independent oracle or invariant route required", "reference replay required"],
            "accepted_alternatives": ["must be authored from method-equivalence analysis"],
            "negative_cases": ["empty submission", "wrong schema", "unsupported claim"],
            "status": "DRAFT",
        },
        "risk": {
            "risk_card_id": f"RISK-{benchmark_id}-DRAFT",
            "task_id": task_id,
            "attribution": {"organization": benchmark.get("organization", ""), "enterprise_role": benchmark.get("enterprise_role", ""), "status": "review_required"},
            "license": {"status": benchmark.get("license_status", "verify_pending"), "solver_redistribution": "blocked_until_review"},
            "privacy": {"status": "review_required"},
            "biosafety_or_medical": {"status": "review_required"},
            "claim_boundary": [workflow.get("claim_boundary", "")],
            "release_status": "REVIEW_REQUIRED",
        },
        "harbor": {
            "harbor_card_id": f"HARBOR-{benchmark_id}-DRAFT",
            "task_id": task_id,
            "task_contract": {"instruction": None, "task_yaml": None},
            "agent_visible": benchmark.get("inputs", []),
            "verifier_only": ["truth", "oracle", "verifier"],
            "environment": {"network": "to_be_frozen", "resources": "to_be_measured"},
            "oracle": {"status": "not_authored"},
            "release_gates": {"source": "blocked", "license": "blocked", "truth": "blocked", "verifier": "blocked", "trial": "not_run"},
            "status": "CONTRACT_ONLY",
        },
        "review": {
            "review_id": f"REVIEW-{benchmark_id}-DRAFT",
            "task_id": task_id,
            "reviewers": ["domain_scientist", "methods_reproducibility_auditor", "license_attribution_reviewer"],
            "hard_gates": ["enterprise attribution verified", "license verified", "truth route independently checked", "agent/verifier isolation tested"],
            "open_questions": ["what is the real business handoff?", "which evidence is visible to the agent?", "what is the acceptable answer class?"],
            "decision": "REVISE",
            "status": "PENDING",
        },
        "candidate_set": {
            "candidate_set_id": f"CSET-{benchmark_id}-DRAFT",
            "source_benchmark_id": benchmark_id,
            "candidates": [
                {
                    "candidate_id": f"{candidate_prefix}-decision-gate-001",
                    "decision": business_decision,
                    "unit": workflow.get("independent_unit", "unresolved"),
                    "error_consequence": error_consequence,
                    "semantic_axes": ["business_decision", "failure_mode", "claim_boundary"],
                    "handoff": handoff[0] if handoff else "unresolved",
                    "selection_status": "PENDING",
                },
                {
                    "candidate_id": f"{candidate_prefix}-evidence-boundary-002",
                    "decision": "which claims are supported, uncertain, or blocked by the available evidence",
                    "unit": workflow.get("independent_unit", "unresolved"),
                    "error_consequence": "unsupported claim or premature escalation",
                    "semantic_axes": ["visible_evidence", "claim_boundary", "evaluation_contract"],
                    "handoff": handoff[-1] if handoff else "unresolved",
                    "selection_status": "PENDING",
                },
                {
                    "candidate_id": f"{candidate_prefix}-handoff-review-003",
                    "decision": "whether to proceed, stop, or request human review at the next workflow handoff",
                    "unit": workflow.get("independent_unit", "unresolved"),
                    "error_consequence": "wasted experiment, invalid analysis handoff, or audit failure",
                    "semantic_axes": ["enterprise_context", "handoff", "stopping_rule"],
                    "handoff": "human_review->next_stage",
                    "selection_status": "PENDING",
                },
            ],
            "deduplication_axes": ["decision", "unit", "error_consequence", "handoff", "stopping_rule"],
            "selection_gate": {
                "minimum_candidates": 3,
                "maximum_candidates": 5,
                "require_two_semantic_differences": True,
                "require_independent_review": True,
            },
            "open_questions": ["which candidate has a real enterprise owner?", "which candidate has an independent truth route?"],
            "status": "DRAFT",
        },
        "enterprise_value": {
            "enterprise_value_card_id": f"VALUE-{benchmark_id}-DRAFT",
            "task_id": task_id,
            "enterprise_reality": {
                "evidence_class": benchmark.get("authenticity_class", "S"),
                "real_work_node": stage,
                "named_role": role,
                "decision": business_decision,
                "downstream_action": "pending confirmation with an enterprise practitioner",
                "error_consequence": error_consequence,
                "human_owner": "unresolved",
            },
            "utility_hypothesis": {
                "decision_quality": "reduce false escalation and prevent invalid downstream handoff",
                "cycle_time_or_cost": "not estimated",
                "risk_reduction": "detect data, evidence, or claim-boundary failures before the next stage",
                "adoption_test": "an independent practitioner can state the proceed/stop/review rule from the artifact",
            },
            "novelty": {
                "source_gap": "pending source and practitioner review",
                "new_information_or_control": "requires an explicit business decision and auditable handoff, not only a benchmark score",
                "not_surface_variant": True,
            },
            "required_evidence": ["named_role", "decision", "downstream_action", "error_consequence", "human_owner"],
            "status": "DRAFT",
        },
        "control_plan": {
            "control_plan_id": f"CONTROL-{benchmark_id}-DRAFT",
            "task_id": task_id,
            "controls": [
                {"control_id": "positive-sufficient-evidence", "kind": "positive", "input_change": "valid evidence and analyzable metadata", "expected_behavior": "make the supported decision with evidence", "verifier_signal": "decision_and_evidence_match", "status": "NOT_RUN"},
                {"control_id": "negative-invalid-input", "kind": "negative", "input_change": "conflicting metadata, units, or schema", "expected_behavior": "detect the defect and stop or downgrade the claim", "verifier_signal": "defect_reported_and_no_unsafe_completion", "status": "NOT_RUN"},
                {"control_id": "invariance-benign-reorder", "kind": "invariance", "input_change": "legal row/order or filename permutation", "expected_behavior": "preserve the decision and key metrics", "verifier_signal": "equivalent_result_class", "status": "NOT_RUN"},
                {"control_id": "insufficient-evidence", "kind": "insufficient_evidence", "input_change": "remove one necessary evidence source", "expected_behavior": "separate supported claims from unresolved claims", "verifier_signal": "bounded_abstention", "status": "NOT_RUN"},
            ],
            "single_factor_policy": True,
            "calibration_status": "NOT_RUN",
            "release_blockers": ["execute positive/negative/invariance controls", "verify expected relations", "record false-positive and false-negative cases"],
            "status": "DRAFT",
        },
        "difficulty": {
            "difficulty_card_id": f"DIFF-{benchmark_id}-DRAFT",
            "task_id": task_id,
            "difficulty_hypothesis": {
                "reasoning_chain": ["validate input provenance and unit", "identify independent unit and split", "compare competing methods or claims", "produce a bounded enterprise decision", "leave an auditable handoff"],
                "competing_choices": ["proceed vs stop", "support vs abstain", "candidate A vs candidate B", "technical success vs business readiness"],
                "stateful_dependencies": ["later claims depend on earlier metadata and split checks", "a failed gate changes the allowed conclusion"],
                "uncertainty_sources": ["partial labels", "metadata conflicts", "equivalent valid answers", "public benchmark versus enterprise-use boundary"],
                "target_failure_mechanism": "a fluent answer that skips provenance, experimental unit, evidence boundary, or handoff rules",
            },
            "shortcut_probes": [
                "keyword or company-name matching",
                "constant prediction or always-support response",
                "file-count and output-volume heuristics",
                "copying public benchmark labels or leaderboard answers",
            ],
            "baseline_matrix": [
                {"strategy": "reference_solution", "purpose": "prove a valid solution exists", "expected_status": "NOT_RUN"},
                {"strategy": "simple_legal_baseline", "purpose": "measure whether the task is only direct computation", "expected_status": "NOT_RUN"},
                {"strategy": "always_abstain", "purpose": "test whether conservative non-answering is over-rewarded", "expected_status": "NOT_RUN"},
                {"strategy": "template_or_keyword", "purpose": "test prompt and label shortcuts", "expected_status": "NOT_RUN"},
                {"strategy": "target_model", "purpose": "measure autonomous reasoning and tool use", "expected_status": "NOT_RUN"},
            ],
            "difficulty_dimensions": ["scientific_judgment", "evidence_reconciliation", "tool_and_trace_reliability", "claim_boundary", "artifact_completeness"],
            "status": "DRAFT",
        },
        "training_value": {
            "training_value_card_id": f"TRAIN-{benchmark_id}-DRAFT",
            "task_id": task_id,
            "capability_targets": ["schema and provenance inspection", "experimental-unit and split reasoning", "evidence-grounded decision making", "uncertainty and claim-boundary control"],
            "error_labels": ["input_understanding", "method_choice", "calculation_or_tool", "evidence_misuse", "claim_overreach", "delivery_failure"],
            "feedback_granularity": ["artifact-level", "criterion-level", "claim-level", "failure-injection-level"],
            "generalization_plan": {
                "held_out_axis": "organization, molecule/sample/plate identity, or source version",
                "contamination_control": "freeze source commit and hold out entity-level inputs; do not expose hidden labels or author oracle",
                "transfer_probe": "evaluate a new instance with the same decision contract but different evidence and failure mechanism",
            },
            "training_use": "EVAL_ONLY_UNTIL_CALIBRATED",
            "status": "DRAFT",
        },
        "model_trial": {
            "model_trial_card_id": f"TRIAL-{benchmark_id}-DRAFT",
            "task_id": task_id,
            "protocol_version": "enterprise-model-trial.v1",
            "strategies": ["reference_solution", "simple_legal_baseline", "always_abstain", "template_or_keyword", "target_model"],
            "fixed_config": {"task_digest": None, "input_hashes": [], "model_version": None, "tool_policy": None, "budget": None, "repeat_count": None},
            "score_dimensions": ["scientific_correctness", "evidence_grounding", "decision_usefulness", "artifact_completeness", "reproducibility", "uncertainty_and_claim_boundary", "safety_and_human_review"],
            "failure_attribution_taxonomy": ["input_understanding", "method_choice", "calculation_or_tool", "evidence_and_citation", "claim_boundary", "handoff_and_delivery"],
            "training_value_evidence": {"signal_quality": "NOT_RUN", "error_localization": "NOT_RUN", "generalization": "NOT_RUN", "use_recommendation": "EVAL_ONLY_UNTIL_CALIBRATED"},
            "run_records": [],
            "status": "NOT_RUN",
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("knowledge_base"))
    parser.add_argument("--out", type=Path, default=Path("knowledge_base/draft_bundles"))
    parser.add_argument("--clean", action="store_true", help="remove only previously generated bundle directories")
    args = parser.parse_args()
    benchmarks = read_jsonl(args.root / "registry/enterprise_benchmarks.jsonl")
    workflows = read_jsonl(args.root / "registry/workflows.jsonl")
    workflow_by_benchmark = {benchmark_id: workflow for workflow in workflows for benchmark_id in workflow.get("benchmark_ids", [])}
    if args.clean and args.out.exists():
        for child in args.out.iterdir():
            if child.is_dir() and child.name.startswith("EB"):
                for path in sorted(child.rglob("*"), reverse=True):
                    if path.is_file() or path.is_symlink():
                        path.unlink()
                    elif path.is_dir():
                        path.rmdir()
                child.rmdir()
    args.out.mkdir(parents=True, exist_ok=True)
    retrieved_at = dt.date.today().isoformat()
    for benchmark in benchmarks:
        benchmark_id = benchmark["benchmark_id"]
        bundle_dir = args.out / f"{benchmark_id}-{slug(benchmark['name'])}"
        bundle_dir.mkdir(parents=True, exist_ok=True)
        cards = build_cards(benchmark, workflow_by_benchmark.get(benchmark_id), retrieved_at)
        manifest = {
            "schema_version": "enterprise_card_bundle.v2",
            "bundle_id": f"BUNDLE-{benchmark_id}-DRAFT",
            "source_benchmark_id": benchmark_id,
            "derived_task_id": cards["transformation"]["derived_task_id"],
            "cards": {name: f"{name}_card.json" for name in CARD_NAMES},
            "visibility_policy": {
                "agent_visible": ["benchmark", "workflow", "data", "harbor", "enterprise_value"],
                "author_only": ["source", "transformation", "candidate_set", "control_plan", "difficulty", "training_value", "model_trial", "risk", "review"],
                "verifier_only": ["evaluation.truth_route", "evaluation.negative_cases", "harbor.oracle", "control_plan.expected_truth"],
            },
            "status": "DRAFT",
            "release_blockers": ["source_verification", "license_review", "independent_truth_route", "business_value_review", "control_calibration", "container_replay", "model_trial"],
        }
        (bundle_dir / "card_bundle.manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        for name, card in cards.items():
            (bundle_dir / f"{name}_card.json").write_text(json.dumps(card, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"generated {bundle_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
