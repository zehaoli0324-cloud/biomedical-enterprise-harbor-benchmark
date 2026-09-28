#!/usr/bin/env python3
"""Run the fail-closed task pipeline gate over formal or working-tree tasks."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_task_pipeline import evaluate


ROOT = Path(__file__).resolve().parents[1]


def scope_registry() -> dict[str, set[str]]:
    data = json.loads((ROOT / "config/task_scope.v1.json").read_text(encoding="utf-8"))
    return {
        "formal": set(data.get("formal_release_scope", [])),
        "candidate": set(data.get("candidate_only_scope", [])),
    }


def discover_tasks(formal_only: bool) -> list[Path]:
    formal = scope_registry()["formal"]
    tasks = []
    for package in sorted(path for path in (ROOT / "benchmarks").iterdir() if path.is_dir()):
        if not ((package / "task.yaml").is_file() or (package / "task.toml").is_file()):
            continue
        if formal_only and package.name not in formal:
            continue
        tasks.append(package)
    return tasks


def compact(report: dict[str, Any], formal: bool) -> dict[str, Any]:
    manifest = report["build_manifest"]
    return {
        "task_id": report["task_id"],
        "scope": "formal" if formal else "candidate_or_formal",
        "pipeline_status": report["pipeline_status"],
        "evidence_status": report["evidence_status"],
        "review_status": report["review_status"],
        "release_status": report["release_status"],
        "release_permitted": report["release_permitted"],
        "blockers": report["blockers"],
        "release_blockers": report["release_blockers"],
        "task_version": report["build_manifest"]["task_version"],
        "data_fingerprint": manifest["data_fingerprint"],
        "contract_fingerprint": manifest["contract_fingerprint"],
        "file_count": len(manifest["files"]),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    scope = parser.add_mutually_exclusive_group()
    scope.add_argument("--all", action="store_true", help="scan all task packages in benchmarks/")
    scope.add_argument("--formal-only", action="store_true", help="scan only packages in config/task_scope.v1.json formal_release_scope")
    parser.add_argument("--package", type=Path, action="append", help="scan one or more explicit packages")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    formal = scope_registry()["formal"]
    if args.package:
        packages = [path.resolve() for path in args.package]
    else:
        packages = discover_tasks(formal_only=args.formal_only and not args.all)
    rows = [compact(evaluate(package), package.name in formal) for package in packages]
    summary: dict[str, int] = {}
    for row in rows:
        for key in ("pipeline_status", "evidence_status", "review_status", "release_status"):
            value = row[key]
            summary[f"{key}:{value}"] = summary.get(f"{key}:{value}", 0) + 1
    result = {
        "schema_version": "task_pipeline_batch_report.v1",
        "scope": "explicit" if args.package else ("formal" if args.formal_only and not args.all else "working_tree"),
        "package_count": len(rows),
        "summary": summary,
        "tasks": rows,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"package_count": len(rows), "summary": summary}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
