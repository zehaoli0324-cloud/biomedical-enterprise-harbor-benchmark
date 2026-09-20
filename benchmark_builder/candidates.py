"""Candidate-card validation, multi-judge review, and Pareto selection."""

from __future__ import annotations

import hashlib
import json
import math
import statistics
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .config import load_spec
from .scoring import score_spec


CARD_KEYS = (
    "workflow_evidence",
    "scientific_scenario",
    "scientific_judgment",
    "difficulty",
    "compute",
)

CANDIDATE_CRITERIA = {
    "scientific_reality": {
        "minimum": 3.0,
        "weight": 1.4,
        "description": "A real researcher makes this decision and an error changes the research path.",
    },
    "research_value": {
        "minimum": 2.5,
        "weight": 1.0,
        "description": "The task measures a consequential capability rather than formatting or tool recall.",
    },
    "scientific_judgment": {
        "minimum": 3.0,
        "weight": 1.4,
        "description": "The task contains competing defensible choices, assumptions, or stopping decisions.",
    },
    "observability": {
        "minimum": 3.0,
        "weight": 1.2,
        "description": "Agent-visible evidence is sufficient to act without exposing hidden truth.",
    },
    "verifiability": {
        "minimum": 3.0,
        "weight": 1.4,
        "description": "Important decisions and artifacts have independent oracle, invariant, or rubric routes.",
    },
    "naive_resistance": {
        "minimum": 2.5,
        "weight": 1.1,
        "description": "Lookup, output volume, tool-name matching, and obvious leakage do not solve the task.",
    },
    "compute_feasibility": {
        "minimum": 2.0,
        "weight": 0.8,
        "description": "The environment, resource budget, and failure behavior can be materialized and rerun.",
    },
    "reproducibility": {
        "minimum": 2.5,
        "weight": 1.0,
        "description": "Inputs, versions, parameters, resources, and stochastic behavior can be frozen.",
    },
    "calibrated_difficulty": {
        "minimum": 3.0,
        "weight": 1.2,
        "description": "Difficulty comes from scientific judgment and dependent reasoning, not gratuitous volume.",
    },
}

CANDIDATE_HARD_GATES = (
    "scientific_reality",
    "observability",
    "verifiability",
    "claim_safety",
    "no_hidden_truth_leakage",
    "executable_with_budget",
)

CANDIDATE_JUDGES = (
    {"id": "domain_scientist", "role": "domain scientist"},
    {"id": "benchmark_methodologist", "role": "benchmark and measurement methodologist"},
    {"id": "execution_auditor", "role": "compute, verifier, and reproducibility auditor"},
)

PARETO_CRITERIA = (
    "scientific_reality",
    "scientific_judgment",
    "verifiability",
    "naive_resistance",
    "compute_feasibility",
    "calibrated_difficulty",
)

ITERATION_CARD = {
    "scientific_reality": "scientific_scenario",
    "research_value": "scientific_scenario",
    "scientific_judgment": "scientific_judgment",
    "observability": "workflow_evidence",
    "verifiability": "scientific_judgment",
    "naive_resistance": "difficulty",
    "compute_feasibility": "compute",
    "reproducibility": "compute",
    "calibrated_difficulty": "difficulty",
    "claim_safety": "scientific_judgment",
    "no_hidden_truth_leakage": "workflow_evidence",
    "executable_with_budget": "compute",
}


class CandidateError(ValueError):
    """Raised when candidate cards or judge results violate their contract."""


@dataclass(frozen=True)
class CandidateBundle:
    candidate_id: str
    design_intent: str
    scenario_family: str
    paths: dict[str, Path]
    digests: dict[str, str]
    task_id: str
    scenario_id: str
    difficulty_score: float

    def public_dict(self) -> dict[str, Any]:
        return {
            "candidate_id": self.candidate_id,
            "design_intent": self.design_intent,
            "scenario_family": self.scenario_family,
            "task_id": self.task_id,
            "scenario_id": self.scenario_id,
            "difficulty_score": self.difficulty_score,
            "cards": {name: str(path) for name, path in self.paths.items()},
            "card_digests": dict(self.digests),
        }


@dataclass(frozen=True)
class CandidateSet:
    path: Path
    workflow_id: str
    candidates: tuple[CandidateBundle, ...]
    digest: str


def _read_json(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise CandidateError(f"{label} is not valid JSON: {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise CandidateError(f"{label} must be a JSON object: {path}")
    return value


def _nonempty_strings(value: Any, label: str) -> list[str]:
    if not isinstance(value, list) or not value or not all(isinstance(item, str) and item for item in value):
        raise CandidateError(f"{label} must be a non-empty list of strings")
    return value


def _resolve(base: Path, value: Any, label: str) -> Path:
    if not isinstance(value, str) or not value:
        raise CandidateError(f"{label} must be a non-empty path")
    path = Path(value)
    if not path.is_absolute():
        path = base / path
    path = path.resolve()
    if not path.is_file():
        raise CandidateError(f"{label} does not exist: {path}")
    return path


def _file_digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _validate_evidence_card(card: dict[str, Any], path: Path, workflow_id: str) -> None:
    if card.get("schema_version") != "workflow-evidence-card.v1":
        raise CandidateError(f"unsupported workflow evidence card schema: {path}")
    if card.get("workflow_id") != workflow_id:
        raise CandidateError(f"workflow evidence card does not match workflow_id: {path}")
    _nonempty_strings(card.get("operations"), f"{path}.operations")
    sources = card.get("sources")
    if not isinstance(sources, list) or not sources:
        raise CandidateError(f"{path}.sources must be a non-empty list")
    for index, source in enumerate(sources):
        if not isinstance(source, dict):
            raise CandidateError(f"{path}.sources[{index}] must be an object")
        for field in ("locator", "evidence_tier", "verification_status"):
            if not isinstance(source.get(field), str) or not source[field]:
                raise CandidateError(f"{path}.sources[{index}].{field} is required")
    _nonempty_strings(card.get("unsupported_inferences"), f"{path}.unsupported_inferences")


def _validate_judgment_card(
    card: dict[str, Any], path: Path, task_id: str, scenario_id: str, expected_ids: set[str]
) -> None:
    if card.get("schema_version") != "scientific-judgment-card.v1":
        raise CandidateError(f"unsupported scientific judgment card schema: {path}")
    if card.get("task_id") != task_id or card.get("scenario_id") != scenario_id:
        raise CandidateError(f"scientific judgment card task/scenario mismatch: {path}")
    values = card.get("judgments")
    if not isinstance(values, list) or not values:
        raise CandidateError(f"{path}.judgments must be a non-empty list")
    seen: set[str] = set()
    for index, value in enumerate(values):
        if not isinstance(value, dict):
            raise CandidateError(f"{path}.judgments[{index}] must be an object")
        for field in ("id", "decision", "failure_consequence", "observable", "verifier", "claim_boundary"):
            if not isinstance(value.get(field), str) or not value[field]:
                raise CandidateError(f"{path}.judgments[{index}].{field} is required")
        if value["id"] in seen:
            raise CandidateError(f"duplicate scientific judgment {value['id']}: {path}")
        seen.add(value["id"])
    missing = expected_ids - seen
    if missing:
        raise CandidateError(f"scientific judgment card does not cover scenario judgments: {sorted(missing)}")


def _validate_compute_card(card: dict[str, Any], path: Path, task_id: str, constraints: dict[str, Any]) -> None:
    if card.get("schema_version") != "compute-card.v1":
        raise CandidateError(f"unsupported compute card schema: {path}")
    if card.get("task_id") != task_id:
        raise CandidateError(f"compute card task_id mismatch: {path}")
    environment = card.get("environment")
    if not isinstance(environment, dict) or environment.get("network") not in {"off", "restricted", "on"}:
        raise CandidateError(f"{path}.environment.network must be off, restricted, or on")
    budget = card.get("resource_budget")
    if not isinstance(budget, dict):
        raise CandidateError(f"{path}.resource_budget must be an object")
    for field in ("cpu_seconds", "memory_mb", "storage_mb"):
        value = budget.get(field)
        if isinstance(value, bool) or not isinstance(value, (int, float)) or value <= 0:
            raise CandidateError(f"{path}.resource_budget.{field} must be positive")
    for field in ("cpu_seconds", "memory_mb"):
        if field in constraints and float(constraints[field]) != float(budget[field]):
            raise CandidateError(f"compute card {field} does not match difficulty config constraints")
    if "network" in constraints and constraints["network"] != environment["network"]:
        raise CandidateError("compute card network does not match difficulty config constraints")
    stages = card.get("stages")
    if not isinstance(stages, list) or not stages:
        raise CandidateError(f"{path}.stages must be a non-empty list")
    for index, stage in enumerate(stages):
        if not isinstance(stage, dict):
            raise CandidateError(f"{path}.stages[{index}] must be an object")
        for field in ("id", "inputs", "outputs", "failure_behavior"):
            if field not in stage:
                raise CandidateError(f"{path}.stages[{index}].{field} is required")
        _nonempty_strings(stage["inputs"], f"{path}.stages[{index}].inputs")
        _nonempty_strings(stage["outputs"], f"{path}.stages[{index}].outputs")
    _nonempty_strings(card.get("programmatic_checks"), f"{path}.programmatic_checks")


def load_candidate_set(path: str | Path, catalog_path: str | Path | None = None) -> CandidateSet:
    manifest_path = Path(path).resolve()
    raw = _read_json(manifest_path, "candidate set")
    if raw.get("schema_version") != "benchmark-candidate-set.v1":
        raise CandidateError("unsupported candidate set schema")
    workflow_id = raw.get("workflow_id")
    if not isinstance(workflow_id, str) or not workflow_id:
        raise CandidateError("candidate set requires workflow_id")
    entries = raw.get("candidates")
    if not isinstance(entries, list) or not 2 <= len(entries) <= 8:
        raise CandidateError("candidate set requires between 2 and 8 candidates")

    seen: set[str] = set()
    bundles: list[CandidateBundle] = []
    digest_payload: dict[str, Any] = {"manifest": raw, "cards": {}}
    for index, entry in enumerate(entries):
        if not isinstance(entry, dict):
            raise CandidateError(f"candidates[{index}] must be an object")
        candidate_id = entry.get("candidate_id")
        if not isinstance(candidate_id, str) or not candidate_id or candidate_id in seen:
            raise CandidateError(f"candidate_id must be non-empty and unique: {candidate_id!r}")
        for field in ("design_intent", "scenario_family"):
            if not isinstance(entry.get(field), str) or not entry[field]:
                raise CandidateError(f"{candidate_id}.{field} must be a non-empty string")
        seen.add(candidate_id)
        cards = entry.get("cards")
        if not isinstance(cards, dict) or any(key not in cards for key in CARD_KEYS):
            raise CandidateError(f"{candidate_id}.cards must reference all card types: {CARD_KEYS}")
        paths = {
            key: _resolve(manifest_path.parent, cards[key], f"{candidate_id}.cards.{key}")
            for key in CARD_KEYS
        }
        evidence = _read_json(paths["workflow_evidence"], "workflow evidence card")
        judgment = _read_json(paths["scientific_judgment"], "scientific judgment card")
        compute = _read_json(paths["compute"], "compute card")
        try:
            spec = load_spec(paths["difficulty"], catalog_path)
            difficulty_report = score_spec(spec)
        except (OSError, TypeError, ValueError) as exc:
            raise CandidateError(f"invalid difficulty card for {candidate_id}: {exc}") from exc
        if spec.task_id != candidate_id:
            raise CandidateError(f"candidate_id must equal difficulty task id: {candidate_id} != {spec.task_id}")
        if spec.scenario_card is None or Path(spec.scenario_card.path) != paths["scientific_scenario"]:
            raise CandidateError(f"{candidate_id} difficulty card must link to its scientific scenario card")
        _validate_evidence_card(evidence, paths["workflow_evidence"], workflow_id)
        _validate_judgment_card(
            judgment,
            paths["scientific_judgment"],
            spec.task_id,
            spec.scenario_card.scenario_id,
            set(spec.scenario_card.scientific_judgments),
        )
        _validate_compute_card(compute, paths["compute"], spec.task_id, spec.constraints)
        digests = {name: _file_digest(card_path) for name, card_path in paths.items()}
        digest_payload["cards"][candidate_id] = digests
        bundles.append(
            CandidateBundle(
                candidate_id=candidate_id,
                design_intent=str(entry.get("design_intent", "")),
                scenario_family=str(entry.get("scenario_family", spec.scenario_card.scenario_id)),
                paths=paths,
                digests=digests,
                task_id=spec.task_id,
                scenario_id=spec.scenario_card.scenario_id,
                difficulty_score=difficulty_report.adjusted_score,
            )
        )
    encoded = json.dumps(digest_payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
    return CandidateSet(manifest_path, workflow_id, tuple(bundles), hashlib.sha256(encoded).hexdigest())


def candidate_protocol(candidate_set: CandidateSet) -> dict[str, Any]:
    return {
        "schema_version": "benchmark-candidate-review.v1",
        "workflow_id": candidate_set.workflow_id,
        "candidate_set_digest": candidate_set.digest,
        "review_design": {
            "blind_independent_review": True,
            "judge_roles": list(CANDIDATE_JUDGES),
            "scale": {"min": 0.0, "max": 4.0},
            "criteria": CANDIDATE_CRITERIA,
            "hard_gates": list(CANDIDATE_HARD_GATES),
            "selection": "hard gates, criterion floors, agreement check, Pareto front, declared-weight tie-break",
        },
        "candidates": [candidate.public_dict() for candidate in candidate_set.candidates],
        "judge_instructions": [
            "Review each card and cited source; do not reward prose polish or artifact volume.",
            "Score scientific reality separately from difficulty and compute feasibility.",
            "Fail verifiability when a plausible answer cannot be independently distinguished from a correct answer.",
            "Fail calibrated_difficulty when burden comes mainly from scale, token count, or redundant tools.",
            "Record evidence locators and a falsifiable concern for every score below its minimum.",
            "Do not view another judge's scores before submitting the review.",
        ],
        "output_contract": {
            "workflow_id": "string",
            "candidate_set_digest": "string",
            "judges": [
                {
                    "judge_id": "one configured judge id",
                    "candidates": {
                        "<candidate_id>": {
                            "criteria": {
                                "<criterion_id>": {
                                    "score": "number from 0 to 4",
                                    "confidence": "number from 0 to 1",
                                    "evidence": ["card path plus field or source locator"],
                                    "rationale": "evidence-grounded explanation",
                                }
                            },
                            "hard_gates": {"<gate_id>": "boolean"},
                            "concerns": ["falsifiable concern or missing evidence"],
                        }
                    },
                }
            ],
        },
    }


def _number(value: Any, label: str, lower: float, upper: float) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise CandidateError(f"{label} must be a finite number")
    value = float(value)
    if not lower <= value <= upper:
        raise CandidateError(f"{label} must be between {lower} and {upper}")
    return value


def _agreement(scores: list[float]) -> float:
    if len(scores) <= 1:
        return 1.0
    return round(max(0.0, min(1.0, 1.0 - statistics.pstdev(scores) / 4.0)), 4)


def _load_reviews(path: str | Path, candidate_set: CandidateSet) -> list[dict[str, Any]]:
    raw = _read_json(Path(path), "candidate review packet")
    if raw.get("workflow_id") != candidate_set.workflow_id:
        raise CandidateError("review packet workflow_id does not match candidate set")
    if raw.get("candidate_set_digest") != candidate_set.digest:
        raise CandidateError("review packet candidate_set_digest does not match candidate set")
    judges = raw.get("judges")
    if not isinstance(judges, list):
        raise CandidateError("review packet requires judges list")
    expected_judges = {judge["id"] for judge in CANDIDATE_JUDGES}
    expected_candidates = {candidate.candidate_id for candidate in candidate_set.candidates}
    seen: set[str] = set()
    checked: list[dict[str, Any]] = []
    for judge in judges:
        if not isinstance(judge, dict) or judge.get("judge_id") not in expected_judges:
            raise CandidateError("review packet has unknown judge")
        judge_id = judge["judge_id"]
        if judge_id in seen:
            raise CandidateError(f"duplicate candidate judge: {judge_id}")
        seen.add(judge_id)
        values = judge.get("candidates")
        if not isinstance(values, dict) or set(values) != expected_candidates:
            raise CandidateError(f"{judge_id} must review every candidate exactly once")
        judge_result: dict[str, Any] = {"judge_id": judge_id, "candidates": {}}
        for candidate_id, value in values.items():
            if not isinstance(value, dict) or not isinstance(value.get("criteria"), dict):
                raise CandidateError(f"{judge_id}.{candidate_id} requires criteria")
            criterion_result: dict[str, Any] = {}
            for criterion_id in CANDIDATE_CRITERIA:
                criterion = value["criteria"].get(criterion_id)
                if not isinstance(criterion, dict):
                    raise CandidateError(f"{judge_id}.{candidate_id} missing {criterion_id}")
                evidence = criterion.get("evidence")
                if not isinstance(evidence, list) or not all(isinstance(item, str) and item for item in evidence):
                    raise CandidateError(f"{judge_id}.{candidate_id}.{criterion_id}.evidence must be strings")
                criterion_result[criterion_id] = {
                    "score": _number(criterion.get("score"), f"{judge_id}.{candidate_id}.{criterion_id}.score", 0, 4),
                    "confidence": _number(
                        criterion.get("confidence"), f"{judge_id}.{candidate_id}.{criterion_id}.confidence", 0, 1
                    ),
                    "evidence": evidence,
                    "rationale": str(criterion.get("rationale", "")),
                }
            gates = value.get("hard_gates")
            if not isinstance(gates, dict):
                raise CandidateError(f"{judge_id}.{candidate_id} requires hard_gates")
            checked_gates = {gate: gates.get(gate) is True for gate in CANDIDATE_HARD_GATES}
            concerns = value.get("concerns", [])
            if not isinstance(concerns, list) or not all(isinstance(item, str) for item in concerns):
                raise CandidateError(f"{judge_id}.{candidate_id}.concerns must be strings")
            judge_result["candidates"][candidate_id] = {
                "criteria": criterion_result,
                "hard_gates": checked_gates,
                "concerns": concerns,
            }
        checked.append(judge_result)
    missing = expected_judges - seen
    if missing:
        raise CandidateError(f"missing required candidate judges: {sorted(missing)}")
    return checked


def _dominates(left: dict[str, Any], right: dict[str, Any]) -> bool:
    left_scores = left["criteria"]
    right_scores = right["criteria"]
    no_worse = all(left_scores[key]["score"] >= right_scores[key]["score"] for key in PARETO_CRITERIA)
    strictly_better = any(left_scores[key]["score"] > right_scores[key]["score"] for key in PARETO_CRITERIA)
    return no_worse and strictly_better


def select_candidates(
    candidate_set: CandidateSet, reviews_path: str | Path, min_agreement: float = 0.75
) -> dict[str, Any]:
    judges = _load_reviews(reviews_path, candidate_set)
    results: dict[str, Any] = {}
    for candidate in candidate_set.candidates:
        criteria: dict[str, Any] = {}
        for criterion_id, definition in CANDIDATE_CRITERIA.items():
            values = [judge["candidates"][candidate.candidate_id]["criteria"][criterion_id] for judge in judges]
            scores = [value["score"] for value in values]
            score = round(statistics.median(scores), 4)
            criteria[criterion_id] = {
                "score": score,
                "minimum": definition["minimum"],
                "passed": score >= definition["minimum"],
                "agreement": _agreement(scores),
                "confidence": round(statistics.mean(value["confidence"] for value in values), 4),
                "judge_scores": scores,
                "evidence": sorted({item for value in values for item in value["evidence"]}),
                "judge_rationales": [value["rationale"] for value in values],
            }
        gates = {
            gate: all(judge["candidates"][candidate.candidate_id]["hard_gates"][gate] for judge in judges)
            for gate in CANDIDATE_HARD_GATES
        }
        failed_gates = [gate for gate, passed in gates.items() if not passed]
        failed_criteria = [key for key, value in criteria.items() if not value["passed"]]
        agreement = round(statistics.mean(value["agreement"] for value in criteria.values()), 4)
        minimum_agreement = min(value["agreement"] for value in criteria.values())
        weighted_score = round(
            sum(criteria[key]["score"] * definition["weight"] for key, definition in CANDIDATE_CRITERIA.items())
            / sum(definition["weight"] for definition in CANDIDATE_CRITERIA.values()),
            4,
        )
        results[candidate.candidate_id] = {
            "candidate": candidate.public_dict(),
            "eligible": not failed_gates and not failed_criteria,
            "criteria": criteria,
            "hard_gates": gates,
            "failed_gates": failed_gates,
            "failed_criteria": failed_criteria,
            "overall_agreement": agreement,
            "minimum_criterion_agreement": minimum_agreement,
            "weighted_score": weighted_score,
            "concerns": sorted(
                {
                    concern
                    for judge in judges
                    for concern in judge["candidates"][candidate.candidate_id]["concerns"]
                    if concern
                }
            ),
        }

    eligible = [candidate_id for candidate_id, value in results.items() if value["eligible"]]
    pareto = [
        candidate_id
        for candidate_id in eligible
        if not any(
            other_id != candidate_id and _dominates(results[other_id], results[candidate_id])
            for other_id in eligible
        )
    ]
    agreed_front = [
        candidate_id
        for candidate_id in pareto
        if results[candidate_id]["minimum_criterion_agreement"] >= min_agreement
    ]
    if not eligible:
        status = "no_eligible_candidate"
        recommended = None
    elif not agreed_front:
        status = "adjudication_required"
        recommended = None
    else:
        status = "selected"
        recommended = sorted(
            agreed_front,
            key=lambda candidate_id: (
                -results[candidate_id]["weighted_score"],
                -results[candidate_id]["overall_agreement"],
                candidate_id,
            ),
        )[0]
    return {
        "schema_version": "benchmark-candidate-selection.v1",
        "workflow_id": candidate_set.workflow_id,
        "candidate_set_digest": candidate_set.digest,
        "status": status,
        "min_agreement": min_agreement,
        "eligible_candidates": eligible,
        "pareto_criteria": list(PARETO_CRITERIA),
        "pareto_front": pareto,
        "recommended_candidate": recommended,
        "selection_rule": "hard gates and floors -> Pareto front -> agreement -> declared-weight tie-break",
        "candidates": results,
    }


def build_candidate_iteration_plan(candidate_set: CandidateSet, report: dict[str, Any]) -> dict[str, Any]:
    if report.get("workflow_id") != candidate_set.workflow_id or report.get("candidate_set_digest") != candidate_set.digest:
        raise CandidateError("selection report does not match candidate set")
    status = report.get("status")
    if status == "selected":
        candidate_id = report.get("recommended_candidate")
        action = {
            "type": "compile_and_trial",
            "candidate_id": candidate_id,
            "difficulty_card": report["candidates"][candidate_id]["candidate"]["cards"]["difficulty"],
            "reason": "candidate passed gates, floors, agreement, and Pareto selection",
        }
        plan_status = "ready_for_compile"
    elif status == "adjudication_required":
        action = {
            "type": "independent_adjudication",
            "candidate_ids": report.get("pareto_front", []),
            "reason": "no Pareto-front candidate met the agreement threshold",
        }
        plan_status = "needs_adjudication"
    else:
        candidates = report.get("candidates", {})
        if not candidates:
            raise CandidateError("selection report has no candidate results")
        candidate_id = sorted(
            candidates,
            key=lambda key: (
                len(candidates[key].get("failed_gates", [])),
                sum(
                    max(0.0, value["minimum"] - value["score"])
                    for value in candidates[key].get("criteria", {}).values()
                ),
                -candidates[key].get("weighted_score", 0),
                key,
            ),
        )[0]
        candidate = candidates[candidate_id]
        if candidate.get("failed_gates"):
            target = candidate["failed_gates"][0]
            reason = f"repair failed hard gate: {target}"
        else:
            failed = candidate.get("failed_criteria", [])
            if not failed:
                raise CandidateError("no eligible candidate but report contains no failed gate or criterion")
            target = min(
                failed,
                key=lambda key: candidate["criteria"][key]["score"] - candidate["criteria"][key]["minimum"],
            )
            reason = f"repair weakest criterion: {target}"
        action = {
            "type": "revise_one_card",
            "candidate_id": candidate_id,
            "target": target,
            "card": ITERATION_CARD[target],
            "reason": reason,
            "evidence": candidate.get("criteria", {}).get(target, {}).get("evidence", []),
            "concerns": candidate.get("concerns", []),
        }
        plan_status = "iteration_required"
    return {
        "schema_version": "benchmark-candidate-iteration.v1",
        "workflow_id": candidate_set.workflow_id,
        "parent_candidate_set_digest": candidate_set.digest,
        "selection_status": status,
        "status": plan_status,
        "next_action": action,
        "invariants": [
            "change only the named card and one causal defect in this round",
            "refresh the candidate-set digest and all three independent reviews",
            "preserve source locators and agent-visible/hidden-truth separation",
            "rerun card validation before candidate review",
        ],
    }
