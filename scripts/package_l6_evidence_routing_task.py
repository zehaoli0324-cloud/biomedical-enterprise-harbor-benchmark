#!/usr/bin/env python3
"""Package and verify the EB013 L6 evidence-routing author bundle."""

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
TASK_ID = "eb013-evidence-budget-routing-001"
PREFIX = "l6-evidence-budget-routing-013"
TRIALS = {
    "trial-gpt56-sol-001": Path("/private/tmp/benchmark-runs/eb013-evidence-budget-routing-001-l6/trial-gpt56-sol-001"),
    "eb013-evidence-budget-routing-001-gpt56sol-001": Path("/private/tmp/enterprise-l6-target-trials/eb013-evidence-budget-routing-001-gpt56sol-001"),
}
TRIAL_FILES = (
    "manifest.json",
    "verifier_result.json",
    "agent_workspace/outputs/plan.json",
    "agent_workspace/outputs/route.tsv",
    "agent_workspace/outputs/decision.json",
    "agent_workspace/outputs/provenance.json",
    "agent_workspace/outputs/audit.md",
)


def trial_source(trial: Path, relative: str) -> Path:
    """Resolve canonical runner outputs, accepting legacy root-level outputs."""
    source = trial / relative
    if source.is_file():
        return source
    if relative.startswith("agent_workspace/outputs/"):
        legacy = trial / "outputs" / relative.removeprefix("agent_workspace/outputs/")
        if legacy.is_file():
            return legacy
    return source


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
    if preflight["status"] != "PASS":
        raise ValueError(f"SOP preflight failed: {preflight['blockers']}")
    sop = json.loads((task / "quality/sop_card.json").read_text(encoding="utf-8"))
    if sop.get("release_status") != "BLOCKED":
        raise ValueError("author bundle must remain release blocked")
    audit = json.loads((task / "quality/independent_verifier_audit.json").read_text(encoding="utf-8"))
    if audit.get("status") != "PASS" or audit.get("review_status") != "pass":
        raise ValueError("independent verifier audit missing")
    files: dict[str, bytes] = {
        "README.md": (
            "# L6 evidence-budget routing bundle\n\n"
            "Author-side calibration bundle for eb013-evidence-budget-routing-001. "
            "The solving agent receives only instruction.md, data/ and writable outputs/. "
            "Release remains blocked pending fixed-container replay and practitioner review.\n"
        ).encode("utf-8")
    }
    add(files, "tranche/scale_tranche_012.json", ROOT / "candidate_pools/enterprise-v1/scale_tranche_012.json")
    add(files, "contracts/eb013-evidence-budget-routing-001.toml", ROOT / "candidate_pools/enterprise-v1/contracts/eb013-evidence-budget-routing-001.toml")
    add(files, "reports/eb013-evidence-budget-routing-001-enterprise-sop-preflight.json", ROOT / "reports/eb013-evidence-budget-routing-001-enterprise-sop-preflight.json")
    for source in sorted(task.rglob("*")):
        if source.is_file() and "__pycache__" not in source.parts and source.suffix != ".pyc":
            add(files, f"tasks/{TASK_ID}/{source.relative_to(task).as_posix()}", source)
    trial_summary: dict[str, object] = {"task_id": TASK_ID, "trials": []}
    evidence_by_trial = {}
    for evidence_path in sorted((task / "quality").glob("target_trial_evidence*.json")):
        evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
        evidence_by_trial[evidence.get("trial_id")] = evidence
    for trial_id, trial in TRIALS.items():
        for relative in TRIAL_FILES:
            add(files, f"trials/{TASK_ID}/{trial_id}/{relative}", trial_source(trial, relative))
        verdict = json.loads((trial / "verifier_result.json").read_text(encoding="utf-8"))
        manifest = json.loads((trial / "manifest.json").read_text(encoding="utf-8"))
        summary = {
            "trial_id": trial_id,
            "verifier_passed": verdict.get("passed"),
            "verifier_errors": verdict.get("errors", []),
            "agent_exit_code": manifest.get("agent_exit_code"),
            "timed_out": manifest.get("timed_out", False),
            "trial_path": f"trials/{TASK_ID}/{trial_id}",
        }
        evidence = evidence_by_trial.get(trial_id)
        if evidence:
            summary["evidence_interpretation"] = evidence.get("interpretation")
            replay = evidence.get("unchanged_artifact_contract_replay")
            summary["contract_replay"] = replay.get("status") if isinstance(replay, dict) else replay
            summary["initial_failure"] = evidence.get("initial_failure")
        trial_summary["trials"].append(summary)
    files["tranche/trial-summary.json"] = (json.dumps(trial_summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")
    metadata = {
        "schema_version": "l6_evidence_routing_bundle.v1",
        "task_id": TASK_ID,
        "tranche_id": "TRANCHE-012",
        "module": "math_minimax_evidence_route_selection",
        "release_status": "BLOCKED",
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
    fd, temporary = tempfile.mkstemp(prefix=".l6-package-", dir=output.parent)
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
