#!/usr/bin/env python3
"""Build and verify the calibrated internal snapshot for EB006-011."""
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
TASK_ID = "eb006-research-completion-011"
PREFIX = f"{TASK_ID}-calibrated-20260924"
EXCLUDED_PARTS = {"__pycache__", ".pytest_cache", "outputs"}


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def included(relative: Path) -> bool:
    parts = relative.parts
    return (
        not any(part in EXCLUDED_PARTS for part in parts)
        and relative.suffix != ".pyc"
        and relative.name != ".DS_Store"
        and parts[:2] != ("quality", "trials")
    )


def build_files() -> dict[str, bytes]:
    files: dict[str, bytes] = {}
    task = ROOT / "benchmarks" / TASK_ID
    for path in sorted(task.rglob("*")):
        relative = path.relative_to(task)
        if path.is_file() and not path.is_symlink() and included(relative):
            files[f"task/{relative.as_posix()}"] = path.read_bytes()

    for relative in (
        f"reports/{TASK_ID}-enterprise-sop-preflight.json",
        "reports/selected-four-v2-target-trials-20260924.json",
        "reports/selected-four-v2-target-trials-20260924.md",
    ):
        path = ROOT / relative
        if not path.is_file() or path.is_symlink():
            raise ValueError(f"missing or symlinked report: {path}")
        files[relative] = path.read_bytes()

    metadata = {
        "schema_version": "calibrated_internal_snapshot.v1",
        "bundle_id": PREFIX,
        "task_id": TASK_ID,
        "snapshot_status": "CALIBRATED_INTERNAL_SNAPSHOT",
        "formal_release_status": "BLOCKED",
        "release_blockers": [
            "fixed-container release replay",
            "practitioner review",
            "real-data replacement",
        ],
        "target_trial": {
            "model": "gpt-5.6-sol",
            "trial_id": "selected4-eb006-gpt56sol-v2-002",
            "classification": "SCIENTIFIC_FAIL_CONTRACT_PASS",
            "valid_difficulty_evidence": True,
        },
        "agent_visible_paths": ["task/instruction.md", "task/data/", "task/environment/"],
        "author_only_paths": [
            "task/solution/",
            "task/tests/",
            "task/verifier.py",
            "task/verifier_only/",
            "task/authoring/",
            "task/quality/",
        ],
        "excluded": ["task/quality/trials/", "**/__pycache__/", "**/*.pyc", "**/outputs/"],
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
        if any(PurePosixPath(name).is_absolute() or ".." in PurePosixPath(name).parts for name in names):
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
    forbidden = ("quality/trials/", "__pycache__", ".pyc", "/outputs/")
    if any(any(token in name for token in forbidden) for name in payload):
        raise ValueError("archive contains excluded run product")
    if manifest["snapshot_status"] != "CALIBRATED_INTERNAL_SNAPSHOT":
        raise ValueError("snapshot status mismatch")
    if manifest["formal_release_status"] != "BLOCKED":
        raise ValueError("formal release must remain blocked")
    print(f"verified {len(payload)} payload files for {manifest['bundle_id']}")


def build(output: Path) -> None:
    if output.exists():
        raise FileExistsError(f"refusing to overwrite existing archive: {output}")
    files = build_files()
    output.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=".eb006-011-calibrated-", dir=output.parent)
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
