#!/usr/bin/env python3
"""Package high-quality model trials with task inputs, runtime, trajectories and analysis."""
from __future__ import annotations

import argparse
import gzip
import hashlib
import io
import json
import os
import tarfile
import tempfile
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]
PREFIX = "high-quality-gpt56sol-trials-20260928"
TASKS = (
    "eb013-cross-context-evidence-portfolio-005",
    "eb013-evidence-budget-routing-001",
    "eb013-evidence-budget-routing-002",
    "eb013-partial-observation-risk-004",
    "eb013-shared-setup-routing-003",
    "eb014-sequential-evidence-feedback-002",
    "eb015-real-source-replacement-gate-001",
)
RUNTIME_FILES = (
    "benchmark_runner/adapters/codex_gpt55.py",
    "benchmark_runner/adapters/codex_complete_turn.py",
    "benchmark_runner/trajectory.py",
    "benchmark_runner/cli.py",
    "reports/gpt56sol_trial_status_20260928.md",
    "reports/high_quality_trial_bundle_20260928.md",
)
SKIP_PARTS = {"__pycache__", ".pytest_cache", ".git"}


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def include(relative: Path) -> bool:
    return not any(part in SKIP_PARTS for part in relative.parts) and relative.suffix != ".pyc" and relative.name != ".DS_Store"


def add_file(files: dict[str, bytes], name: str, path: Path) -> None:
    if not path.is_file() or path.is_symlink():
        raise ValueError(f"missing or symlinked source: {path}")
    if name in files:
        raise ValueError(f"duplicate package path: {name}")
    files[name] = path.read_bytes()


def trial_records(task: Path) -> tuple[list[str], str, str]:
    path = task / "quality/model_trial_results.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    records = [
        row for row in data.get("records", [])
        if row.get("model") == "gpt-5.6-sol" and row.get("passed") is True
    ]
    if not records:
        raise ValueError(f"no passing gpt-5.6-sol record for {task.name}")
    ids = [row.get("trial_id") for row in records if row.get("trial_id")]
    return ids, records[-1].get("status", ""), data.get("target_model_status", "")


def build_files() -> dict[str, bytes]:
    files: dict[str, bytes] = {}
    task_manifest: dict[str, object] = {}
    for task_id in TASKS:
        task = ROOT / "benchmarks" / task_id
        if not task.is_dir():
            raise ValueError(f"missing task: {task}")
        selected_ids, selected_status, top_status = trial_records(task)
        trial_root = task / "quality/trials"
        analysis = sorted(path.name for path in (task / "quality").glob("trial_analysis*.md"))
        if not trial_root.is_dir() or not any(trial_root.iterdir()):
            raise ValueError(f"missing trajectory/trial directory: {trial_root}")
        if not analysis:
            raise ValueError(f"missing trial analysis: {task / 'quality'}")
        environment_files = [
            path.relative_to(task).as_posix()
            for path in sorted((task / "environment").rglob("*") if (task / "environment").is_dir() else [])
            if path.is_file()
        ]
        trial_files = [
            path.relative_to(task).as_posix()
            for path in sorted(trial_root.rglob("*"))
            if path.is_file() and include(path.relative_to(task))
        ]
        for path in sorted(task.rglob("*")):
            relative = path.relative_to(task)
            if path.is_file() and include(relative):
                add_file(files, f"tasks/{task_id}/{relative.as_posix()}", path)
        task_manifest[task_id] = {
            "model": "gpt-5.6-sol",
            "passing_trial_ids": selected_ids,
            "selected_trial_status": selected_status,
            "quality_target_status": top_status,
            "environment_present": bool(environment_files),
            "environment_files": environment_files,
            "trajectory_files": trial_files,
            "analysis_files": [f"quality/{name}" for name in analysis],
            "release_status": "BLOCKED",
            "note": "High-quality model completion evidence; package is internal calibration evidence, not Harbor release evidence.",
        }

    for relative in RUNTIME_FILES:
        add_file(files, f"runtime/{relative}", ROOT / relative)

    metadata = {
        "schema_version": "high_quality_trial_bundle.v1",
        "bundle_id": PREFIX,
        "snapshot_status": "INTERNAL_CALIBRATION_EVIDENCE",
        "formal_release_status": "BLOCKED",
        "model": "gpt-5.6-sol",
        "selection_rule": "task has a passing gpt-5.6-sol record, stored trajectory/trial artifacts, and written trial analysis; verifier pass is not required for inclusion if the analysis classifies the issue as delivery/contract-only",
        "tasks": task_manifest,
        "included_components": ["task package", "environment when present", "data", "quality/trials trajectory", "trial evidence", "trial analysis", "runtime adapters"],
        "excluded_runtime_noise": ["__pycache__", ".pytest_cache", "*.pyc", ".DS_Store"],
        "files": {name: {"sha256": digest(data), "size": len(data)} for name, data in sorted(files.items())},
    }
    files["manifest.json"] = (json.dumps(metadata, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode()
    return files


def verify(path: Path) -> None:
    with tarfile.open(path, "r:gz") as archive:
        members = archive.getmembers()
        names = [member.name for member in members]
        if len(names) != len(set(names)) or any(not member.isfile() for member in members):
            raise ValueError("archive must contain unique regular files only")
        if any(PurePosixPath(name).is_absolute() or ".." in PurePosixPath(name).parts for name in names):
            raise ValueError("unsafe archive path")
        payload = {member.name.removeprefix(PREFIX + "/"): archive.extractfile(member).read() for member in members}
    manifest = json.loads(payload.pop("manifest.json"))
    if set(payload) != set(manifest["files"]):
        raise ValueError("manifest membership mismatch")
    for name, expected in manifest["files"].items():
        if digest(payload[name]) != expected["sha256"] or len(payload[name]) != expected["size"]:
            raise ValueError(f"manifest digest mismatch: {name}")
    if set(manifest["tasks"]) != set(TASKS):
        raise ValueError("task membership mismatch")
    for task_id, info in manifest["tasks"].items():
        if not info["trajectory_files"] or not info["analysis_files"]:
            raise ValueError(f"incomplete trial evidence for {task_id}")
    print(f"verified {len(payload)} payload files for {manifest['bundle_id']}")


def build(output: Path) -> None:
    if output.exists():
        raise FileExistsError(f"refusing to overwrite existing archive: {output}")
    files = build_files()
    output.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=".high-quality-trials-", dir=output.parent)
    try:
        os.fchmod(fd, 0o644)
        with os.fdopen(fd, "wb") as raw, gzip.GzipFile(fileobj=raw, mode="wb", filename="", mtime=0, compresslevel=9) as compressed, tarfile.open(fileobj=compressed, mode="w") as archive:
            for name, data in sorted(files.items()):
                info = tarfile.TarInfo(f"{PREFIX}/{name}")
                info.size = len(data)
                info.mode = 0o644
                info.mtime = 0
                archive.addfile(info, io.BytesIO(data))
        os.replace(temporary, output)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    verify(output)
    checksum = output.with_name(output.name + ".sha256")
    archive_hash = digest(output.read_bytes())
    checksum.write_text(f"{archive_hash}  {output.name}\n", encoding="ascii")
    print(json.dumps({"archive": str(output), "sha256": archive_hash, "files": len(files)}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--output", type=Path)
    group.add_argument("--verify", type=Path)
    args = parser.parse_args()
    build(args.output) if args.output else verify(args.verify)
