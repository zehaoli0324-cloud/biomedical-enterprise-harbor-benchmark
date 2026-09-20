#!/usr/bin/env python3
"""Validate cross-links in the enterprise benchmark knowledge base."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def read_jsonl(path: Path) -> list[dict]:
    rows = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"{path}:{line_no}: invalid JSON: {exc}") from exc
        if not isinstance(value, dict):
            raise ValueError(f"{path}:{line_no}: record must be an object")
        rows.append(value)
    return rows


def check_unique(rows: list[dict], key: str, label: str, errors: list[str]) -> dict[str, dict]:
    index = {}
    for row in rows:
        value = row.get(key)
        if not value:
            errors.append(f"{label}: missing {key}")
        elif value in index:
            errors.append(f"{label}: duplicate {key}={value}")
        else:
            index[value] = row
    return index


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("knowledge_base"))
    args = parser.parse_args()
    root = args.root
    errors: list[str] = []
    sources = read_jsonl(root / "registry/enterprise_benchmarks.jsonl") if (root / "registry/enterprise_benchmarks.jsonl").exists() else []
    workflows = read_jsonl(root / "registry/workflows.jsonl") if (root / "registry/workflows.jsonl").exists() else []
    patterns = read_jsonl(root / "registry/transformation_patterns.jsonl") if (root / "registry/transformation_patterns.jsonl").exists() else []
    source_index = check_unique(sources, "benchmark_id", "benchmarks", errors)
    workflow_index = check_unique(workflows, "workflow_id", "workflows", errors)
    pattern_index = check_unique(patterns, "pattern_id", "patterns", errors)
    del workflow_index, pattern_index
    seeds = json.loads((root / "seeds/official_sources.json").read_text(encoding="utf-8"))
    seed_ids = {row.get("source_id") for row in seeds}
    benchmark_ids = set(source_index)
    for row in sources:
        if row.get("source_id") not in seed_ids:
            errors.append(f"{row.get('benchmark_id')}: source_id is absent from official seed registry")
        if row.get("authenticity_class") not in {"A", "B", "C", "W", "S"}:
            errors.append(f"{row.get('benchmark_id')}: invalid authenticity_class")
        if not row.get("source_url"):
            errors.append(f"{row.get('benchmark_id')}: missing source_url")
    for row in workflows:
        for benchmark_id in row.get("benchmark_ids", []):
            if benchmark_id not in benchmark_ids:
                errors.append(f"{row.get('workflow_id')}: unknown benchmark_id {benchmark_id}")
        if not row.get("handoffs"):
            errors.append(f"{row.get('workflow_id')}: workflow requires at least one handoff")
        if not row.get("claim_boundary"):
            errors.append(f"{row.get('workflow_id')}: claim_boundary is required")
    print(json.dumps({"valid": not errors, "counts": {"benchmarks": len(sources), "workflows": len(workflows), "patterns": len(patterns)}, "errors": errors}, ensure_ascii=False, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
