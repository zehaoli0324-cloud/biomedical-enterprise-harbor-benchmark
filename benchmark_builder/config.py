from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Any

from .catalog import index_modules, load_catalog
from .models import (
    BenchmarkSpec,
    DifficultyDimension,
    DIMENSIONS,
    EVALUATION_CRITERIA,
    EvaluationCriterion,
    EvaluationSpec,
    IterationPolicy,
    JudgeRole,
    ModuleSelection,
)
from .scenario import load_scenario_card, validate_scenario_link


def _as_module(value: Any) -> ModuleSelection:
    if isinstance(value, str):
        return ModuleSelection(value)
    if isinstance(value, dict) and isinstance(value.get("id"), str):
        params = value.get("params", {})
        if not isinstance(params, dict):
            raise ValueError(f"Module params must be a table: {value!r}")
        return ModuleSelection(value["id"], params)
    raise ValueError(f"Invalid module selection: {value!r}")


def _load_evaluation(raw: Any) -> EvaluationSpec:
    if raw is None:
        return EvaluationSpec.default()
    if not isinstance(raw, dict):
        raise ValueError("[evaluation] must be a table")

    scale = raw.get("scale", {})
    if not isinstance(scale, dict):
        raise ValueError("[evaluation.scale] must be a table")
    scale_min = scale.get("min", 0.0)
    scale_max = scale.get("max", 4.0)
    if not isinstance(scale_min, (int, float)) or not isinstance(scale_max, (int, float)) or scale_min >= scale_max:
        raise ValueError("evaluation scale requires min < max")

    raw_criteria = raw.get("criteria")
    if raw_criteria is None:
        criteria = EvaluationSpec.default().criteria
    else:
        if not isinstance(raw_criteria, list) or not raw_criteria:
            raise ValueError("evaluation.criteria must be a non-empty array of tables")
        criteria_list: list[EvaluationCriterion] = []
        seen: set[str] = set()
        for value in raw_criteria:
            if not isinstance(value, dict) or not isinstance(value.get("id"), str):
                raise ValueError(f"Invalid evaluation criterion: {value!r}")
            criterion_id = value["id"]
            if criterion_id in seen or criterion_id not in EVALUATION_CRITERIA:
                raise ValueError(f"Unknown or duplicate evaluation criterion: {criterion_id}")
            seen.add(criterion_id)
            weight = value.get("weight", 1.0)
            minimum_score = value.get("minimum_score", scale_min)
            if not isinstance(weight, (int, float)) or weight <= 0:
                raise ValueError(f"{criterion_id}.weight must be positive")
            if not isinstance(minimum_score, (int, float)) or not scale_min <= minimum_score <= scale_max:
                raise ValueError(f"{criterion_id}.minimum_score must be within evaluation scale")
            criteria_list.append(
                EvaluationCriterion(
                    criterion_id=criterion_id,
                    weight=float(weight),
                    minimum_score=float(minimum_score),
                    critical=bool(value.get("critical", False)),
                    description=str(value.get("description", "")),
                    remediation=str(value.get("remediation", "")),
                )
            )
        criteria = tuple(criteria_list)

    raw_judges = raw.get("judges")
    if raw_judges is None:
        judges = EvaluationSpec.default().judges
    else:
        if not isinstance(raw_judges, list) or not raw_judges:
            raise ValueError("evaluation.judges must be a non-empty array of tables")
        judges_list: list[JudgeRole] = []
        seen_judges: set[str] = set()
        for value in raw_judges:
            if not isinstance(value, dict) or not isinstance(value.get("id"), str) or not isinstance(value.get("role"), str):
                raise ValueError(f"Invalid evaluation judge: {value!r}")
            judge_id = value["id"]
            if judge_id in seen_judges:
                raise ValueError(f"Duplicate evaluation judge: {judge_id}")
            seen_judges.add(judge_id)
            temperature = value.get("temperature", 0.0)
            if not isinstance(temperature, (int, float)) or not 0 <= temperature <= 1:
                raise ValueError(f"{judge_id}.temperature must be between 0 and 1")
            judges_list.append(
                JudgeRole(
                    judge_id=judge_id,
                    role=value["role"],
                    required=bool(value.get("required", True)),
                    model=str(value.get("model", "external")),
                    temperature=float(temperature),
                )
            )
        judges = tuple(judges_list)

    hard_gates = raw.get("hard_gates", EvaluationSpec.default().hard_gates)
    if not isinstance(hard_gates, list) or not all(isinstance(item, str) and item for item in hard_gates):
        raise ValueError("evaluation.hard_gates must be a list of non-empty strings")

    raw_iteration = raw.get("iteration", {})
    if not isinstance(raw_iteration, dict):
        raise ValueError("[evaluation.iteration] must be a table")
    iteration = IterationPolicy(
        max_rounds=int(raw_iteration.get("max_rounds", 3)),
        min_agreement=float(raw_iteration.get("min_agreement", 0.7)),
        accept_score=float(raw_iteration.get("accept_score", 3.0)),
        regressions_allowed=int(raw_iteration.get("regressions_allowed", 0)),
        one_change_per_round=bool(raw_iteration.get("one_change_per_round", True)),
    )
    if iteration.max_rounds < 1 or not 0 <= iteration.min_agreement <= 1:
        raise ValueError("evaluation iteration has invalid max_rounds or min_agreement")
    if not scale_min <= iteration.accept_score <= scale_max:
        raise ValueError("evaluation.iteration.accept_score must be within evaluation scale")

    return EvaluationSpec(scale_min, scale_max, criteria, judges, tuple(hard_gates), iteration)


def load_spec(path: str | Path, catalog_path: str | Path | None = None) -> BenchmarkSpec:
    config_path = Path(path)
    with config_path.open("rb") as handle:
        raw = tomllib.load(handle)

    task = raw.get("task", {})
    if not task.get("id") or not task.get("title") or not task.get("domain"):
        raise ValueError("[task] requires id, title, and domain")

    raw_dimensions = raw.get("difficulty", {})
    dimensions: dict[str, DifficultyDimension] = {}
    unknown_dimensions = set(raw_dimensions) - set(DIMENSIONS)
    if unknown_dimensions:
        raise ValueError(f"Unknown difficulty dimensions: {sorted(unknown_dimensions)}")
    for name in DIMENSIONS:
        value = raw_dimensions.get(name)
        if value is None:
            raise ValueError(f"Missing difficulty dimension: {name}")
        if not isinstance(value, dict):
            raise ValueError(f"Difficulty dimension must be a table: {name}")
        level = value.get("level")
        if not isinstance(level, int) or not 1 <= level <= 5:
            raise ValueError(f"{name}.level must be an integer from 1 to 5")
        weight = value.get("weight", 1.0)
        if not isinstance(weight, (int, float)) or weight <= 0:
            raise ValueError(f"{name}.weight must be positive")
        tags = value.get("tags", [])
        if not isinstance(tags, list) or not all(isinstance(tag, str) for tag in tags):
            raise ValueError(f"{name}.tags must be a list of strings")
        dimensions[name] = DifficultyDimension(
            level=level,
            weight=float(weight),
            rationale=str(value.get("rationale", "")),
            tags=tuple(tags),
        )

    catalog = load_catalog(catalog_path)
    module_index = index_modules(catalog)
    raw_modules = raw.get("modules", {})
    modules: dict[str, tuple[ModuleSelection, ...]] = {}
    for category, values in raw_modules.items():
        if not isinstance(values, list):
            raise ValueError(f"Module category must be a list: {category}")
        selections = tuple(_as_module(value) for value in values)
        for selection in selections:
            if selection.module_id not in module_index:
                raise ValueError(f"Unknown module: {selection.module_id}")
            declared_category = module_index[selection.module_id].get("category")
            if declared_category != category:
                raise ValueError(
                    f"Module {selection.module_id} belongs to {declared_category}, not {category}"
                )
        modules[category] = selections

    data_types = raw.get("data", {}).get("types", [])
    if not isinstance(data_types, list) or not all(isinstance(item, str) for item in data_types):
        raise ValueError("[data].types must be a list of strings")

    scenario_card = None
    raw_scenario = raw.get("scenario", {})
    if not isinstance(raw_scenario, dict) or not raw_scenario.get("card"):
        raise ValueError("[scenario] card is required: difficulty generation must link to a scenario card")
    card_path = Path(raw_scenario["card"])
    if not card_path.is_absolute():
        card_path = config_path.parent.parent / card_path if not (config_path.parent / card_path).exists() else config_path.parent / card_path
    scenario_card = load_scenario_card(card_path)
    validate_scenario_link(scenario_card, tuple(task.get("source_scenarios", [])))

    return BenchmarkSpec(
        task_id=task["id"],
        title=task["title"],
        domain=task["domain"],
        source_scenarios=tuple(task.get("source_scenarios", [])),
        dimensions=dimensions,
        modules=modules,
        data_types=tuple(data_types),
        constraints=raw.get("constraints", {}),
        evaluation=_load_evaluation(raw.get("evaluation")),
        scenario_card=scenario_card,
    )
