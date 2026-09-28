#!/usr/bin/env python3
"""Audit a real-source replacement card without downloading or inventing data.

The audit is intentionally metadata-only.  A source can be marked ready for
review only when its rights, file-level SHA-256 and verifier rebind evidence
are present.  Release promotion additionally requires the standard numeric
provenance and input-manifest files.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path


SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit(task_dir: Path) -> dict:
    data = task_dir / "data"
    rules = load(data / "rules.json")
    sources = load(data / "sources.json")
    required_fields = list(rules.get("required_freeze_fields", ()))
    rows = []
    for source in sources:
        missing = [name for name in required_fields if not source.get(name)]
        blockers = []
        rights_status = source.get("rights_status")
        if rights_status not in rules.get("allowed_rights_statuses", []):
            blockers.append("rights_review_required")
        sha256 = source.get("sha256")
        if not isinstance(sha256, str) or not SHA256_RE.fullmatch(sha256):
            blockers.append("sha256_missing_or_invalid")
        if rules.get("verifier_rebound_required") and source.get("verifier_rebound") is not True:
            blockers.append("verifier_rebind_required")
        if missing:
            blockers.append("required_freeze_fields_missing")
        if blockers and blockers[0] == "rights_review_required":
            release_status = "BLOCKED_RIGHTS"
        elif blockers and blockers[0] == "sha256_missing_or_invalid":
            release_status = "BLOCKED_HASH"
        elif blockers:
            release_status = "STAGING_REBIND_REQUIRED"
        else:
            release_status = "READY_FOR_REVIEW"
        rows.append(
            {
                "source_id": source.get("source_id"),
                "task_id": source.get("task_id"),
                "release_status": release_status,
                "blockers": blockers,
                "required_fields_missing": missing,
                "rights_status": rights_status,
                "sha256_frozen": bool(isinstance(sha256, str) and SHA256_RE.fullmatch(sha256)),
                "verifier_rebound": source.get("verifier_rebound") is True,
                "file_inventory_count": len(source.get("file_inventory", [])) if isinstance(source.get("file_inventory"), list) else 0,
                "claim_boundary": source.get("claim_boundary"),
            }
        )

    required_release_artifacts = {
        relative: {"present": (task_dir / relative).is_file()}
        for relative in ("data/numeric_provenance.tsv", "data/release_input_manifest.json")
    }
    source_blocked = [row["source_id"] for row in rows if row["release_status"] != "READY_FOR_REVIEW"]
    artifact_blocked = [name for name, record in required_release_artifacts.items() if not record["present"]]
    release_ready = not source_blocked and not artifact_blocked
    return {
        "schema_version": "real_source_gate_audit.v1",
        "task_id": task_dir.name,
        "rules_version": rules.get("rules_version"),
        "source_count": len(rows),
        "rows": rows,
        "blocked_sources": source_blocked,
        "required_release_artifacts": required_release_artifacts,
        "missing_release_artifacts": artifact_blocked,
        "release_status": "READY_FOR_REVIEW" if release_ready else "STAGING_BLOCKED",
        "claim_boundary": rules.get("claim_boundary", "source_audit_only_not_scientific_claim"),
        "input_sha256": {
            "data/rules.json": digest(data / "rules.json"),
            "data/sources.json": digest(data / "sources.json"),
        },
        "next_actions": rules.get("required_next_actions", []),
        "network_used": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--strict-release", action="store_true")
    args = parser.parse_args()
    report = audit(args.task.resolve())
    text = json.dumps(report, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0 if (report["release_status"] == "READY_FOR_REVIEW" or not args.strict_release) else 1


if __name__ == "__main__":
    raise SystemExit(main())
