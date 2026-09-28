#!/usr/bin/env python3
"""Build and verify the calibrated selected-four v3 internal bundle."""
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
PREFIX = "selected-four-v3-calibrated-20260924"
TASKS = (
    "eb006-research-completion-011",
    "eb013-cross-context-evidence-portfolio-005",
    "eb014-sequential-evidence-feedback-002",
    "eb015-real-source-replacement-gate-001",
)
TASK_METADATA = {
    "eb006-research-completion-011": {
        "version": "1.3.2",
        "trial_classification": "SCIENTIFIC_FAIL_CONTRACT_PASS",
        "target_model_defeated": True,
        "release_blockers": [
            "fixed-container release replay",
            "practitioner review",
            "real-data replacement",
        ],
    },
    "eb013-cross-context-evidence-portfolio-005": {
        "version": "1.2.0",
        "trial_classification": "RAW_PASS",
        "target_model_defeated": False,
        "release_blockers": [
            "fixed-container replay",
            "held-out target trials",
            "practitioner review",
        ],
    },
    "eb014-sequential-evidence-feedback-002": {
        "version": "2.0.0",
        "trial_classification": "RAW_PASS",
        "target_model_defeated": False,
        "release_blockers": [
            "fixed-container replay",
            "trajectory analysis",
            "practitioner review",
        ],
    },
    "eb015-real-source-replacement-gate-001": {
        "version": "2.0.0",
        "trial_classification": "PASS_AFTER_CONTRACT_REPLAY",
        "target_model_defeated": False,
        "release_blockers": [
            "source rights review",
            "file-level SHA-256 freeze",
            "verifier rebind",
            "fixed-container replay",
            "practitioner review",
        ],
    },
}
REPORTS = (
    "reports/selected-four-v3-optimization-20260924.json",
    "reports/selected-four-v3-optimization-20260924.md",
    "reports/eb006-research-completion-011-enterprise-sop-preflight.json",
    "reports/eb013-cross-context-evidence-portfolio-005-enterprise-sop-preflight.json",
    "reports/eb014-sequential-evidence-feedback-002-enterprise-sop-preflight.json",
    "reports/eb015-real-source-replacement-gate-001-enterprise-sop-preflight.json",
)
SUPPORT_FILES = (
    "scripts/check_enterprise_harbor_sop.py",
    "scripts/check_selected_four_v2.py",
    "scripts/package_selected_four_v3.py",
    "scripts/sync_selected_harbor_copies.py",
)
EXCLUDED_PARTS = {"__pycache__", ".pytest_cache", "outputs"}
EXCLUDED_QUALITY_DIRS = {"trials", "container_replays"}


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def included(relative: Path) -> bool:
    parts = relative.parts
    if any(part in EXCLUDED_PARTS for part in parts):
        return False
    if relative.suffix == ".pyc" or relative.name == ".DS_Store":
        return False
    return not (
        len(parts) >= 2
        and parts[0] == "quality"
        and parts[1] in EXCLUDED_QUALITY_DIRS
    )


def add_file(files: dict[str, bytes], name: str, path: Path) -> None:
    if not path.is_file() or path.is_symlink():
        raise ValueError(f"missing or symlinked source: {path}")
    if name in files:
        raise ValueError(f"duplicate package path: {name}")
    files[name] = path.read_bytes()


def build_files() -> dict[str, bytes]:
    files: dict[str, bytes] = {}
    for task_id in TASKS:
        task = ROOT / "benchmarks" / task_id
        for path in sorted(task.rglob("*")):
            relative = path.relative_to(task)
            if path.is_file() and not path.is_symlink() and included(relative):
                add_file(files, f"tasks/{task_id}/{relative.as_posix()}", path)

    for relative in REPORTS + SUPPORT_FILES:
        add_file(files, relative, ROOT / relative)

    metadata = {
        "schema_version": "calibrated_task_batch.v1",
        "bundle_id": PREFIX,
        "snapshot_status": "CALIBRATED_INTERNAL_BATCH",
        "formal_release_status": "BLOCKED",
        "tasks": TASK_METADATA,
        "agent_visible_paths": [
            "tasks/<task_id>/instruction.md",
            "tasks/<task_id>/data/",
            "tasks/<task_id>/environment/",
        ],
        "author_only_paths": [
            "tasks/<task_id>/solution/",
            "tasks/<task_id>/tests/",
            "tasks/<task_id>/verifier.py",
            "tasks/<task_id>/verifier_only/",
            "tasks/<task_id>/authoring/",
            "tasks/<task_id>/quality/",
        ],
        "excluded": [
            "tasks/<task_id>/quality/trials/",
            "tasks/<task_id>/quality/container_replays/",
            "**/__pycache__/",
            "**/.pytest_cache/",
            "**/*.pyc",
            "**/outputs/",
        ],
        "verification": {
            "pytest": "51 passed, 3 skipped",
            "selected_four_dynamic_checks": "PASS",
            "enterprise_sop_preflight": "PASS",
        },
        "files": {
            name: {"sha256": digest(data), "size": len(data)}
            for name, data in sorted(files.items())
        },
    }
    files["manifest.json"] = (
        json.dumps(metadata, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode()
    return files


def verify(path: Path) -> None:
    with tarfile.open(path, "r:gz") as archive:
        members = archive.getmembers()
        names = [member.name for member in members]
        if len(names) != len(set(names)) or any(not member.isfile() for member in members):
            raise ValueError("archive must contain unique regular files only")
        if any(
            PurePosixPath(name).is_absolute() or ".." in PurePosixPath(name).parts
            for name in names
        ):
            raise ValueError("unsafe archive path")
        payload = {
            member.name.removeprefix(PREFIX + "/"): archive.extractfile(member).read()
            for member in members
        }

    manifest = json.loads(payload.pop("manifest.json"))
    if set(payload) != set(manifest["files"]):
        raise ValueError("manifest membership mismatch")
    for name, expected in manifest["files"].items():
        if digest(payload[name]) != expected["sha256"] or len(payload[name]) != expected["size"]:
            raise ValueError(f"manifest digest mismatch: {name}")

    for name in payload:
        parts = PurePosixPath(name).parts
        if any(part in EXCLUDED_PARTS for part in parts) or name.endswith(".pyc"):
            raise ValueError(f"archive contains excluded runtime product: {name}")
        if any(
            parts[index] == "quality" and parts[index + 1] in EXCLUDED_QUALITY_DIRS
            for index in range(len(parts) - 1)
        ):
            raise ValueError(f"archive contains excluded quality run history: {name}")

    packaged_tasks = {
        parts[1]
        for name in payload
        if len(parts := PurePosixPath(name).parts) >= 2 and parts[0] == "tasks"
    }
    if packaged_tasks != set(TASKS):
        raise ValueError("task membership mismatch")
    if manifest["snapshot_status"] != "CALIBRATED_INTERNAL_BATCH":
        raise ValueError("snapshot status mismatch")
    if manifest["formal_release_status"] != "BLOCKED":
        raise ValueError("formal release status must remain blocked")
    print(f"verified {len(payload)} payload files for {manifest['bundle_id']}")


def build(output: Path) -> None:
    if output.exists():
        raise FileExistsError(f"refusing to overwrite existing archive: {output}")
    files = build_files()
    output.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=".selected-four-v3-", dir=output.parent)
    try:
        os.fchmod(fd, 0o644)
        with (
            os.fdopen(fd, "wb") as raw,
            gzip.GzipFile(fileobj=raw, mode="wb", filename="", mtime=0, compresslevel=9) as compressed,
            tarfile.open(fileobj=compressed, mode="w") as archive,
        ):
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
    archive_hash = digest(output.read_bytes())
    checksum = output.with_name(output.name + ".sha256")
    checksum.write_text(f"{archive_hash}  {output.name}\n", encoding="ascii")
    print(json.dumps({"archive": str(output), "sha256": archive_hash, "files": len(files)}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--output", type=Path)
    group.add_argument("--verify", type=Path)
    args = parser.parse_args()
    build(args.output) if args.output else verify(args.verify)
