#!/usr/bin/env python3
"""Build an author-side V1.2 package for the next closed-loop task batch."""

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
PREFIX = "l5-next-batch-010"
TASKS = (
    "eb010-closed-loop-replay-003",
    "eb010-closed-loop-ambiguity-004",
    "eb010-distributional-policy-stress-006",
)
README = """# L5 next batch 010: V1.2 SOP calibration bundle

This author-side bundle contains three closed-loop policy tasks covering L5,
L5.1 and L5.3. Each task passed the V1.2 structural preflight, has an explicit
contract audit, a difficulty budget, held-out variant declarations, controls,
baselines and an independent verifier audit. Target-model records are retained
with their original contract-replay attribution; a contract replay pass is not
scientific difficulty evidence.

The package is not agent-facing and is not READY_FOR_HARBOR. Fixed-container
replay, practitioner review and held-out variant runs remain release blockers.
"""


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def add(files: dict[str, bytes], destination: str, source: Path) -> None:
    if source.is_symlink() or not source.is_file():
        raise ValueError(f"missing or symlinked file: {source}")
    if destination in files:
        raise ValueError(f"duplicate package path: {destination}")
    files[destination] = source.read_bytes()


def payload() -> dict[str, bytes]:
    files = {"README.md": README.encode()}
    add(files, "tranche/scale_tranche_010.json", ROOT / "candidate_pools/enterprise-v1/scale_tranche_010.json")
    summary = {"schema_version": "next_l5_batch_trial_summary.v1", "tranche_id": "TRANCHE-010", "tasks": {}}
    for task_id in TASKS:
        task = ROOT / "benchmarks" / task_id
        check = evaluate(task)
        if check["status"] != "PASS":
            raise ValueError(f"SOP preflight failed for {task_id}: {check['blockers']}")
        quality = task / "quality"
        sop = json.loads((quality / "sop_card.json").read_text())
        if sop.get("sop_version") != "enterprise-harbor-sop-v1.2":
            raise ValueError(f"V1.2 SOP card required for {task_id}")
        audit = json.loads((quality / "independent_verifier_audit.json").read_text())
        if audit.get("status") != "PASS" or audit.get("review_status") != "pass":
            raise ValueError(f"independent audit missing for {task_id}")
        for source in sorted(task.rglob("*")):
            if source.is_file() and "__pycache__" not in source.parts and source.suffix != ".pyc":
                add(files, f"tasks/{task_id}/{source.relative_to(task).as_posix()}", source)
        report_path = ROOT / "reports" / f"{task_id}-enterprise-sop-preflight.json"
        if report_path.is_file():
            add(files, f"reports/{report_path.name}", report_path)
        results = json.loads((quality / "model_trial_results.json").read_text())
        difficulty = json.loads((quality / "difficulty_card.json").read_text())
        summary["tasks"][task_id] = {
            "level": next((item["level"] for item in json.loads((ROOT / "candidate_pools/enterprise-v1/scale_tranche_010.json").read_text())["recommended_candidates"] if item["candidate_id"] == task_id), None),
            "sop_preflight": check["status"],
            "target_model_status": results.get("target_model_status"),
            "trial_records": [
                {key: row.get(key) for key in ("strategy", "trial_id", "status", "passed", "valid_difficulty_evidence", "failure_attribution", "runner_status", "verifier_status", "timed_out")}
                for row in results.get("records", []) if row.get("strategy") == "target_model"
            ],
            "primary_module": difficulty.get("primary_module"),
            "secondary_modules": difficulty.get("secondary_modules", []),
            "held_out_variants": difficulty.get("held_out_variants", []),
            "contract_audit": "tasks/%s/quality/contract_audit.json" % task_id,
            "independent_audit": "tasks/%s/quality/independent_verifier_audit.json" % task_id,
        }
    files["tranche/trial-summary.json"] = (json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode()
    metadata = {
        "schema_version": "l5_next_batch_bundle.v1",
        "tranche_id": "TRANCHE-010",
        "release_status": "BLOCKED",
        "tasks": summary["tasks"],
    }
    metadata["files"] = {name: {"sha256": sha(content), "size": len(content)} for name, content in sorted(files.items())}
    files["manifest.json"] = (json.dumps(metadata, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode()
    return files


def verify(path: Path) -> None:
    with tarfile.open(path, "r:gz") as archive:
        members = archive.getmembers()
        if len({member.name for member in members}) != len(members) or any(not member.isfile() for member in members):
            raise ValueError("duplicate or non-file archive member")
        prefix = PREFIX + "/"
        contents = {member.name.removeprefix(prefix): archive.extractfile(member).read() for member in members}
    metadata = json.loads(contents.pop("manifest.json"))
    if set(contents) != set(metadata["files"]):
        raise ValueError("manifest membership mismatch")
    for name, item in metadata["files"].items():
        if sha(contents[name]) != item["sha256"] or len(contents[name]) != item["size"]:
            raise ValueError(f"hash mismatch: {name}")
    print(f"verified {len(contents)} payload files for {len(metadata['tasks'])} tasks")


def build(output: Path) -> None:
    if output.exists():
        raise FileExistsError(output)
    files = payload()
    output.parent.mkdir(parents=True, exist_ok=True)
    fd, temp = tempfile.mkstemp(prefix=".l5-package-", dir=output.parent)
    try:
        os.fchmod(fd, 0o644)
        with os.fdopen(fd, "wb") as raw, gzip.GzipFile(fileobj=raw, mode="wb", filename="", mtime=0) as compressed:
            with tarfile.open(fileobj=compressed, mode="w") as archive:
                for name, content in sorted(files.items()):
                    info = tarfile.TarInfo(f"{PREFIX}/{name}")
                    info.size, info.mode, info.mtime = len(content), 0o644, 0
                    archive.addfile(info, io.BytesIO(content))
        os.replace(temp, output)
    finally:
        if os.path.exists(temp):
            os.unlink(temp)
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
