#!/usr/bin/env python3
"""Compile a contract-only batch and record immutable difficulty/spec digests."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from benchmark_builder.compiler import compile_spec, spec_digest
from benchmark_builder.config import load_spec
from benchmark_builder.scoring import score_spec


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("."))
    args = parser.parse_args()
    root = args.root.resolve()
    config_dir = root / "candidate_pools/enterprise-v1/contracts"
    output_dir = config_dir / "compiled"
    output_dir.mkdir(parents=True, exist_ok=True)
    records: list[dict] = []
    for config_path in sorted(config_dir.glob("eb*.toml")):
        spec = load_spec(config_path)
        report = score_spec(spec)
        task_output = output_dir / config_path.stem
        manifest_path = compile_spec(spec, report, task_output)
        materialized = all(
            path.exists()
            for path in (
                root / "benchmarks" / spec.task_id / "data",
                root / "benchmarks" / spec.task_id / "verifier.py",
                root / "benchmarks" / spec.task_id / "verifier_only" / "reference.json",
            )
        )
        records.append({
            "task_id": spec.task_id,
            "config": str(config_path.relative_to(root)),
            "compiled_manifest": str(manifest_path.relative_to(root)),
            "status": "ready_for_calibration" if materialized else "compiled_contract",
            "band": report.band,
            "adjusted_score": report.adjusted_score,
            "spec_digest": spec_digest(spec),
            "data_status": "synthetic_fixture" if materialized else "not_materialized",
            "verifier_status": "authored" if materialized else "not_authored",
            "model_trial_status": "NOT_RUN",
        })
    batch_status = "MIXED_CALIBRATION_AND_CONTRACT" if any(item["status"] == "ready_for_calibration" for item in records) else "COMPILED_CONTRACT"
    result = {
        "schema_version": "enterprise_contract_compile_batch.v1",
        "batch_id": "TRANCHE-001",
        "status": batch_status,
        "task_count": len(records),
        "release_policy": "compiled difficulty is not evidence of runnable data, truth, verifier, or model readiness",
        "tasks": records,
    }
    path = config_dir / "batch_compile_report.json"
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"compiled {len(records)} contract-only tasks; report={path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
