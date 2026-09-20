#!/usr/bin/env python3
"""Validate one enterprise source-to-Harbor card bundle without third-party dependencies."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


REQUIRED_CARDS = ("source", "benchmark", "workflow", "transformation", "data", "evaluation", "risk", "harbor", "review")


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
    loaded: dict[str, dict] = {}
    for card_name in REQUIRED_CARDS:
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
    print(json.dumps({"valid": not errors, "bundle": str(root), "source_benchmark_id": benchmark_id, "derived_task_id": task_id, "cards": sorted(loaded), "errors": errors}, ensure_ascii=False, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
