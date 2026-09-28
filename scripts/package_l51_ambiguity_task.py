#!/usr/bin/env python3
"""Package and verify the L5.1 self-planned ambiguity task author bundle."""

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
TASK_ID = "eb010-closed-loop-ambiguity-004"
PREFIX = "l51-ambiguity-self-plan-012"
TRIAL = Path("/private/tmp/benchmark-runs/eb010-closed-loop-ambiguity-004-v071/trial-gpt56-sol-005")
TRIAL_FILES = (
    "manifest.json",
    "verifier_result.json",
    "agent_workspace/outputs/plan.json",
    "agent_workspace/outputs/decision.json",
    "agent_workspace/outputs/evidence.tsv",
    "agent_workspace/outputs/discovery.json",
    "agent_workspace/outputs/audit.md",
)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def add(files: dict[str, bytes], destination: str, source: Path) -> None:
    if destination in files:
        raise ValueError(f"duplicate package path: {destination}")
    if source.is_symlink() or not source.is_file():
        raise ValueError(f"missing or symlinked file: {source}")
    files[destination] = source.read_bytes()


def payload() -> dict[str, bytes]:
    task = ROOT / "benchmarks" / TASK_ID
    check = evaluate(task)
    if check["status"] != "PASS":
        raise ValueError(f"SOP preflight failed: {check['blockers']}")
    quality = task / "quality"
    sop = json.loads((quality / "sop_card.json").read_text())
    if sop.get("sop_version") != "enterprise-harbor-sop-v1.2":
        raise ValueError("v1.2 SOP card required")
    if sop.get("release_status") != "BLOCKED":
        raise ValueError("author package must remain release blocked")
    audit = json.loads((quality / "independent_verifier_audit.json").read_text())
    if audit.get("status") != "PASS" or audit.get("review_status") != "pass":
        raise ValueError("independent verifier audit missing")
    results = json.loads((quality / "model_trial_results.json").read_text())
    record = next((row for row in results.get("records", []) if row.get("trial_id") == "trial-gpt56-sol-005"), None)
    if not record or record.get("passed") is not True:
        raise ValueError("v0.7.1 clean target trial record missing")
    files: dict[str, bytes] = {
        "README.md": (
            "# L5.1 self-planned ambiguity task bundle\n\n"
            "Author-side calibration bundle for eb010-closed-loop-ambiguity-004 v0.7.1. "
            "The package is not agent-facing and is not READY_FOR_HARBOR. Fixed-container replay, "
            "held-out variants and practitioner review remain release blockers.\n"
        ).encode()
    }
    add(files, "tranche/scale_tranche_007.json", ROOT / "candidate_pools/enterprise-v1/scale_tranche_007.json")
    add(files, "contracts/eb010-closed-loop-ambiguity-004.toml", ROOT / "candidate_pools/enterprise-v1/contracts/eb010-closed-loop-ambiguity-004.toml")
    add(files, "reports/eb010-closed-loop-ambiguity-004-enterprise-sop-preflight.json", ROOT / "reports/eb010-closed-loop-ambiguity-004-enterprise-sop-preflight.json")
    add(files, "reports/eb010-closed-loop-ambiguity-004-verification-agent.json", ROOT / "reports/eb010-closed-loop-ambiguity-004-verification-agent.json")
    for source in sorted(task.rglob("*")):
        if source.is_file() and "__pycache__" not in source.parts and source.suffix != ".pyc":
            add(files, f"tasks/{TASK_ID}/{source.relative_to(task).as_posix()}", source)
    for relative in TRIAL_FILES:
        add(files, f"trials/{TASK_ID}/{relative}", TRIAL / relative)
    summary = {
        "schema_version": "l51_target_trial_summary.v1",
        "task_id": TASK_ID,
        "task_version": "0.7.1",
        "target_model": "gpt-5.6-sol",
        "trial_id": "trial-gpt56-sol-005",
        "status": "pass",
        "plan": {"operations": ["inventory", "interpret", "screen", "replay", "decide"], "total_cost": 6.5, "network_used": False, "stop_condition": "eligible_record_selected"},
        "avoided_shortcuts": ["label_scan", "top_only_replay", "external_lookup", "defer_all"],
        "release_status": "BLOCKED",
        "release_blockers": sop.get("release_blockers", []),
    }
    files["tranche/trial-summary.json"] = (json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode()
    metadata = {
        "schema_version": "l51_ambiguity_author_bundle.v1",
        "tranche_id": "TRANCHE-007",
        "task_id": TASK_ID,
        "task_version": "0.7.1",
        "agent_boundary": "author-side bundle; solving agent receives instruction.md, data/ and writable outputs/ only",
        "release_status": "BLOCKED",
        "files": {name: {"sha256": sha(content), "size": len(content)} for name, content in sorted(files.items())},
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
        if sha(contents[name]) != item["sha256"] or len(contents[name]) != item["size"]:
            raise ValueError(f"archive hash mismatch: {name}")
    print(f"verified {len(contents)} payload files for {metadata['task_id']}")


def build(output: Path) -> None:
    if output.exists():
        raise FileExistsError(f"refusing to overwrite existing archive: {output}")
    files = payload()
    output.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=".l51-package-", dir=output.parent)
    try:
        os.fchmod(fd, 0o644)
        with os.fdopen(fd, "wb") as raw, gzip.GzipFile(fileobj=raw, mode="wb", filename="", mtime=0) as compressed, tarfile.open(fileobj=compressed, mode="w") as archive:
            for name, content in sorted(files.items()):
                info = tarfile.TarInfo(f"{PREFIX}/{name}")
                info.size, info.mode, info.mtime = len(content), 0o644, 0
                archive.addfile(info, io.BytesIO(content))
        os.replace(temporary, output)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    verify(output)
    print(json.dumps({"archive": str(output), "sha256": sha(output.read_bytes()), "files": len(files)}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    parser.add_argument("--verify", type=Path)
    args = parser.parse_args()
    if (args.output is None) == (args.verify is None):
        parser.error("provide exactly one of --output or --verify")
    build(args.output) if args.output else verify(args.verify)
