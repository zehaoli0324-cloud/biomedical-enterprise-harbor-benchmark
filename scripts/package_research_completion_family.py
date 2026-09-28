#!/usr/bin/env python3
"""Build a deterministic staging archive for the EB006 research family."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import io
import json
import os
import tarfile
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PREFIX = "eb006-research-completion-family-20260924"
TASKS = (
    "eb006-research-completion-009",
    "eb006-research-completion-010",
    "eb006-research-completion-011",
)


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def build_files() -> dict[str, bytes]:
    files: dict[str, bytes] = {}

    def add(name: str, path: Path) -> None:
        if not path.is_file() or path.is_symlink():
            raise ValueError(f"missing or symlinked source: {path}")
        if name in files:
            raise ValueError(f"duplicate package path: {name}")
        files[name] = path.read_bytes()

    for task_id in TASKS:
        task = ROOT / "benchmarks" / task_id
        for path in sorted(task.rglob("*")):
            if path.is_file() and "__pycache__" not in path.parts and path.suffix != ".pyc":
                add(f"tasks/{task_id}/{path.relative_to(task).as_posix()}", path)
        report = ROOT / "reports" / f"{task_id}-enterprise-sop-preflight.json"
        if report.is_file():
            add(f"reports/{report.name}", report)

    for relative in (
        "scripts/audit_cross_assay_completion.py",
        "scripts/materialize_research_harbor_package.py",
        "scripts/standardize_research_completion_quality.py",
        "scripts/check_enterprise_harbor_sop.py",
    ):
        add(relative, ROOT / relative)

    metadata = {
        "schema_version": "enterprise_staging_bundle.v1",
        "bundle_id": PREFIX,
        "tasks": list(TASKS),
        "release_status": "BLOCKED",
        "release_blockers": [
            "fixed-container replay",
            "target-model trial for 010",
            "practitioner review",
            "real-data replacement",
        ],
        "scientific_boundary": "all three tasks use disclosed synthetic measurements for analytical triage only",
        "files": {name: {"sha256": digest(data), "size": len(data)} for name, data in sorted(files.items())},
    }
    files["manifest.json"] = (json.dumps(metadata, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode()
    return files


def verify(path: Path) -> None:
    with tarfile.open(path, "r:gz") as archive:
        members = archive.getmembers()
        if len({member.name for member in members}) != len(members) or any(not member.isfile() for member in members):
            raise ValueError("duplicate or non-file archive member")
        contents = {member.name.removeprefix(PREFIX + "/"): archive.extractfile(member).read() for member in members}
    metadata = json.loads(contents.pop("manifest.json"))
    if set(contents) != set(metadata["files"]):
        raise ValueError("manifest membership mismatch")
    for name, item in metadata["files"].items():
        if digest(contents[name]) != item["sha256"] or len(contents[name]) != item["size"]:
            raise ValueError(f"archive hash mismatch: {name}")
    if metadata["release_status"] != "BLOCKED":
        raise ValueError("staging bundle must remain release blocked")
    print(f"verified {len(contents)} payload files for {metadata['bundle_id']}")


def build(output: Path) -> None:
    if output.exists():
        raise FileExistsError(f"refusing to overwrite existing archive: {output}")
    files = build_files()
    output.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=".eb006-family-", dir=output.parent)
    try:
        os.fchmod(fd, 0o644)
        with os.fdopen(fd, "wb") as raw, gzip.GzipFile(fileobj=raw, mode="wb", filename="", mtime=0, compresslevel=9) as compressed, tarfile.open(fileobj=compressed, mode="w") as archive:
            for name, data in sorted(files.items()):
                info = tarfile.TarInfo(f"{PREFIX}/{name}")
                info.size, info.mode, info.mtime = len(data), 0o644, 0
                archive.addfile(info, io.BytesIO(data))
        os.replace(temporary, output)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    verify(output)
    print(json.dumps({"archive": str(output), "sha256": digest(output.read_bytes()), "files": len(files)}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    parser.add_argument("--verify", type=Path)
    args = parser.parse_args()
    if (args.output is None) == (args.verify is None):
        parser.error("provide exactly one of --output or --verify")
    build(args.output) if args.output else verify(args.verify)
