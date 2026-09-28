#!/usr/bin/env python3
"""Mark historical model trials as superseded after fixture expansion."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TASKS = [
    "eb010-closed-loop-ambiguity-004",
    "eb010-distributional-policy-stress-006",
    "eb010-stop-uncertainty-002",
    "eb011-reproduction-manifest-001",
    "eb013-evidence-budget-routing-001",
    "eb013-evidence-budget-routing-002",
]


def update(path: Path, task_id: str) -> None:
    if not path.is_file():
        return
    payload = json.loads(path.read_text(encoding="utf-8"))
    previous = payload.get("status")
    payload["data_expansion"] = {
        "status": "SUPERSEDES_PREVIOUS_TRIAL",
        "expanded_on": "2026-09-24",
        "fixture_version": "data-expanded-20260924",
        "previous_status": previous,
        "recalibration_required": True,
    }
    if path.name == "model_trial_results.json" and previous not in {"BASELINES_COMPLETE", "NOT_RUN"}:
        payload["status"] = "DATA_EXPANDED_RECALIBRATION_REQUIRED"
        payload["target_model_status"] = "RECALIBRATION_REQUIRED"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    for task_id in TASKS:
        quality = ROOT / "benchmarks" / task_id / "quality"
        update(quality / "model_trial_results.json", task_id)
        update(quality / "model_trial_card.json", task_id)
        update(quality / "sop_card.json", task_id)
    print(json.dumps({"tasks": TASKS, "status": "DATA_EXPANDED_RECALIBRATION_REQUIRED"}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
