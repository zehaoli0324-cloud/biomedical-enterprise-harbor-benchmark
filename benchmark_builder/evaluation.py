"""Structured multi-judge evaluation and controlled task iteration."""

from __future__ import annotations

import json
import math
import statistics
from pathlib import Path
from typing import Any

from .compiler import spec_digest
from .models import BenchmarkSpec, EvaluationSpec


class EvaluationError(ValueError):
    """Raised when a judge packet is incomplete or incompatible with a task spec."""


def evaluation_protocol(spec: BenchmarkSpec) -> dict[str, Any]:
    """Return the provider-neutral contract sent to each LLM judge."""
    return {
        "schema_version": "benchmark_builder.evaluation.v1",
        "task_id": spec.task_id,
        "spec_digest": spec_digest(spec),
        "scale": {"min": spec.evaluation.scale_min, "max": spec.evaluation.scale_max},
        "judge_roles": [judge.to_dict() for judge in spec.evaluation.judges],
        "criteria": [criterion.to_dict() for criterion in spec.evaluation.criteria],
        "hard_gates": list(spec.evaluation.hard_gates),
        "output_contract": {
            "task_id": "string",
            "spec_digest": "string",
            "submission_id": "string",
            "judge_id": "string",
            "criteria": {
                "<criterion_id>": {
                    "score": "number within scale",
                    "confidence": "number from 0 to 1",
                    "evidence": "list of artifact paths, line locators, or verifier IDs",
                    "rationale": "short evidence-grounded explanation",
                }
            },
            "hard_gates": {"<gate_id>": "boolean"},
        },
        "judge_instructions": [
            "Score only evidence present in the submission and the agent-visible task inputs.",
            "Do not infer a missing result from a plausible tool workflow.",
            "Separate scientific correctness from writing quality and output volume.",
            "Return an explicit low score or failed gate when the submission overclaims causality or hides uncertainty.",
            "Cite artifact paths or verifier IDs for every non-trivial score.",
        ],
    }


def _validate_number(value: Any, label: str, lower: float, upper: float) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise EvaluationError(f"{label} must be a finite number")
    if not lower <= float(value) <= upper:
        raise EvaluationError(f"{label} must be between {lower} and {upper}")
    return float(value)


def _load_judgment_packet(path: str | Path, spec: BenchmarkSpec) -> dict[str, Any]:
    with Path(path).open(encoding="utf-8") as handle:
        packet = json.load(handle)
    if not isinstance(packet, dict):
        raise EvaluationError("judgment packet must be a JSON object")
    if packet.get("task_id") != spec.task_id:
        raise EvaluationError("judgment packet task_id does not match task spec")
    expected_digest = spec_digest(spec)
    if packet.get("spec_digest") != expected_digest:
        raise EvaluationError("judgment packet spec_digest does not match task spec")
    if not isinstance(packet.get("submission_id"), str) or not packet["submission_id"]:
        raise EvaluationError("judgment packet requires submission_id")
    if not isinstance(packet.get("judges"), list):
        raise EvaluationError("judgment packet requires a judges list")
    return packet


def _validate_judges(packet: dict[str, Any], spec: BenchmarkSpec) -> list[dict[str, Any]]:
    expected = {judge.judge_id: judge for judge in spec.evaluation.judges}
    seen: set[str] = set()
    validated: list[dict[str, Any]] = []
    for raw in packet["judges"]:
        if not isinstance(raw, dict) or not isinstance(raw.get("judge_id"), str):
            raise EvaluationError("each judge entry requires judge_id")
        judge_id = raw["judge_id"]
        if judge_id not in expected or judge_id in seen:
            raise EvaluationError(f"unknown or duplicate judge: {judge_id}")
        seen.add(judge_id)
        criteria = raw.get("criteria")
        if not isinstance(criteria, dict):
            raise EvaluationError(f"{judge_id} requires criteria object")
        checked: dict[str, Any] = {}
        for criterion in spec.evaluation.criteria:
            value = criteria.get(criterion.criterion_id)
            if not isinstance(value, dict):
                raise EvaluationError(f"{judge_id} is missing criterion {criterion.criterion_id}")
            score = _validate_number(
                value.get("score"),
                f"{judge_id}.{criterion.criterion_id}.score",
                spec.evaluation.scale_min,
                spec.evaluation.scale_max,
            )
            confidence = _validate_number(
                value.get("confidence"), f"{judge_id}.{criterion.criterion_id}.confidence", 0.0, 1.0
            )
            evidence = value.get("evidence", [])
            if not isinstance(evidence, list) or not all(isinstance(item, str) and item for item in evidence):
                raise EvaluationError(f"{judge_id}.{criterion.criterion_id}.evidence must be a list of strings")
            checked[criterion.criterion_id] = {
                "score": score,
                "confidence": confidence,
                "evidence": evidence,
                "rationale": str(value.get("rationale", "")),
            }
        hard_gates = raw.get("hard_gates", {})
        if not isinstance(hard_gates, dict):
            raise EvaluationError(f"{judge_id}.hard_gates must be an object")
        checked_gates = {gate: bool(hard_gates.get(gate, False)) for gate in spec.evaluation.hard_gates}
        validated.append({"judge_id": judge_id, "criteria": checked, "hard_gates": checked_gates})

    missing_required = [
        judge_id for judge_id, judge in expected.items() if judge.required and judge_id not in seen
    ]
    if missing_required:
        raise EvaluationError(f"missing required judges: {', '.join(sorted(missing_required))}")
    return validated


def _agreement(scores: list[float], scale_span: float) -> float:
    if len(scores) <= 1:
        return 1.0
    dispersion = statistics.pstdev(scores) / scale_span
    return round(max(0.0, min(1.0, 1.0 - dispersion)), 4)


def evaluate_submission(spec: BenchmarkSpec, judgments_path: str | Path) -> dict[str, Any]:
    """Aggregate independently-produced LLM judge JSON into a stable report."""
    packet = _load_judgment_packet(judgments_path, spec)
    judges = _validate_judges(packet, spec)
    criterion_results: dict[str, Any] = {}
    weighted_sum = 0.0
    total_weight = sum(criterion.weight for criterion in spec.evaluation.criteria)
    for criterion in spec.evaluation.criteria:
        values = [judge["criteria"][criterion.criterion_id] for judge in judges]
        scores = [value["score"] for value in values]
        score = round(statistics.median(scores), 4)
        agreement = _agreement(scores, spec.evaluation.scale_max - spec.evaluation.scale_min)
        criterion_results[criterion.criterion_id] = {
            "score": score,
            "minimum_score": criterion.minimum_score,
            "critical": criterion.critical,
            "passed": score >= criterion.minimum_score,
            "agreement": agreement,
            "confidence": round(statistics.mean(value["confidence"] for value in values), 4),
            "judge_scores": scores,
            "evidence": sorted({item for value in values for item in value["evidence"]}),
            "remediation": criterion.remediation,
        }
        weighted_sum += score * criterion.weight

    gate_results = {
        gate: all(judge["hard_gates"][gate] for judge in judges)
        for gate in spec.evaluation.hard_gates
    }
    overall = round(weighted_sum / total_weight, 4)
    overall_agreement = round(
        statistics.mean(result["agreement"] for result in criterion_results.values()), 4
    )
    critical_failures = [
        criterion_id
        for criterion_id, result in criterion_results.items()
        if result["critical"] and not result["passed"]
    ]
    failed_gates = [gate for gate, passed in gate_results.items() if not passed]
    if failed_gates or critical_failures:
        status = "revise_required"
    elif overall_agreement < spec.evaluation.iteration.min_agreement:
        status = "adjudication_required"
    elif overall < spec.evaluation.iteration.accept_score:
        status = "revise_required"
    else:
        status = "accepted"

    return {
        "schema_version": "benchmark_builder.evaluation.v1",
        "task_id": spec.task_id,
        "spec_digest": spec_digest(spec),
        "submission_id": packet["submission_id"],
        "status": status,
        "overall_score": overall,
        "overall_agreement": overall_agreement,
        "accept_score": spec.evaluation.iteration.accept_score,
        "min_agreement": spec.evaluation.iteration.min_agreement,
        "criteria": criterion_results,
        "hard_gates": gate_results,
        "failed_gates": failed_gates,
        "critical_failures": critical_failures,
        "judge_ids": [judge["judge_id"] for judge in judges],
    }


def build_iteration_plan(
    spec: BenchmarkSpec, report: dict[str, Any], previous: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Turn an evaluation report into one controlled next-round action."""
    if report.get("task_id") != spec.task_id or report.get("spec_digest") != spec_digest(spec):
        raise EvaluationError("evaluation report does not match task spec")
    regressions: list[dict[str, Any]] = []
    if previous is not None:
        if previous.get("task_id") != spec.task_id:
            raise EvaluationError("previous evaluation report task_id does not match task spec")
        previous_criteria = previous.get("criteria", {})
        for criterion_id, result in report.get("criteria", {}).items():
            old = previous_criteria.get(criterion_id)
            if isinstance(old, dict) and result.get("score", 0) < old.get("score", 0):
                regressions.append(
                    {
                        "criterion": criterion_id,
                        "previous_score": old.get("score"),
                        "current_score": result.get("score"),
                    }
                )
        if len(regressions) > spec.evaluation.iteration.regressions_allowed:
            return {
                "schema_version": "benchmark_builder.iteration.v1",
                "task_id": spec.task_id,
                "parent_spec_digest": previous.get("spec_digest"),
                "current_spec_digest": spec_digest(spec),
                "evaluation_status": report.get("status"),
                "round_policy": spec.evaluation.iteration.to_dict(),
                "status": "rollback_required",
                "next_action": {
                    "type": "rollback",
                    "reason": "criterion-level regression exceeds configured allowance",
                    "regressions": regressions,
                },
                "invariants": [
                    "do not accept a higher aggregate score that hides a critical regression",
                    "restore the last accepted spec or adjudicate the regression",
                ],
            }

    if report.get("status") == "accepted":
        action = {"type": "freeze", "reason": "score, agreement, critical criteria, and hard gates passed"}
        status = "ready_for_freeze"
    elif report.get("status") == "adjudication_required":
        action = {
            "type": "adjudicate",
            "reason": "judge disagreement is above the configured tolerance",
            "required_inputs": ["independent expert adjudication", "criterion-specific evidence review"],
        }
        status = "needs_adjudication"
    else:
        failed = report.get("failed_gates", [])
        candidates = sorted(
            (
                (result["score"] - result["minimum_score"], criterion_id, result)
                for criterion_id, result in report.get("criteria", {}).items()
                if not result.get("passed", False)
            ),
            key=lambda item: item[0],
        )
        if candidates:
            _, criterion_id, result = candidates[0]
            action = {
                "type": "revise_task_or_verifier",
                "criterion": criterion_id,
                "reason": result.get("remediation", "criterion below minimum"),
                "evidence": result.get("evidence", []),
            }
        elif failed:
            action = {
                "type": "repair_release_gate",
                "gates": failed,
                "reason": "a hard gate failed; do not tune wording until the gate is repaired",
            }
        else:
            action = {
                "type": "revise_task_or_verifier",
                "reason": "overall score is below the acceptance threshold",
            }
        status = "iteration_required"
    return {
        "schema_version": "benchmark_builder.iteration.v1",
        "task_id": spec.task_id,
        "parent_spec_digest": spec_digest(spec),
        "evaluation_status": report.get("status"),
        "regressions": regressions,
        "round_policy": spec.evaluation.iteration.to_dict(),
        "status": status,
        "next_action": action,
        "invariants": [
            "change one causal factor per round when one_change_per_round is true",
            "preserve agent-visible/hidden-truth separation",
            "rerun all hard gates and holdout checks after every change",
            "record new spec digest and compare criterion-level regressions",
        ],
    }
