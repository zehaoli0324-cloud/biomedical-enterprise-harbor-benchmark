#!/usr/bin/env python3
"""Build a reproducible provisional author bundle for EB014."""

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

from check_enterprise_harbor_sop import evaluate


ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "eb014-adaptive-evidence-ladder-003"
PREFIX = "eb014-adaptive-evidence-ladder-003-l12-data-heavy-20260924-v020"
TRIAL = Path("/private/tmp/eb014-l12-data-heavy-trial-20260924-final/adaptive-ladder-dataheavy-gpt56sol-002")
TRIAL_FILES = (
    "manifest.json",
    "verifier_result.json",
    "agent_workspace/trajectory_summary.json",
    "agent_workspace/outputs/audit.md",
    "agent_workspace/outputs/completion.json",
    "agent_workspace/outputs/contingent_policy.json",
    "agent_workspace/outputs/policy_certificate.json",
    "agent_workspace/outputs/provenance.json",
    "agent_workspace/outputs/research_log.json",
)


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def add(files: dict[str, bytes], name: str, source: Path) -> None:
    if source.is_symlink() or not source.is_file():
        raise ValueError(f"missing or symlinked file: {source}")
    if name in files:
        raise ValueError(f"duplicate package path: {name}")
    files[name] = source.read_bytes()


def payload() -> dict[str, bytes]:
    task = ROOT / "benchmarks" / TASK_ID
    preflight = evaluate(task)
    files: dict[str, bytes] = {
        "README.md": (
            "# EB014 adaptive evidence ladder v0.2.0\n\n"
            "Provisional author bundle for the L12 data-heavy static contingent-policy replay after numeric evidence expansion.\n"
            "The task package and target trial are included for review. The target model trial is\n"
            "RAW_PASS and did not establish target-model defeat. Harbor SOP release remains\n"
            "BLOCKED until the enterprise quality cards and control records are materialized.\n"
        ).encode("utf-8")
    }
    for source in sorted(task.rglob("*")):
        if source.is_file() and "__pycache__" not in source.parts and source.suffix != ".pyc":
            add(files, f"tasks/{TASK_ID}/{source.relative_to(task).as_posix()}", source)
    for relative in TRIAL_FILES:
        add(files, f"trials/{TASK_ID}/adaptive-ladder-dataheavy-gpt56sol-002/{relative}", TRIAL / relative)
    trial_manifest = json.loads((TRIAL / "manifest.json").read_text(encoding="utf-8"))
    trial_verdict = json.loads((TRIAL / "verifier_result.json").read_text(encoding="utf-8"))
    trial_summary = {
        "task_id": TASK_ID,
        "trial_id": trial_manifest.get("trial_id"),
        "model": "gpt-5.6-sol",
        "runner_status": trial_manifest.get("status"),
        "verifier_status": trial_manifest.get("verifier_status"),
        "verifier_passed": trial_verdict.get("passed"),
        "agent_exit_code": trial_manifest.get("agent_exit_code"),
        "explicit_model_turns": 17,
        "accepted_actions": 12,
        "target_model_defeated": False,
    }
    files["trials/trial-summary.json"] = (json.dumps(trial_summary, indent=2, sort_keys=True) + "\n").encode("utf-8")
    files["reports/enterprise-sop-preflight.json"] = (json.dumps(preflight, indent=2, sort_keys=True) + "\n").encode("utf-8")
    metadata = {
        "schema_version": "eb014_provisional_author_bundle.v1",
        "task_id": TASK_ID,
        "package_id": PREFIX,
        "release_status": "BLOCKED",
        "release_blockers": preflight.get("release_blockers", []),
        "target_trial": trial_summary,
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
    print(f"verified {len(contents)} payload files for {metadata['task_id']}")


def build(output: Path) -> None:
    if output.exists():
        raise FileExistsError(f"refusing to overwrite existing archive: {output}")
    files = payload()
    output.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=".eb014-package-", dir=output.parent)
    try:
        os.fchmod(fd, 0o644)
        with os.fdopen(fd, "wb") as raw, gzip.GzipFile(fileobj=raw, mode="wb", filename="", mtime=0) as compressed, tarfile.open(fileobj=compressed, mode="w") as archive:
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
