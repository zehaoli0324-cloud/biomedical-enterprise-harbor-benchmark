#!/usr/bin/env python3
"""Build and verify a provisional, author-side L4 calibration bundle."""

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
PREFIX = "l4-tranche-005-provisional"
TASKS = (
    "eb003-recovery-chain-005",
    "eb005-normalization-hierarchy-003",
    "eb008-route-portfolio-002",
    "eb010-next-batch-002",
    "eb011-measurement-request-005",
    "eb012-cross-handoff-audit-001",
)
TRIAL_FILES = (
    "manifest.json",
    "verifier_result.json",
    "agent_workspace/instruction.md",
    "agent_workspace/data/case.json",
    "agent_workspace/data/rules.json",
    "agent_workspace/outputs/decision.json",
    "agent_workspace/outputs/evidence.tsv",
    "agent_workspace/outputs/review.md",
    "agent_workspace/outputs/manifest.json",
)
README = """# L4 tranche 005: provisional calibration bundle

Six complete synthetic enterprise evaluation tasks are included under `tasks/`.
This is an author-side bundle: `verifier.py`, `verifier_only/`, `tests/`,
`quality/`, `contracts/`, and `trials/` must never be exposed to a solving agent.
The agent-visible workspace consists only of each task's `instruction.md` and
`data/`, with a writable `outputs/` directory.

The earlier target-model trial failed the exact output contract; its records
remain unchanged. A later run against clarified instructions passed the local
verifier for all six tasks. Both trial results and their minimal artifacts are
included for review. This is provisional acceptance for packaging, not a
claim that the earlier failures passed and not READY_FOR_HARBOR.

`tranche/l4-trial-summary.json` gives the machine-readable trial conditions and
failure attribution for all six tasks. `tranche/l4-difficulty-analysis.md` and
`tranche/l4-transferable-modules.json` explain which parts of the difficulty
are scientific, which parts were contract defects, and how to reuse the modules.

The recorded model runs used `process_cwd_only`. Independent practitioner
review and fixed-container replay are still required before release.
`manifest.json` lists the task statuses and SHA-256 of every packaged file.
"""


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def add_file(files: dict[str, bytes], destination: str, source: Path) -> None:
    if source.is_symlink() or not source.is_file():
        raise ValueError(f"missing or symlinked file: {source}")
    if destination in files:
        raise ValueError(f"duplicate package path: {destination}")
    files[destination] = source.read_bytes()


def payload() -> dict[str, bytes]:
    files = {"README.md": README.encode("utf-8")}
    metadata = {
        "schema_version": "l4_provisional_calibration_bundle.v1",
        "tranche_id": "TRANCHE-005",
        "acceptance": "PROVISIONAL_FOR_PACKAGING",
        "release_status": "BLOCKED",
        "execution_boundary": "author_side_bundle; agent sees instruction.md and data/ only",
        "trial_summary_path": "tranche/l4-trial-summary.json",
        "difficulty_analysis_path": "tranche/l4-difficulty-analysis.md",
        "transferable_modules_path": "tranche/l4-transferable-modules.json",
        "tasks": {},
    }
    add_file(files, "tranche/scale_tranche_005.json", ROOT / "candidate_pools/enterprise-v1/scale_tranche_005.json")
    add_file(files, "tranche/difficulty.md", ROOT / "docs/enterprise-difficulty-escalation-v1.md")
    add_file(files, "tranche/l4-difficulty-analysis.md", ROOT / "docs/l4-tranche-005-difficulty-analysis.md")
    add_file(files, "tranche/l4-transferable-modules.json", ROOT / "config/l4_tranche_005_transferable_modules.json")
    trial_summary = {
        "schema_version": "l4_trial_summary.v1",
        "tranche_id": "TRANCHE-005",
        "trial_scope": "author_side_process_cwd_only",
        "contract_repair_interpretation": "initial failures are retained as contract-defect evidence; revised trials test the clarified contract",
        "tasks": {},
    }
    for task_id in TASKS:
        task = ROOT / "benchmarks" / task_id
        check = evaluate(task)
        if check["status"] != "PASS":
            raise ValueError(f"SOP preflight failed for {task_id}: {check['blockers']}")
        quality = task / "quality"
        results = json.loads((quality / "model_trial_results.json").read_text())
        sop = json.loads((quality / "sop_card.json").read_text())
        audit = json.loads((quality / "independent_verifier_audit.json").read_text())
        if results.get("target_model_status") != "PASS" or sop.get("release_status") != "BLOCKED":
            raise ValueError(f"unexpected trial/release state for {task_id}")
        if audit.get("status") != "PASS" or audit.get("review_status") != "pass":
            raise ValueError(f"independent verifier audit missing for {task_id}")
        trial_records = [row for row in results.get("records", []) if row.get("strategy") == "target_model"]
        if not any(row.get("passed") is True for row in trial_records) or not any(row.get("passed") is False for row in trial_records):
            raise ValueError(f"both target trial outcomes required for {task_id}")
        packaged_trials = []
        for row in trial_records:
            trial = Path(row["trial_dir"])
            trial_id = row["trial_id"]
            trial_manifest = json.loads((trial / "manifest.json").read_text())
            verdict = json.loads((trial / "verifier_result.json").read_text())
            if verdict.get("passed") is not row["passed"]:
                raise ValueError(f"trial verdict mismatch: {task_id}/{trial_id}")
            for relative in TRIAL_FILES:
                add_file(files, f"trials/{task_id}/{trial_id}/{relative}", trial / relative)
            packaged_trials.append({
                "trial_id": trial_id,
                "passed": row["passed"],
                "task_version": row.get("task_version"),
                "model": row.get("model"),
                "runner_status": row.get("runner_status"),
                "agent_exit_code": row.get("agent_exit_code"),
                "timed_out": row.get("timed_out"),
                "verifier_status": row.get("verifier_status"),
                "failure_attribution": row.get("failure_attribution"),
                "verifier_errors": row.get("verifier_errors", []),
                "artifact_sha256": row.get("artifact_sha256"),
                "isolation_mode": trial_manifest.get("isolation_mode"),
                "trial_path": f"trials/{task_id}/{trial_id}",
            })
        for source in sorted(task.rglob("*")):
            if not source.is_file() or "__pycache__" in source.parts or source.suffix == ".pyc":
                continue
            add_file(files, f"tasks/{task_id}/{source.relative_to(task).as_posix()}", source)
        contract = ROOT / "candidate_pools/enterprise-v1/contracts" / f"{task_id}.toml"
        add_file(files, f"contracts/{task_id}.toml", contract)
        metadata["tasks"][task_id] = {
            "task_version": next(line.split(":", 1)[1].strip().strip('"') for line in (task / "task.yaml").read_text().splitlines() if line.startswith("version:")),
            "target_model_status": results["target_model_status"],
            "release_status": sop["release_status"],
            "release_blockers": sop.get("release_blockers", []),
            "trials": packaged_trials,
        }
        trial_summary["tasks"][task_id] = {
            "quality_card_path": f"tasks/{task_id}/quality/model_trial_card.json",
            "quality_results_path": f"tasks/{task_id}/quality/model_trial_results.json",
            "target_model_status": results.get("target_model_status"),
            "records": packaged_trials,
            "independent_verifier_audit": {
                "status": audit.get("status"),
                "review_status": audit.get("review_status"),
                "report_path": f"tasks/{task_id}/quality/independent_verifier_audit.json",
            },
        }
        preflight = ROOT / "reports" / f"{task_id}-enterprise-sop-preflight.json"
        verification = ROOT / "reports" / f"{task_id}-verification-agent.json"
        add_file(files, f"reports/{preflight.name}", preflight)
        add_file(files, f"reports/{verification.name}", verification)
        verification_report = json.loads(verification.read_text())
        trial_summary["tasks"][task_id]["sop_preflight_report_path"] = f"reports/{preflight.name}"
        trial_summary["tasks"][task_id]["verification_agent"] = {
            "status": verification_report.get("status"),
            "report_path": f"reports/{verification.name}",
        }
    files["tranche/l4-trial-summary.json"] = (json.dumps(trial_summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")
    metadata["files"] = {path: {"sha256": digest(content), "size": len(content)} for path, content in sorted(files.items())}
    files["manifest.json"] = (json.dumps(metadata, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")
    return files


def build(output: Path) -> None:
    if output.exists():
        raise FileExistsError(f"refusing to overwrite existing archive: {output}")
    files = payload()
    output.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=".l4-package-", dir=output.parent)
    try:
        os.fchmod(fd, 0o644)
        with os.fdopen(fd, "wb") as raw, gzip.GzipFile(fileobj=raw, mode="wb", filename="", mtime=0) as compressed:
            with tarfile.open(fileobj=compressed, mode="w") as archive:
                for name, content in sorted(files.items()):
                    info = tarfile.TarInfo(f"{PREFIX}/{name}")
                    info.size = len(content)
                    info.mode = 0o644
                    info.mtime = 0
                    archive.addfile(info, io.BytesIO(content))
        os.replace(temporary, output)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    verify(output)
    print(json.dumps({"archive": str(output), "sha256": digest(output.read_bytes()), "files": len(files), "tasks": len(TASKS)}))


def verify(path: Path) -> None:
    with tarfile.open(path, mode="r:gz") as archive:
        members = archive.getmembers()
        if len({member.name for member in members}) != len(members) or any(not member.isfile() for member in members):
            raise ValueError("duplicate or non-file archive member")
        contents = {member.name.removeprefix(PREFIX + "/"): archive.extractfile(member).read() for member in members}
    metadata = json.loads(contents.pop("manifest.json"))
    expected = metadata["files"]
    if set(contents) != set(expected) or len(metadata["tasks"]) != len(TASKS):
        raise ValueError("archive manifest membership mismatch")
    for name, properties in expected.items():
        if digest(contents[name]) != properties["sha256"] or len(contents[name]) != properties["size"]:
            raise ValueError(f"archive hash mismatch: {name}")
    print(f"verified {len(contents)} payload files for {len(TASKS)} tasks")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--verify", type=Path)
    args = parser.parse_args()
    if (args.output is None) == (args.verify is None):
        parser.error("provide exactly one of --output or --verify")
    if args.output:
        build(args.output)
    else:
        verify(args.verify)
