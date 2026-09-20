#!/usr/bin/env python3
"""Validate scaled enterprise candidate cards and semantic diversity."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def validate(path: Path) -> tuple[bool, list[str]]:
    errors: list[str] = []
    manifest = json.loads((path / "manifest.json").read_text(encoding="utf-8"))
    if manifest.get("schema_version") != "enterprise_candidate_matrix.v1":
        errors.append("unsupported matrix schema")
    entries = manifest.get("cards", [])
    if manifest.get("benchmark_count") != len(entries):
        errors.append("benchmark_count mismatch")
    total = 0
    for entry in entries:
        card_path = path.parent.parent / entry["path"]
        if not card_path.exists():
            errors.append(f"missing card: {entry['path']}")
            continue
        card = json.loads(card_path.read_text(encoding="utf-8"))
        candidates = card.get("candidates", [])
        if not 3 <= len(candidates) <= 5:
            errors.append(f"{entry['benchmark_id']} must contain 3-5 candidates")
        total += len(candidates)
        fingerprints = set()
        axis_sets = []
        for candidate in candidates:
            required = ("candidate_id", "decision", "independent_unit", "handoff", "error_consequence", "semantic_axes", "failure_injections", "required_artifacts", "gpt_difficulty_mechanism", "claim_boundary")
            missing = [field for field in required if not candidate.get(field)]
            if missing:
                errors.append(f"{candidate.get('candidate_id', '<unknown>')} missing {missing}")
            fingerprint = tuple(candidate.get(field, "").lower() for field in ("decision", "independent_unit", "handoff"))
            if fingerprint in fingerprints:
                errors.append(f"surface duplicate in {entry['benchmark_id']}: {candidate.get('candidate_id')}")
            fingerprints.add(fingerprint)
            axis_sets.append(set(candidate.get("semantic_axes", [])))
        for index, left in enumerate(axis_sets):
            for right in axis_sets[index + 1 :]:
                if len(left.symmetric_difference(right)) < 2:
                    errors.append(f"{entry['benchmark_id']} pair differs on fewer than two semantic axes")
    if total != manifest.get("candidate_count"):
        errors.append("candidate_count mismatch")
    return not errors, errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("matrix", type=Path)
    args = parser.parse_args()
    ok, errors = validate(args.matrix)
    print(json.dumps({"valid": ok, "errors": errors}, ensure_ascii=False, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
