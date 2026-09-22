#!/usr/bin/env python3
"""Package the L5.4 cross-stage task and its completed target trial."""

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
TASK_ID = "eb012-cross-stage-chain-002"
PREFIX = "l54-cross-stage-task-011"
TRIALS = {
    "gpt56sol-001": Path("/private/tmp/enterprise-l54-target-trials/eb012-cross-stage-chain-002-gpt56sol-001"),
    "gpt56sol-002": Path("/private/tmp/enterprise-l54-target-trials-v2/eb012-cross-stage-chain-002-gpt56sol-002"),
    "gpt56sol-003": Path("/private/tmp/enterprise-l54-target-trials-v3/eb012-cross-stage-chain-002-gpt56sol-003"),
    "gpt56sol-004": Path("/private/tmp/enterprise-l54-target-trials-v4/eb012-cross-stage-chain-002-gpt56sol-004"),
}
TRIAL_FILES = ("manifest.json", "verifier_result.json", "agent_workspace/outputs/chain.json", "agent_workspace/outputs/handoff.tsv", "agent_workspace/outputs/audit.md", "agent_workspace/outputs/manifest.json")


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def add(files: dict[str, bytes], name: str, path: Path) -> None:
    if not path.is_file() or path.is_symlink():
        raise ValueError(f"missing or symlinked file: {path}")
    files[name] = path.read_bytes()


def payload() -> dict[str, bytes]:
    task = ROOT / "benchmarks" / TASK_ID
    check = evaluate(task)
    if check["status"] != "PASS":
        raise ValueError(check["blockers"])
    files = {"README.md": b"# L5.4 cross-stage task 011\n\nAuthor-side package. Four target trials are retained: all completed the chain audit, raw output formatting required verifier compatibility replay, and release remains blocked pending fixed-container replay and practitioner review.\n"}
    add(files, "tranche/scale_tranche_011.json", ROOT / "candidate_pools/enterprise-v1/scale_tranche_011.json")
    for path in sorted(task.rglob("*")):
        if path.is_file() and "__pycache__" not in path.parts and path.suffix != ".pyc":
            add(files, f"tasks/{TASK_ID}/{path.relative_to(task).as_posix()}", path)
    for label, trial in TRIALS.items():
        for path in TRIAL_FILES:
            add(files, f"trials/{TASK_ID}/{label}/{path}", trial / path)
    report = json.loads((task / "quality/model_trial_results.json").read_text())
    summary = {"task_id": TASK_ID, "target_model_status": report.get("target_model_status"), "records": [row for row in report.get("records", []) if row.get("strategy") == "target_model"], "included_trials": sorted(TRIALS), "artifact_boundary": "original model outputs are immutable; only verifier compatibility was repaired"}
    files["tranche/trial-summary.json"] = (json.dumps(summary, indent=2) + "\n").encode()
    metadata = {"schema_version": "l54_task_bundle.v1", "tranche_id": "TRANCHE-011", "release_status": "BLOCKED", "files": {name: {"sha256": digest(data), "size": len(data)} for name, data in sorted(files.items())}}
    files["manifest.json"] = (json.dumps(metadata, indent=2, sort_keys=True) + "\n").encode()
    return files


def verify(path: Path) -> None:
    with tarfile.open(path, "r:gz") as archive:
        members = archive.getmembers(); contents = {member.name.removeprefix(PREFIX + "/"): archive.extractfile(member).read() for member in members}
    metadata = json.loads(contents.pop("manifest.json"))
    if set(contents) != set(metadata["files"]): raise ValueError("manifest membership mismatch")
    for name, item in metadata["files"].items():
        if digest(contents[name]) != item["sha256"] or len(contents[name]) != item["size"]: raise ValueError(f"hash mismatch: {name}")
    print(f"verified {len(contents)} payload files")


def build(output: Path) -> None:
    if output.exists(): raise FileExistsError(output)
    files = payload(); output.parent.mkdir(parents=True, exist_ok=True); fd, temp = tempfile.mkstemp(prefix=".l54-package-", dir=output.parent)
    try:
        os.fchmod(fd, 0o644)
        with os.fdopen(fd, "wb") as raw, gzip.GzipFile(fileobj=raw, mode="wb", filename="", mtime=0) as compressed, tarfile.open(fileobj=compressed, mode="w") as archive:
            for name, data in sorted(files.items()):
                info = tarfile.TarInfo(f"{PREFIX}/{name}"); info.size, info.mode, info.mtime = len(data), 0o644, 0; archive.addfile(info, io.BytesIO(data))
        os.replace(temp, output)
    finally:
        if os.path.exists(temp): os.unlink(temp)
    verify(output); print(json.dumps({"archive": str(output), "sha256": digest(output.read_bytes()), "files": len(files)}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(); parser.add_argument("--output", type=Path); parser.add_argument("--verify", type=Path); args = parser.parse_args()
    if (args.output is None) == (args.verify is None): parser.error("provide exactly one of --output or --verify")
    build(args.output) if args.output else verify(args.verify)
