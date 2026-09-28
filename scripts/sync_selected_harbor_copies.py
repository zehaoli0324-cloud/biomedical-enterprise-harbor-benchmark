#!/usr/bin/env python3
"""Synchronize generated Harbor copies for the selected executable tasks."""
from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TASKS = (
    "eb014-sequential-evidence-feedback-002",
    "eb015-real-source-replacement-gate-001",
)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sync_task(task_id: str) -> dict[str, object]:
    task = ROOT / "benchmarks" / task_id
    pairs: list[tuple[Path, Path]] = []
    for source in sorted((task / "data").iterdir()):
        if source.is_file():
            pairs.append((source, task / "environment/data" / source.name))
            pairs.append((source, task / "tests/verification_data" / source.name))
    pairs.extend(
        [
            (task / "instruction.md", task / "environment/instruction.md"),
            (task / "verifier.py", task / "tests/verifier.py"),
        ]
    )
    for source in sorted((task / "verifier_only").iterdir()):
        if source.is_file():
            pairs.append((source, task / "tests/verifier_only" / source.name))

    for source, destination in pairs:
        if not source.is_file() or source.is_symlink():
            raise ValueError(f"invalid synchronization source: {source}")
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
        if sha(source) != sha(destination):
            raise ValueError(f"copy drift: {source} != {destination}")
    return {"task_id": task_id, "copies": len(pairs), "status": "PASS"}


if __name__ == "__main__":
    print(json.dumps({"tasks": [sync_task(task_id) for task_id in TASKS]}, indent=2))
