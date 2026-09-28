#!/usr/bin/env python3
"""Build a fail-closed, hash-bound lifecycle report for one task package.

This checker deliberately does not infer scientific validity from file presence.
It reports independent pipeline/evidence/review/release axes and keeps release
blocked until explicit dynamic and human gates are recorded.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import tomllib
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "config/task_pipeline_schema.v1.json"


def load_schema() -> dict[str, Any]:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(path: Path) -> dict[str, Any] | None:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return None
    return value if isinstance(value, dict) else None


def task_identity(package: Path) -> dict[str, Any]:
    yaml_path = package / "task.yaml"
    toml_path = package / "task.toml"
    identities: list[dict[str, Any]] = []
    if yaml_path.is_file():
        text = yaml_path.read_text(encoding="utf-8", errors="replace")
        task_id = _yaml_scalar(text, "id")
        version = _yaml_scalar(text, "version")
        identities.append({"format": "yaml", "id": task_id, "version": version})
    if toml_path.is_file():
        try:
            data = tomllib.loads(toml_path.read_text(encoding="utf-8"))
            task = data.get("task", data)
            identities.append({"format": "toml", "id": task.get("name") or task.get("id"), "version": task.get("version")})
        except (OSError, tomllib.TOMLDecodeError):
            identities.append({"format": "toml", "id": None, "version": None})
    ids = {item.get("id") for item in identities if item.get("id")}
    versions = {item.get("version") for item in identities if item.get("version")}
    return {
        "directory_id": package.name,
        "formats": identities,
        # Sets are used only for consistency checks; choose a stable value for
        # reports so repeated audits do not change with hash iteration order.
        "task_id": sorted(ids)[0] if ids else package.name,
        "task_version": sorted(versions)[0] if versions else None,
        "identity_consistent": bool(identities) and len(ids) <= 1 and len(versions) <= 1 and package.name in ids,
    }


def _yaml_scalar(text: str, key: str) -> str | None:
    match = re.search(rf"^\s*{re.escape(key)}:\s*([^#\n]+)", text, re.MULTILINE)
    if not match:
        return None
    return match.group(1).strip().strip("'\"")


def files_for_hash(package: Path) -> dict[str, str]:
    files: dict[str, str] = {}
    for path in sorted(package.rglob("*")):
        if not path.is_file() or ".git" in path.parts or "__pycache__" in path.parts:
            continue
        relative = path.relative_to(package).as_posix()
        files[relative] = sha256(path)
    return files


def _check(checks: list[dict[str, Any]], name: str, passed: bool, detail: str) -> None:
    checks.append({"check": name, "status": "PASS" if passed else "BLOCKER", "detail": detail})


def evaluate(package: Path) -> dict[str, Any]:
    package = package.resolve()
    schema = load_schema()
    checks: list[dict[str, Any]] = []
    blockers: list[str] = []
    release_blockers: list[str] = []
    identity = task_identity(package)

    _check(checks, "task_identity", identity["identity_consistent"], json.dumps(identity, ensure_ascii=False))
    if not identity["identity_consistent"]:
        blockers.append("task_identity")

    required = ["instruction.md", "verifier_only/reference.json", "quality/sop_card.json"]
    required += ["task.yaml"] if (package / "task.yaml").exists() else ["task.toml"]
    has_verifier = (package / "verifier.py").is_file() or (package / "tests/verifier.py").is_file()
    for relative in required:
        present = (package / relative).is_file() and (package / relative).stat().st_size > 0
        _check(checks, f"file:{relative}", present, "present" if present else "missing_or_empty")
        if not present:
            blockers.append(f"file:{relative}")
    _check(checks, "file:verifier", has_verifier, "root_or_tests_verifier")
    if not has_verifier:
        blockers.append("file:verifier")
    data_dir = package / "data"
    data_ok = data_dir.is_dir() and any(path.is_file() for path in data_dir.iterdir())
    _check(checks, "data_nonempty", data_ok, str(data_dir))
    if not data_ok:
        blockers.append("data_nonempty")

    root_verifier = package / "verifier.py"
    tests_verifier = package / "tests/verifier.py"
    if root_verifier.is_file() and tests_verifier.is_file():
        synced = root_verifier.read_bytes() == tests_verifier.read_bytes()
        _check(checks, "verifier_copy_sync", synced, "byte_equal" if synced else "drift")
        if not synced:
            blockers.append("verifier_copy_sync")

    instruction_copy = package / "environment/instruction.md"
    if instruction_copy.exists():
        synced = instruction_copy.read_bytes() == (package / "instruction.md").read_bytes()
        _check(checks, "instruction_copy_sync", synced, "byte_equal" if synced else "drift")
        if not synced:
            blockers.append("instruction_copy_sync")

    environment_data = package / "environment/data"
    if environment_data.is_dir():
        for source in sorted(path for path in data_dir.iterdir() if path.is_file()):
            target = environment_data / source.name
            synced = target.is_file() and target.read_bytes() == source.read_bytes()
            _check(checks, f"environment_data:{source.name}", synced, "byte_equal" if synced else "missing_or_drift")
            if not synced:
                blockers.append(f"environment_data:{source.name}")

    contract_missing = [path for path in schema["required_contract_files"] if not (package / path).is_file()]
    _check(checks, "contract_files", not contract_missing, ",".join(contract_missing) or "complete")
    if contract_missing:
        release_blockers.extend(f"missing:{path}" for path in contract_missing)

    quality = read_json(package / "quality/sop_card.json") or {}
    source_status = quality.get("source_status") or (read_json(package / "evidence_quality.json") or {}).get("source_status") or "UNKNOWN"
    scientific_review = read_json(package / "quality/scientific_review.json")
    review_status = "APPROVED" if scientific_review and scientific_review.get("status") in {"APPROVED", "PASS"} else "NOT_RUN"
    evidence_missing = [path for path in schema["release_evidence_files"] if not (package / path).is_file()]
    for path in evidence_missing:
        release_blockers.append(f"missing:{path}")
    if source_status in {"PLACEHOLDER_OR_MISSING", "UNREGISTERED", "UNKNOWN"}:
        release_blockers.append(f"source_status:{source_status}")
    if review_status != "APPROVED":
        release_blockers.append("scientific_review")

    dynamic = quality.get("dynamic_gates") or quality.get("replay") or {}
    dynamic_ready = isinstance(dynamic, dict) and all(dynamic.get(gate) in {"PASS", "PASS_NEGATIVE", True} for gate in ("oracle", "nop"))
    _check(checks, "dynamic_oracle_nop", dynamic_ready, "explicit_pass_records_required")
    if not dynamic_ready:
        release_blockers.append("dynamic_oracle_nop")

    pipeline_status = "CONTRACT_ONLY" if blockers else "DEVELOPMENT_BUILT"
    evidence_status = "STATIC_REVIEW_PASS" if not blockers else "PENDING"
    release_status = "READY_FOR_HARBOR" if not blockers and not release_blockers else "BLOCKED"
    manifest = {
        "schema_version": "task_build_manifest.v1",
        "task_id": identity["task_id"],
        "task_version": identity["task_version"],
        "source_commit": _git_commit(package),
        "data_fingerprint": _fingerprint(files_for_hash(package), prefix="data/"),
        "contract_fingerprint": _fingerprint(files_for_hash(package), prefix="contract"),
        "files": files_for_hash(package),
    }
    return {
        "schema_version": "task_pipeline_report.v1",
        "task_id": identity["task_id"],
        "package": str(package),
        "pipeline_status": pipeline_status,
        "evidence_status": evidence_status,
        "review_status": review_status,
        "release_status": release_status,
        "source_status": source_status,
        "blockers": sorted(set(blockers)),
        "release_blockers": sorted(set(release_blockers + blockers)),
        "release_permitted": release_status == "READY_FOR_HARBOR",
        "checks": checks,
        "build_manifest": manifest,
    }


def _fingerprint(files: dict[str, str], prefix: str) -> str:
    selected = [f"{path}:{digest}" for path, digest in files.items() if path.startswith(prefix)]
    return hashlib.sha256("\n".join(selected).encode()).hexdigest()


def _git_commit(package: Path) -> str | None:
    try:
        import subprocess
        return subprocess.check_output(["git", "-C", str(package), "rev-parse", "HEAD"], text=True, stderr=subprocess.DEVNULL).strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("package", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--manifest-out", type=Path)
    args = parser.parse_args()
    report = evaluate(args.package)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if args.manifest_out:
        args.manifest_out.parent.mkdir(parents=True, exist_ok=True)
        args.manifest_out.write_text(json.dumps(report["build_manifest"], ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: report[key] for key in ("task_id", "pipeline_status", "evidence_status", "review_status", "release_status", "release_permitted")}, ensure_ascii=False))
    return 0 if report["pipeline_status"] != "CONTRACT_ONLY" else 2


if __name__ == "__main__":
    raise SystemExit(main())
