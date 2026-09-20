#!/usr/bin/env python3
"""Turn differentiated candidate cards into contract-only question briefs.

These briefs are the next scale-out stage. They are not runnable Harbor tasks:
data, truth routes, controls, and model trials remain explicit blockers.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


def slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def compile_briefs(matrix: Path, out: Path) -> dict:
    manifest = json.loads((matrix / "manifest.json").read_text(encoding="utf-8"))
    out.mkdir(parents=True, exist_ok=True)
    briefs: list[dict] = []
    for entry in manifest["cards"]:
        card = json.loads((matrix.parent.parent / entry["path"]).read_text(encoding="utf-8"))
        for candidate in card["candidates"]:
            brief = {
                "schema_version": "enterprise_question_brief.v1",
                "brief_id": f"BRIEF-{candidate['candidate_id']}",
                "source_benchmark_id": card["source_benchmark_id"],
                "source_name": card["source_name"],
                "workflow_id": card["workflow_id"],
                "enterprise_role": card["enterprise_role"],
                "status": "CONTRACT_ONLY",
                "scientific_decision": candidate["decision"],
                "independent_unit": candidate["independent_unit"],
                "handoff": candidate["handoff"],
                "error_consequence": candidate["error_consequence"],
                "agent_visible_inputs": ["frozen task-specific input bundle", "rule/specification file", "provenance metadata"],
                "required_artifacts": candidate["required_artifacts"],
                "failure_injections": candidate["failure_injections"],
                "gpt_difficulty": {
                    "mechanism": candidate["gpt_difficulty_mechanism"],
                    "semantic_axes": candidate["semantic_axes"],
                    "shortcut_probes": candidate["shortcut_probes"],
                },
                "claim_boundary": candidate["claim_boundary"],
                "release_blockers": [
                    "freeze source version and license",
                    "materialize agent-visible data without hidden truth leakage",
                    "author independent oracle or expert-equivalence rubric",
                    "run positive, negative, invariance, and insufficient-evidence controls",
                    "run reference, simple legal, always-abstain, template, and target-model trials",
                ],
            }
            path = out / f"{slug(candidate['candidate_id'])}.json"
            path.write_text(json.dumps(brief, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            briefs.append({"brief_id": brief["brief_id"], "path": str(path.relative_to(out.parent.parent)), "source_benchmark_id": card["source_benchmark_id"]})
    output = {
        "schema_version": "enterprise_question_brief_matrix.v1",
        "source_matrix": str(matrix.relative_to(matrix.parent.parent)),
        "status": "CONTRACT_ONLY",
        "brief_count": len(briefs),
        "selection_policy": "select at most one or two candidates per source after enterprise-value and control review; do not compile every brief automatically",
        "briefs": briefs,
    }
    (out / "manifest.json").write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return output


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--matrix", type=Path, default=Path("candidate_pools/enterprise-v1"))
    parser.add_argument("--out", type=Path, default=Path("candidate_pools/enterprise-v1/question_briefs"))
    args = parser.parse_args()
    matrix = args.matrix.resolve()
    output = compile_briefs(matrix, args.out.resolve())
    print(f"compiled {output['brief_count']} contract-only question briefs")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
