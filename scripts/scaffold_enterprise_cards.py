#!/usr/bin/env python3
"""Generate draft enterprise card bundles from the registry.

The generated cards are intentionally review-blocked scaffolds. They preserve
source attribution and the original benchmark contract, but never infer a
scientific truth route or grant Harbor release readiness.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
from pathlib import Path


CARD_NAMES = ("source", "benchmark", "workflow", "transformation", "data", "evaluation", "risk", "harbor", "review")


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def slug(value: str) -> str:
    value = re.sub(r"[^a-zA-Z0-9]+", "-", value).strip("-").lower()
    return value[:48] or "benchmark"


def build_cards(benchmark: dict, workflow: dict | None, retrieved_at: str) -> dict[str, dict]:
    benchmark_id = benchmark["benchmark_id"]
    task_id = f"{slug(benchmark_id)}-candidate-001"
    source_id = benchmark["source_id"]
    workflow = workflow or {
        "workflow_id": f"WF-{benchmark_id}-UNRESOLVED",
        "benchmark_ids": [benchmark_id],
        "enterprise_stage": "unresolved",
        "role": "unresolved",
        "object": benchmark.get("object", "unresolved"),
        "business_decision": benchmark.get("decision", "unresolved"),
        "handoffs": ["input->analysis->decision"],
        "independent_unit": "unresolved",
        "claim_boundary": "Benchmark score does not establish enterprise or clinical validity.",
        "status": "candidate",
    }
    return {
        "source": {
            "source_id": source_id,
            "organization": benchmark.get("organization", ""),
            "url": benchmark.get("source_url", ""),
            "kind": benchmark.get("enterprise_role", "unknown"),
            "authenticity": benchmark.get("authenticity_class", "S"),
            "evidence_status": benchmark.get("evidence_status", "observed"),
            "retrieved_at": retrieved_at,
            "commit_or_version": None,
            "license_status": benchmark.get("license_status", "verify_pending"),
            "evidence_locators": ["registry/enterprise_benchmarks.jsonl"],
            "unresolved_questions": ["freeze an official commit or version", "verify data and model redistribution terms", "confirm enterprise participation scope"],
        },
        "benchmark": dict(benchmark),
        "workflow": dict(workflow),
        "transformation": {
            "schema_version": "enterprise_transformation_card.v1",
            "transformation_id": f"TX-{benchmark_id}-DRAFT",
            "source_benchmark_id": benchmark_id,
            "derived_task_id": task_id,
            "status": "DRAFT",
            "changed_dimensions": ["business_decision", "failure_mode", "evaluation_contract"],
            "semantic_changed_dimensions": [],
            "surface_only_changes": [],
            "scientific_decision_changed": False,
            "truth_or_failure_changed": False,
            "transformation_primitives": [],
            "evidence": {},
            "accepted_alternatives": [],
            "scientific_rationale": None,
            "release_status": "REVIEW_REQUIRED",
        },
        "data": {
            "data_card_id": f"DATA-{benchmark_id}-DRAFT",
            "source_benchmark_id": benchmark_id,
            "data_kind": "source_data_status_pending",
            "lineage": [benchmark.get("source_url", "")],
            "visibility": {"agent": benchmark.get("inputs", []), "verifier": ["hidden truth to be authored"], "author": ["source files and license evidence"]},
            "truth_scope": "Not yet established; do not infer labels, units, or external validity.",
            "status": "DRAFT",
        },
        "evaluation": {
            "evaluation_card_id": f"EVAL-{benchmark_id}-DRAFT",
            "task_id": task_id,
            "independent_unit": workflow.get("independent_unit", "unresolved"),
            "metrics": benchmark.get("evaluation", {}).get("metrics", []),
            "truth_route": ["independent oracle or invariant route required", "reference replay required"],
            "accepted_alternatives": ["must be authored from method-equivalence analysis"],
            "negative_cases": ["empty submission", "wrong schema", "unsupported claim"],
            "status": "DRAFT",
        },
        "risk": {
            "risk_card_id": f"RISK-{benchmark_id}-DRAFT",
            "task_id": task_id,
            "attribution": {"organization": benchmark.get("organization", ""), "enterprise_role": benchmark.get("enterprise_role", ""), "status": "review_required"},
            "license": {"status": benchmark.get("license_status", "verify_pending"), "solver_redistribution": "blocked_until_review"},
            "privacy": {"status": "review_required"},
            "biosafety_or_medical": {"status": "review_required"},
            "claim_boundary": [workflow.get("claim_boundary", "")],
            "release_status": "REVIEW_REQUIRED",
        },
        "harbor": {
            "harbor_card_id": f"HARBOR-{benchmark_id}-DRAFT",
            "task_id": task_id,
            "task_contract": {"instruction": None, "task_yaml": None},
            "agent_visible": benchmark.get("inputs", []),
            "verifier_only": ["truth", "oracle", "verifier"],
            "environment": {"network": "to_be_frozen", "resources": "to_be_measured"},
            "oracle": {"status": "not_authored"},
            "release_gates": {"source": "blocked", "license": "blocked", "truth": "blocked", "verifier": "blocked", "trial": "not_run"},
            "status": "CONTRACT_ONLY",
        },
        "review": {
            "review_id": f"REVIEW-{benchmark_id}-DRAFT",
            "task_id": task_id,
            "reviewers": ["domain_scientist", "methods_reproducibility_auditor", "license_attribution_reviewer"],
            "hard_gates": ["enterprise attribution verified", "license verified", "truth route independently checked", "agent/verifier isolation tested"],
            "open_questions": ["what is the real business handoff?", "which evidence is visible to the agent?", "what is the acceptable answer class?"],
            "decision": "REVISE",
            "status": "PENDING",
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("knowledge_base"))
    parser.add_argument("--out", type=Path, default=Path("knowledge_base/draft_bundles"))
    parser.add_argument("--clean", action="store_true", help="remove only previously generated bundle directories")
    args = parser.parse_args()
    benchmarks = read_jsonl(args.root / "registry/enterprise_benchmarks.jsonl")
    workflows = read_jsonl(args.root / "registry/workflows.jsonl")
    workflow_by_benchmark = {benchmark_id: workflow for workflow in workflows for benchmark_id in workflow.get("benchmark_ids", [])}
    if args.clean and args.out.exists():
        for child in args.out.iterdir():
            if child.is_dir() and child.name.startswith("EB"):
                for path in sorted(child.rglob("*"), reverse=True):
                    if path.is_file() or path.is_symlink():
                        path.unlink()
                    elif path.is_dir():
                        path.rmdir()
                child.rmdir()
    args.out.mkdir(parents=True, exist_ok=True)
    retrieved_at = dt.date.today().isoformat()
    for benchmark in benchmarks:
        benchmark_id = benchmark["benchmark_id"]
        bundle_dir = args.out / f"{benchmark_id}-{slug(benchmark['name'])}"
        bundle_dir.mkdir(parents=True, exist_ok=True)
        cards = build_cards(benchmark, workflow_by_benchmark.get(benchmark_id), retrieved_at)
        manifest = {
            "schema_version": "enterprise_card_bundle.v1",
            "bundle_id": f"BUNDLE-{benchmark_id}-DRAFT",
            "source_benchmark_id": benchmark_id,
            "derived_task_id": cards["transformation"]["derived_task_id"],
            "cards": {name: f"{name}_card.json" for name in CARD_NAMES},
            "status": "DRAFT",
            "release_blockers": ["source_verification", "license_review", "independent_truth_route", "container_replay", "model_trial"],
        }
        (bundle_dir / "card_bundle.manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        for name, card in cards.items():
            (bundle_dir / f"{name}_card.json").write_text(json.dumps(card, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"generated {bundle_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
