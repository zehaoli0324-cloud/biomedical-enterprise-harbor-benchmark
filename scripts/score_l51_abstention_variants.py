#!/usr/bin/env python3
"""Score abstention variants on the independent evidence units for EB010."""

from __future__ import annotations

import csv
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "eb010-closed-loop-ambiguity-004"
UNIT_WEIGHT = 1 / 21
MAX_ABSTENTION_FRACTION = 0.30
MAX_ABSTENTION_SCORE_WEIGHT = 0.25
BLANKET_ABSTAIN_MAX_REFERENCE_FRACTION = 0.70


def load_verifier():
    task = ROOT / "benchmarks" / TASK_ID
    spec = importlib.util.spec_from_file_location("ambiguity_scoring_verifier", task / "verifier.py")
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return task, module


def load_units(task: Path) -> dict[str, str]:
    mapping = task / "quality/claim_evidence_map.tsv"
    units: dict[str, str] = {}
    with mapping.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            evidence_type = row["evidence_type"]
            if evidence_type == "CONTROL_PARAMETER":
                continue
            action = "abstain" if evidence_type == "INSUFFICIENT_BY_DESIGN" else "definite"
            for record_id in row["example_ids"].split(","):
                record_id = record_id.strip()
                if record_id:
                    units[record_id] = action
    if len(units) != 21:
        raise ValueError(f"expected 21 independent units, found {len(units)}")
    return units


def variant_actions(units: dict[str, str], variant_id: str) -> dict[str, str]:
    actions = {record_id: "abstain" if variant_id == "all_abstain" else "definite" for record_id in units}
    if variant_id == "positive_plus_insufficient_abstain":
        actions = dict(units)
    elif variant_id == "positive_as_wrong_abstain":
        actions = dict(units)
        positive = next(record_id for record_id, action in units.items() if action == "definite")
        actions[positive] = "abstain"
    elif variant_id not in {"all_abstain", "all_definite"}:
        raise ValueError(f"unknown variant: {variant_id}")
    return actions


def score(units: dict[str, str], variant_id: str) -> dict:
    expected = units
    actual = variant_actions(units, variant_id)
    correct = sum(actual[record_id] == expected[record_id] for record_id in units)
    abstained = sum(action == "abstain" for action in actual.values())
    score_value = round(correct / len(units), 6)
    abstention_fraction = round(abstained / len(units), 6)
    abstention_score_weight = round(abstained * UNIT_WEIGHT, 6)
    return {
        "variant_id": variant_id,
        "status": "PASS",
        "score": score_value,
        "score_weight": round(UNIT_WEIGHT, 6),
        "abstention_score_weight": abstention_score_weight,
        "abstention_fraction": abstention_fraction,
        "correct_units": correct,
        "total_units": len(units),
        "actions": actual,
    }


def main() -> int:
    task, verifier = load_verifier()
    units = load_units(task)
    expected = verifier.expected(task / "data")
    missing = sorted(set(units) - set(expected["records"]))
    if missing:
        raise ValueError(f"independent units missing from expected records: {missing}")

    variants = [
        score(units, "all_abstain"),
        score(units, "all_definite"),
        score(units, "positive_plus_insufficient_abstain"),
        score(units, "positive_as_wrong_abstain"),
    ]
    reference = next(row for row in variants if row["variant_id"] == "positive_plus_insufficient_abstain")
    blanket = next(row for row in variants if row["variant_id"] == "all_abstain")
    gate_checks = {
        "abstention_fraction_limit": all(row["abstention_fraction"] <= MAX_ABSTENTION_FRACTION for row in variants[1:]),
        "abstention_score_weight_limit": all(row["abstention_score_weight"] <= MAX_ABSTENTION_SCORE_WEIGHT for row in variants[1:]),
        "blanket_abstain_score_limit": blanket["score"] > 0 and blanket["score"] <= reference["score"] * BLANKET_ABSTAIN_MAX_REFERENCE_FRACTION,
        "reference_variant_complete": reference["score"] == 1.0 and reference["abstention_fraction"] <= MAX_ABSTENTION_FRACTION,
        "wrong_positive_loses_credit": next(row for row in variants if row["variant_id"] == "positive_as_wrong_abstain")["score"] < reference["score"],
    }
    result = {
        "schema_version": "abstention_variant_results.v1",
        "task_id": TASK_ID,
        "fixture_version": "data-expanded-20260924-v2",
        "unit_definition": {
            "source": "quality/claim_evidence_map.tsv",
            "independent_units": len(units),
            "control_units_excluded": 5,
            "weight_method": "equal_weight_per_independent_unit",
            "unit_weight": round(UNIT_WEIGHT, 6),
            "expected_actions": units,
        },
        "limits": {
            "max_independent_sample_fraction": MAX_ABSTENTION_FRACTION,
            "max_score_weight": MAX_ABSTENTION_SCORE_WEIGHT,
            "blanket_abstain_max_fraction_of_reference_score": BLANKET_ABSTAIN_MAX_REFERENCE_FRACTION,
        },
        "variants": variants,
        "gate_checks": gate_checks,
        "gate_status": "PASS" if all(gate_checks.values()) else "BLOCKED",
    }
    (task / "quality/abstention_variant_results.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")

    plan_path = task / "quality/abstention_variant_plan.json"
    plan = json.loads(plan_path.read_text())
    plan["evidence_surface"]["score_weights_declared"] = True
    plan["evidence_surface"]["unit_weight"] = round(UNIT_WEIGHT, 6)
    plan["evidence_surface"]["weight_method"] = "equal_weight_per_independent_unit"
    plan["unit_definition"] = result["unit_definition"]
    plan["limits"] = result["limits"]
    plan["variants"] = [
        {
            "variant_id": row["variant_id"],
            "description": next(item["description"] for item in plan["variants"] if item["variant_id"] == row["variant_id"]),
            "status": row["status"],
            "score": row["score"],
            "score_weight": row["score_weight"],
            "abstention_score_weight": row["abstention_score_weight"],
            "abstention_fraction": row["abstention_fraction"],
            "correct_units": row["correct_units"],
            "total_units": row["total_units"],
        }
        for row in variants
    ]
    plan["gate_status"] = result["gate_status"]
    plan["blocking_reason"] = None if result["gate_status"] == "PASS" else "one or more abstention gate checks failed"
    plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2) + "\n")

    card_path = task / "quality/evidence_surface_card.json"
    card = json.loads(card_path.read_text())
    card["variant_status"] = result["gate_status"]
    card["abstention_variant_results"] = "quality/abstention_variant_results.json"
    card_path.write_text(json.dumps(card, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["gate_status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
