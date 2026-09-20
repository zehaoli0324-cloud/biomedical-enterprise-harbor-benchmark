from __future__ import annotations

from .models import BenchmarkSpec, DifficultyReport


def score_spec(spec: BenchmarkSpec) -> DifficultyReport:
    if spec.scenario_card is None:
        raise ValueError("difficulty scoring requires a linked scenario card")
    total_weight = sum(item.weight for item in spec.dimensions.values())
    raw = sum(item.level * item.weight for item in spec.dimensions.values()) / total_weight
    interactions: list[str] = []
    adjusted = raw

    def level(name: str) -> int:
        return spec.dimensions[name].level

    if level("long_horizon_complexity") >= 4 and level("tool_call_complexity") >= 4:
        adjusted += 0.20
        interactions.append("long_horizon_x_tool_orchestration")
    if level("scientific_judgment") >= 4 and level("information_noise_complexity") >= 4:
        adjusted += 0.20
        interactions.append("judgment_x_noisy_evidence")
    if level("data_complexity") >= 4 and level("environment_complexity") >= 4:
        adjusted += 0.15
        interactions.append("data_x_environment")
    if level("retrieval_complexity") >= 4 and level("scientific_judgment") >= 4:
        adjusted += 0.15
        interactions.append("retrieval_x_scientific_judgment")
    if level("safety_risk") >= 4:
        adjusted += 0.10
        interactions.append("high_stakes_safety_review")

    adjusted = min(5.0, round(adjusted, 3))
    if adjusted < 2:
        band = "introductory"
    elif adjusted < 3:
        band = "intermediate"
    elif adjusted < 4:
        band = "advanced"
    elif adjusted < 4.6:
        band = "research-grade"
    else:
        band = "frontier"

    return DifficultyReport(
        task_id=spec.task_id,
        raw_score=round(raw, 3),
        adjusted_score=adjusted,
        band=band,
        dimensions=spec.dimensions,
        interactions=tuple(interactions),
        selected_modules=spec.modules,
        data_types=spec.data_types,
    )
