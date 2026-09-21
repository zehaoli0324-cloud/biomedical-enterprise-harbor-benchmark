from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


DIMENSIONS = (
    "scientific_scenario",
    "scientific_judgment",
    "computational_difficulty",
    "tool_call_complexity",
    "retrieval_complexity",
    "information_noise_complexity",
    "data_type_complexity",
    "data_complexity",
    "environment_complexity",
    "mathematical_complexity",
    "long_horizon_complexity",
    "safety_risk",
)

EVALUATION_CRITERIA = (
    "scientific_correctness",
    "evidence_grounding",
    "experimental_design",
    "tool_and_trace_reliability",
    "artifact_completeness",
    "reproducibility",
    "uncertainty_and_claim_boundary",
    "safety_and_human_review",
)


@dataclass(frozen=True)
class DifficultyDimension:
    level: int
    weight: float = 1.0
    rationale: str = ""
    tags: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "level": self.level,
            "weight": self.weight,
            "rationale": self.rationale,
            "tags": list(self.tags),
        }


@dataclass(frozen=True)
class ModuleSelection:
    module_id: str
    params: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {"id": self.module_id, "params": self.params}


@dataclass(frozen=True)
class ScenarioCard:
    path: str
    digest: str
    scenario_id: str
    status: str
    source_scenarios: tuple[str, ...]
    scientific_judgments: tuple[str, ...]
    handoff_count: int
    release_gates: dict[str, str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "digest": self.digest,
            "scenario_id": self.scenario_id,
            "status": self.status,
            "source_scenarios": list(self.source_scenarios),
            "scientific_judgments": list(self.scientific_judgments),
            "handoff_count": self.handoff_count,
            "release_gates": dict(self.release_gates),
        }


@dataclass(frozen=True)
class BenchmarkSpec:
    task_id: str
    title: str
    domain: str
    source_scenarios: tuple[str, ...]
    dimensions: dict[str, DifficultyDimension]
    modules: dict[str, tuple[ModuleSelection, ...]]
    data_types: tuple[str, ...]
    constraints: dict[str, Any] = field(default_factory=dict)
    evaluation: "EvaluationSpec" = field(default_factory=lambda: EvaluationSpec.default())
    scenario_card: ScenarioCard | None = None
    evidence: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class EvaluationCriterion:
    criterion_id: str
    weight: float
    minimum_score: float
    critical: bool = False
    description: str = ""
    remediation: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.criterion_id,
            "weight": self.weight,
            "minimum_score": self.minimum_score,
            "critical": self.critical,
            "description": self.description,
            "remediation": self.remediation,
        }


@dataclass(frozen=True)
class JudgeRole:
    judge_id: str
    role: str
    required: bool = True
    model: str = "external"
    temperature: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.judge_id,
            "role": self.role,
            "required": self.required,
            "model": self.model,
            "temperature": self.temperature,
        }


@dataclass(frozen=True)
class IterationPolicy:
    max_rounds: int = 3
    min_agreement: float = 0.7
    accept_score: float = 3.0
    regressions_allowed: int = 0
    one_change_per_round: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "max_rounds": self.max_rounds,
            "min_agreement": self.min_agreement,
            "accept_score": self.accept_score,
            "regressions_allowed": self.regressions_allowed,
            "one_change_per_round": self.one_change_per_round,
        }


@dataclass(frozen=True)
class EvaluationSpec:
    scale_min: float
    scale_max: float
    criteria: tuple[EvaluationCriterion, ...]
    judges: tuple[JudgeRole, ...]
    hard_gates: tuple[str, ...]
    iteration: IterationPolicy

    @classmethod
    def default(cls) -> "EvaluationSpec":
        descriptions = {
            "scientific_correctness": "Correct experimental unit, model, contrast, result and scientific decision.",
            "evidence_grounding": "Claims, numbers and citations are traceable and actually entailed.",
            "experimental_design": "Controls, batches, replicates, stopping rules and sensitivity choices are valid.",
            "tool_and_trace_reliability": "Tools, parameters, order, failures and recovery are faithfully recorded.",
            "artifact_completeness": "Required intermediate and final artifacts are present and schema-valid.",
            "reproducibility": "Versions, inputs, checksums, resources and rerun conditions are sufficient.",
            "uncertainty_and_claim_boundary": "Uncertainty, negative results and association/causality limits are explicit.",
            "safety_and_human_review": "High-risk boundaries and required human review are respected.",
        }
        criteria = tuple(
            EvaluationCriterion(
                criterion_id=criterion_id,
                weight=1.0,
                minimum_score=2.0,
                critical=criterion_id in {"scientific_correctness", "uncertainty_and_claim_boundary"},
                description=descriptions[criterion_id],
                remediation="Review the task instruction, evidence contract, and verifier for this criterion.",
            )
            for criterion_id in EVALUATION_CRITERIA
        )
        judges = (
            JudgeRole("domain_scientist", "domain scientist", True),
            JudgeRole("methods_auditor", "methods and reproducibility auditor", True),
            JudgeRole("evidence_auditor", "evidence and claim auditor", True),
        )
        return cls(0.0, 4.0, criteria, judges, ("scientific_reality", "observability", "verifiability"), IterationPolicy())

    def to_dict(self) -> dict[str, Any]:
        return {
            "scale": {"min": self.scale_min, "max": self.scale_max},
            "criteria": [criterion.to_dict() for criterion in self.criteria],
            "judges": [judge.to_dict() for judge in self.judges],
            "hard_gates": list(self.hard_gates),
            "iteration": self.iteration.to_dict(),
        }


@dataclass(frozen=True)
class DifficultyReport:
    task_id: str
    raw_score: float
    adjusted_score: float
    band: str
    dimensions: dict[str, DifficultyDimension]
    interactions: tuple[str, ...]
    selected_modules: dict[str, tuple[ModuleSelection, ...]]
    data_types: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "raw_score": self.raw_score,
            "adjusted_score": self.adjusted_score,
            "band": self.band,
            "dimensions": {key: value.to_dict() for key, value in self.dimensions.items()},
            "interactions": list(self.interactions),
            "selected_modules": {
                key: [item.to_dict() for item in values]
                for key, values in self.selected_modules.items()
            },
            "data_types": list(self.data_types),
        }
