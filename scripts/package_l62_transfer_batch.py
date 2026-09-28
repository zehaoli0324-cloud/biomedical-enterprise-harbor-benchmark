#!/usr/bin/env python3
"""Build a reproducible author bundle for the L6.2 transfer tranche."""

from __future__ import annotations

import argparse
import hashlib
import gzip
import io
import json
import os
import tarfile
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PREFIX = "l6.2-transfer-tranche-014"
TASKS = ("eb013-evidence-budget-routing-002", "eb010-stop-uncertainty-002", "eb011-reproduction-manifest-001")


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
        add(f"contracts/{task_id}.toml", ROOT / "candidate_pools/enterprise-v1/contracts" / f"{task_id}.toml")
    add("tranche/scale_tranche_014.json", ROOT / "candidate_pools/enterprise-v1/scale_tranche_014.json")
    add("config/reusable_difficulty_modules.json", ROOT / "config/reusable_difficulty_modules.json")
    add("config/module_catalog.json", ROOT / "config/module_catalog.json")
    add("docs/enterprise-harbor-sop-v1.1.md", ROOT / "docs/enterprise-harbor-sop-v1.1.md")
    add("docs/enterprise-difficulty-escalation-v1.md", ROOT / "docs/enterprise-difficulty-escalation-v1.md")
    metadata = {
        "schema_version": "l6.2_transfer_bundle.v1",
        "tranche_id": "TRANCHE-014",
        "tasks": list(TASKS),
        "release_status": "BLOCKED",
        "release_blockers": ["fixed-container replay", "practitioner review"],
        "files": {name: {"sha256": digest(data), "size": len(data)} for name, data in sorted(files.items())},
    }
    files["manifest.json"] = (json.dumps(metadata, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")
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
    print(f"verified {len(contents)} payload files for {metadata['tranche_id']}")


def build(output: Path) -> None:
    if output.exists():
        raise FileExistsError(f"refusing to overwrite existing archive: {output}")
    files = build_files()
    output.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=".l62-package-", dir=output.parent)
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
