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
    quality_modules_path = root / "registry/enterprise_quality_modules.json"
    quality_modules = json.loads(quality_modules_path.read_text(encoding="utf-8")) if quality_modules_path.exists() else {"modules": []}
    requirements_path = root / "registry/public_benchmark_requirements.json"
    requirements_doc = json.loads(requirements_path.read_text(encoding="utf-8")) if requirements_path.exists() else {"requirement_dimensions": [], "source_requirements": []}
    source_index = check_unique(sources, "benchmark_id", "benchmarks", errors)
    workflow_index = check_unique(workflows, "workflow_id", "workflows", errors)
    pattern_index = check_unique(patterns, "pattern_id", "patterns", errors)
    del workflow_index, pattern_index
    benchmark_ids = set(source_index)
    module_rows = quality_modules.get("modules", [])
    module_ids = {row.get("module_id") for row in module_rows if isinstance(row, dict)}
    if len(module_ids) != len(module_rows) or None in module_ids:
        errors.append("quality modules: duplicate or missing module_id")
    if len(module_rows) < 8:
        errors.append("quality modules: expected at least 8 enterprise quality modules")
    for row in module_rows:
        if not row.get("name") or not row.get("purpose") or not row.get("required_evidence"):
            errors.append(f"quality module {row.get('module_id')}: name, purpose, and required_evidence are required")
    requirement_dimensions = requirements_doc.get("requirement_dimensions", [])
    requirement_ids = {row.get("requirement_id") for row in requirement_dimensions if isinstance(row, dict)}
    if len(requirement_dimensions) < 10 or len(requirement_ids) != len(requirement_dimensions) or None in requirement_ids:
        errors.append("public benchmark requirements: expected at least 10 unique requirement dimensions")
    for row in requirement_dimensions:
        if not row.get("name") or not row.get("question") or not row.get("harbor_mapping"):
            errors.append(f"requirement {row.get('requirement_id')}: name, question, and harbor_mapping are required")
    source_requirement_rows = requirements_doc.get("source_requirements", [])
    source_requirement_ids = {row.get("benchmark_id") for row in source_requirement_rows if isinstance(row, dict)}
    for benchmark_id in source_requirement_ids:
        if benchmark_id not in benchmark_ids:
            errors.append(f"public benchmark requirements: unknown benchmark_id {benchmark_id}")
    seeds = json.loads((root / "seeds/official_sources.json").read_text(encoding="utf-8"))
    seed_ids = {row.get("source_id") for row in seeds}
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
    print(json.dumps({"valid": not errors, "counts": {"benchmarks": len(sources), "workflows": len(workflows), "patterns": len(patterns), "quality_modules": len(module_rows), "requirement_dimensions": len(requirement_dimensions), "source_requirement_rows": len(source_requirement_rows)}, "errors": errors}, ensure_ascii=False, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
