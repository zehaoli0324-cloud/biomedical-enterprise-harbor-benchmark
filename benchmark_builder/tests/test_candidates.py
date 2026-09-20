import json
from pathlib import Path

import pytest

from benchmark_builder.candidates import (
    CANDIDATE_CRITERIA,
    CANDIDATE_HARD_GATES,
    CANDIDATE_JUDGES,
    CandidateBundle,
    CandidateError,
    CandidateSet,
    build_candidate_iteration_plan,
    candidate_protocol,
    load_candidate_set,
    select_candidates,
)


ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "candidate_pools/literature-screening-m1/candidate-set.json"


def _candidate_set(tmp_path: Path) -> CandidateSet:
    candidates = tuple(
        CandidateBundle(
            candidate_id=name,
            design_intent=f"intent {name}",
            scenario_family=f"family {name}",
            paths={key: tmp_path / f"{name}-{key}" for key in ("workflow_evidence", "scientific_scenario", "scientific_judgment", "difficulty", "compute")},
            digests={key: f"digest-{name}-{key}" for key in ("workflow_evidence", "scientific_scenario", "scientific_judgment", "difficulty", "compute")},
            task_id=name,
            scenario_id=f"scenario-{name}",
            difficulty_score=4.0,
        )
        for name in ("candidate-a", "candidate-b", "candidate-c")
    )
    return CandidateSet(tmp_path / "candidate-set.json", "workflow-1", candidates, "set-digest")


def _reviews(candidate_set: CandidateSet) -> dict:
    profiles = {
        "candidate-a": {key: 4.0 for key in CANDIDATE_CRITERIA},
        "candidate-b": {key: 3.0 for key in CANDIDATE_CRITERIA},
        "candidate-c": {key: 3.0 for key in CANDIDATE_CRITERIA},
    }
    profiles["candidate-a"]["verifiability"] = 3.0
    profiles["candidate-b"]["verifiability"] = 4.0
    return {
        "workflow_id": candidate_set.workflow_id,
        "candidate_set_digest": candidate_set.digest,
        "judges": [
            {
                "judge_id": judge["id"],
                "candidates": {
                    candidate.candidate_id: {
                        "criteria": {
                            criterion_id: {
                                "score": profiles[candidate.candidate_id][criterion_id],
                                "confidence": 0.9,
                                "evidence": [f"cards/{candidate.candidate_id}/{criterion_id}"],
                                "rationale": "Grounded in the linked card.",
                            }
                            for criterion_id in CANDIDATE_CRITERIA
                        },
                        "hard_gates": {gate: True for gate in CANDIDATE_HARD_GATES},
                        "concerns": [],
                    }
                    for candidate in candidate_set.candidates
                },
            }
            for judge in CANDIDATE_JUDGES
        ],
    }


def test_materialized_candidate_cards_validate_and_bind() -> None:
    candidate_set = load_candidate_set(MANIFEST)
    assert candidate_set.workflow_id == "M1-literature-screening"
    assert len(candidate_set.candidates) == 3
    candidate = candidate_set.candidates[0]
    assert candidate.task_id == "literature-screening-m1-001"
    assert candidate.difficulty_score >= 1
    protocol = candidate_protocol(candidate_set)
    assert protocol["candidate_set_digest"] == candidate_set.digest
    assert len(protocol["review_design"]["judge_roles"]) == 3


def test_selection_preserves_pareto_tradeoffs_and_recommends_one(tmp_path: Path) -> None:
    candidate_set = _candidate_set(tmp_path)
    packet_path = tmp_path / "reviews.json"
    packet_path.write_text(json.dumps(_reviews(candidate_set)), encoding="utf-8")
    report = select_candidates(candidate_set, packet_path)
    assert report["status"] == "selected"
    assert report["pareto_front"] == ["candidate-a", "candidate-b"]
    assert report["recommended_candidate"] == "candidate-a"
    assert "candidate-c" not in report["pareto_front"]
    plan = build_candidate_iteration_plan(candidate_set, report)
    assert plan["status"] == "ready_for_compile"


def test_failed_gate_cannot_be_averaged_away(tmp_path: Path) -> None:
    candidate_set = _candidate_set(tmp_path)
    packet = _reviews(candidate_set)
    packet["judges"][0]["candidates"]["candidate-a"]["hard_gates"]["scientific_reality"] = False
    packet_path = tmp_path / "reviews.json"
    packet_path.write_text(json.dumps(packet), encoding="utf-8")
    report = select_candidates(candidate_set, packet_path)
    assert not report["candidates"]["candidate-a"]["eligible"]
    assert report["recommended_candidate"] == "candidate-b"


def test_stale_candidate_reviews_are_rejected(tmp_path: Path) -> None:
    candidate_set = _candidate_set(tmp_path)
    packet = _reviews(candidate_set)
    packet["candidate_set_digest"] = "stale"
    packet_path = tmp_path / "reviews.json"
    packet_path.write_text(json.dumps(packet), encoding="utf-8")
    with pytest.raises(CandidateError, match="digest"):
        select_candidates(candidate_set, packet_path)


def test_iteration_targets_one_card_for_weakest_candidate(tmp_path: Path) -> None:
    candidate_set = _candidate_set(tmp_path)
    packet = _reviews(candidate_set)
    for judge in packet["judges"]:
        for candidate in judge["candidates"].values():
            candidate["criteria"]["verifiability"]["score"] = 1.0
    packet_path = tmp_path / "reviews.json"
    packet_path.write_text(json.dumps(packet), encoding="utf-8")
    report = select_candidates(candidate_set, packet_path)
    assert report["status"] == "no_eligible_candidate"
    plan = build_candidate_iteration_plan(candidate_set, report)
    assert plan["status"] == "iteration_required"
    assert plan["next_action"]["target"] == "verifiability"
    assert plan["next_action"]["card"] == "scientific_judgment"


def test_one_criterion_with_judge_disagreement_requires_adjudication(tmp_path: Path) -> None:
    candidate_set = _candidate_set(tmp_path)
    packet = _reviews(candidate_set)
    for judge_index, judge in enumerate(packet["judges"]):
        for candidate in judge["candidates"].values():
            candidate["criteria"]["scientific_reality"]["score"] = (4.0, 0.0, 4.0)[judge_index]
    packet_path = tmp_path / "reviews.json"
    packet_path.write_text(json.dumps(packet), encoding="utf-8")
    report = select_candidates(candidate_set, packet_path)
    assert report["status"] == "adjudication_required"
    assert report["recommended_candidate"] is None
    assert all(
        value["minimum_criterion_agreement"] < report["min_agreement"]
        for value in report["candidates"].values()
    )
