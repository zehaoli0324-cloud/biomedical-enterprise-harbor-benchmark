#!/usr/bin/env python3
"""Validate one enterprise source-to-Harbor card bundle without third-party dependencies."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


BASE_CARDS = ("source", "benchmark", "workflow", "transformation", "data", "evaluation", "risk", "harbor", "review")
QUALITY_CARDS = ("candidate_set", "enterprise_value", "requirements", "control_plan", "difficulty", "training_value", "model_trial")
REQUIREMENT_IDS = {f"REQ{index:02d}" for index in range(1, 15)}
SELECTION_REQUIREMENTS = {"REQ02", "REQ03", "REQ04", "REQ06", "REQ08", "REQ09"}
VERIFIED_STATUSES = {"VERIFIED", "VERIFIED_FROM_OFFICIAL_SOURCE"}


def load(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("bundle", type=Path, help="directory containing card_bundle.manifest.json")
    args = parser.parse_args()
    root = args.bundle
    errors: list[str] = []
    manifest_path = root / "card_bundle.manifest.json"
    if not manifest_path.exists():
        print(json.dumps({"valid": False, "errors": ["missing card_bundle.manifest.json"]}, ensure_ascii=False, indent=2))
        return 1
    manifest = load(manifest_path)
    cards = manifest.get("cards", {})
    schema_version = manifest.get("schema_version", "enterprise_card_bundle.v1")
    required_cards = BASE_CARDS + (QUALITY_CARDS if schema_version == "enterprise_card_bundle.v2" else ())
    loaded: dict[str, dict] = {}
    for card_name in required_cards:
        relative = cards.get(card_name)
        if not relative:
            errors.append(f"missing manifest entry for {card_name}")
            continue
        path = root / relative
        if not path.exists():
            errors.append(f"missing card file: {relative}")
            continue
        try:
            loaded[card_name] = load(path)
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            errors.append(str(exc))
    benchmark_id = manifest.get("source_benchmark_id")
    task_id = manifest.get("derived_task_id")
    if loaded.get("benchmark", {}).get("benchmark_id") != benchmark_id:
        errors.append("benchmark card does not match source_benchmark_id")
    if loaded.get("source", {}).get("source_id") != loaded.get("benchmark", {}).get("source_id"):
        errors.append("source and benchmark cards have different source_id")
    if benchmark_id not in loaded.get("workflow", {}).get("benchmark_ids", []):
        errors.append("workflow card does not link source benchmark")
    if loaded.get("transformation", {}).get("source_benchmark_id") != benchmark_id:
        errors.append("transformation card does not link source benchmark")
    for card_name in ("evaluation", "risk", "harbor", "review"):
        if loaded.get(card_name, {}).get("task_id") != task_id:
            errors.append(f"{card_name} card does not match derived_task_id")
    if loaded.get("harbor", {}).get("oracle", {}).get("path") in loaded.get("harbor", {}).get("agent_visible", []):
        errors.append("verifier oracle is listed as agent-visible")
    if loaded.get("transformation", {}).get("release_status") == "READY_FOR_HARBOR" and loaded.get("review", {}).get("decision") != "READY":
        errors.append("ready transformation requires review decision READY")
    if schema_version == "enterprise_card_bundle.v2":
        if loaded.get("candidate_set", {}).get("source_benchmark_id") != benchmark_id:
            errors.append("candidate_set card does not match source_benchmark_id")
        for card_name in QUALITY_CARDS[1:]:
            if loaded.get(card_name, {}).get("task_id") != task_id:
                if card_name != "requirements":
                    errors.append(f"{card_name} card does not match derived_task_id")
        if loaded.get("requirements", {}).get("source_benchmark_id") != benchmark_id:
            errors.append("requirements card does not match source_benchmark_id")
        requirements = loaded.get("requirements", {})
        dimensions = requirements.get("dimensions", [])
        dimension_ids = {row.get("requirement_id") for row in dimensions if isinstance(row, dict)}
        if dimension_ids != REQUIREMENT_IDS:
            missing = sorted(REQUIREMENT_IDS - dimension_ids)
            extra = sorted(dimension_ids - REQUIREMENT_IDS)
            errors.append(f"requirements card must contain exactly REQ01-REQ14 (missing={missing}, extra={extra})")
        for row in dimensions:
            if not isinstance(row, dict):
                errors.append("requirements card dimensions must be objects")
                continue
            if not row.get("name") or not row.get("status") or not row.get("harbor_action"):
                errors.append(f"requirement {row.get('requirement_id')}: name, status, and harbor_action are required")
        status_by_id = {
            row.get("requirement_id"): row.get("status")
            for row in dimensions
            if isinstance(row, dict)
        }
        unresolved_selection_requirements = sorted(
            requirement_id
            for requirement_id in SELECTION_REQUIREMENTS
            if status_by_id.get(requirement_id) not in VERIFIED_STATUSES
        )
        selected_candidates = [
            candidate
            for candidate in loaded.get("candidate_set", {}).get("candidates", [])
            if str(candidate.get("selection_status", "")).upper() == "SELECTED"
        ]
        selected_bundle = (
            bool(selected_candidates)
            or str(loaded.get("benchmark", {}).get("redesign_status", "")).upper() == "SELECTED"
            or str(loaded.get("transformation", {}).get("status", "")).upper() == "SELECTED"
        )
        if selected_bundle and unresolved_selection_requirements:
            errors.append(
                "selected candidates require verified REQ02/03/04/06/08/09; "
                f"unresolved={unresolved_selection_requirements}"
            )
        if loaded.get("transformation", {}).get("release_status") == "READY_FOR_HARBOR" and unresolved_selection_requirements:
            errors.append(
                "READY_FOR_HARBOR requires verified REQ02/03/04/06/08/09; "
                f"unresolved={unresolved_selection_requirements}"
            )
        candidate_count = len(loaded.get("candidate_set", {}).get("candidates", []))
        if not 3 <= candidate_count <= 5:
            errors.append("candidate_set must contain 3-5 candidates")
        if loaded.get("candidate_set", {}).get("selection_gate", {}).get("require_two_semantic_differences") is not True:
            errors.append("candidate_set must require two semantic differences")
        control_kinds = {control.get("kind") for control in loaded.get("control_plan", {}).get("controls", [])}
        for required_kind in ("positive", "negative", "invariance", "insufficient_evidence"):
            if required_kind not in control_kinds:
                errors.append(f"control_plan missing {required_kind} control")
        strategies = set(loaded.get("model_trial", {}).get("strategies", []))
        for required_strategy in ("reference_solution", "simple_legal_baseline", "always_abstain", "template_or_keyword", "target_model"):
            if required_strategy not in strategies:
                errors.append(f"model_trial missing {required_strategy} strategy")
        if loaded.get("training_value", {}).get("training_use") == "PRODUCTION_TRAINING" and loaded.get("model_trial", {}).get("status") != "COMPLETE":
            errors.append("production training use requires completed model trial")
    print(json.dumps({"valid": not errors, "bundle": str(root), "source_benchmark_id": benchmark_id, "derived_task_id": task_id, "cards": sorted(loaded), "errors": errors}, ensure_ascii=False, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
