#!/usr/bin/env python3
"""Audit benchmark packages against the repository task-standardization rules.

The repository contains both the native ``task.yaml`` package format and a
small set of Terminal-Bench-compatible ``task.toml`` packages.  This checker
keeps those formats intact while applying the shared static gates from the
authoring standard.  It deliberately does not infer scientific validity,
model difficulty, or release approval from metadata.
"""

from __future__ import annotations

import argparse
import ast
import json
import re
import subprocess
import tomllib
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
BENCHMARKS = ROOT / "benchmarks"
HIDDEN_TOKENS = ("verifier.py", "tests/", "verifier_only/")
PRIVATE_BASE_TOKENS = ("local", "fable-base", "harbor-base")
OUTPUT_RE = re.compile(r"(?:^|[,{}\s])path:\s*([^,}\s]+)")
SUBMISSION_PATH_RE = re.compile(
    r"submission\s*(?:/|\.joinpath\(\s*)\s*['\"]([^'\"]+)['\"]"
)
REQUIRED_LOOP_RE = re.compile(
    r"(?:for\s+name\s+in|required\s*=)\s*[\(\[]([^\)\]]+)[\)\]]",
    re.DOTALL,
)


def _strip(value: str) -> str:
    return value.strip().strip("\"'").rstrip("/")


def yaml_outputs(text: str) -> set[str]:
    outputs: set[str] = set()
    active = False
    for raw in text.splitlines():
        line = raw.strip()
        if line == "required_outputs:":
            active = True
            continue
        if active and line and not raw.startswith((" ", "\t")):
            break
        if active:
            match = OUTPUT_RE.search(line)
            if match:
                outputs.add(Path(_strip(match.group(1))).name)
    return outputs


def declared_outputs(package: Path) -> tuple[str, str]:
    task_yaml = package / "task.yaml"
    if task_yaml.is_file():
        return "task.yaml", ",".join(sorted(yaml_outputs(task_yaml.read_text(encoding="utf-8"))))
    task_toml = package / "task.toml"
    if task_toml.is_file():
        try:
            payload = tomllib.loads(task_toml.read_text(encoding="utf-8"))
            values = payload.get("artifacts", [])
            return "task.toml", ",".join(sorted(Path(str(value)).name for value in values))
        except (OSError, tomllib.TOMLDecodeError):
            return "task.toml", ""
    return "missing", ""


def verifier_output_names(source: str) -> set[str]:
    names = {Path(_strip(value)).name for value in SUBMISSION_PATH_RE.findall(source)}
    for match in REQUIRED_LOOP_RE.finditer(source):
        block = match.group(0)
        tail = source[match.start() : match.end() + 260]
        if "submission" not in tail or ("is_file" not in tail and "missing artifact" not in tail):
            continue
        names.update(
            Path(_strip(value)).name
            for value in re.findall(r"['\"]([^'\"]+\.(?:json|tsv|csv|md|yaml|py|jsonl)|feedback_history)['\"]", block)
        )
    return {name for name in names if name and name not in {"name"}}


def syntax_errors(package: Path) -> list[str]:
    errors: list[str] = []
    for path in package.rglob("*.py"):
        if "__pycache__" in path.parts:
            continue
        try:
            ast.parse(path.read_text(encoding="utf-8"))
        except (OSError, SyntaxError) as exc:
            errors.append(f"{path.relative_to(ROOT)}: {exc}")
    for path in package.rglob("*.json"):
        if "jobs" in path.parts:
            continue
        try:
            json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"{path.relative_to(ROOT)}: {exc}")
    for path in (package / "task.toml",):
        if path.is_file():
            try:
                tomllib.loads(path.read_text(encoding="utf-8"))
            except (OSError, tomllib.TOMLDecodeError) as exc:
                errors.append(f"{path.relative_to(ROOT)}: {exc}")
    return errors


def audit_package(package: Path) -> dict[str, Any]:
    task_id = package.name
    task_yaml = package / "task.yaml"
    task_toml = package / "task.toml"
    instruction = package / "instruction.md"
    verifier = package / "verifier.py"
    test_verifier = package / "tests" / "verifier.py"
    checks: dict[str, Any] = {}

    checks["id_matches_directory"] = (
        task_id in task_yaml.read_text(encoding="utf-8", errors="replace")[:200]
        if task_yaml.is_file()
        else task_id in task_toml.read_text(encoding="utf-8", errors="replace")
        if task_toml.is_file()
        else False
    )
    schema, output_text = declared_outputs(package)
    declared = {item for item in output_text.split(",") if item}
    checks["schema"] = schema
    checks["required_outputs_declared"] = bool(declared)
    checks["data_nonempty"] = (package / "data").is_dir() and any((package / "data").iterdir())
    checks["instruction_present"] = instruction.is_file() and instruction.stat().st_size > 0
    checks["verifier_present"] = verifier.is_file() or test_verifier.is_file()
    checks["reference_present"] = (package / "verifier_only" / "reference.json").is_file() or (
        package / "verifier_only" / "reference_labels.json"
    ).is_file()
    instruction_text = instruction.read_text(encoding="utf-8", errors="replace") if instruction.is_file() else ""
    checks["hidden_boundary_not_leaked"] = not any(token in instruction_text for token in HIDDEN_TOKENS)
    checks["declared_outputs_in_instruction"] = bool(declared) and all(
        name in instruction_text for name in declared if name != "feedback_history"
    )

    env_instruction = package / "environment" / "instruction.md"
    checks["instruction_copy"] = (
        "absent" if not env_instruction.exists() else "match" if env_instruction.read_bytes() == instruction.read_bytes() else "drift"
    )
    checks["verifier_copy"] = (
        "absent" if not test_verifier.exists() else "match" if test_verifier.read_bytes() == verifier.read_bytes() else "drift"
    )

    dockerfile = package / "environment" / "Dockerfile"
    if dockerfile.is_file():
        docker_text = dockerfile.read_text(encoding="utf-8")
        bases = re.findall(r"^FROM\s+([^\s]+)", docker_text, flags=re.MULTILINE)
        checks["docker_base"] = bases
        checks["portable_docker_base"] = bool(bases) and not any(
            any(token in base.lower() for token in PRIVATE_BASE_TOKENS) for base in bases
        )
        checks["docker_hidden_boundary_not_copied"] = not any(
            line.lstrip().upper().startswith(("COPY ", "ADD "))
            and any(token in line.lower() for token in ("verifier", "tests", "reference", "hidden"))
            for line in docker_text.splitlines()
        )
    else:
        checks["docker_base"] = "not_applicable"
        checks["portable_docker_base"] = "not_applicable"
        checks["docker_hidden_boundary_not_copied"] = "not_applicable"

    source_path = test_verifier if test_verifier.is_file() else verifier
    if source_path.is_file():
        verifier_text = source_path.read_text(encoding="utf-8", errors="replace")
        referenced = verifier_output_names(verifier_text)
        checks["verifier_output_literals"] = sorted(referenced)
        checks["verifier_outputs_declared"] = sorted(referenced - declared)
    else:
        checks["verifier_output_literals"] = []
        checks["verifier_outputs_declared"] = []

    checks["syntax_errors"] = syntax_errors(package)
    shell_errors = []
    for shell in (package / "tests" / "test.sh", package / "solution" / "solve.sh"):
        if shell.is_file():
            result = subprocess.run(["sh", "-n", str(shell)], capture_output=True, text=True)
            if result.returncode:
                shell_errors.append(f"{shell.relative_to(ROOT)}: {result.stderr.strip()}")
    checks["shell_syntax_errors"] = shell_errors
    checks["generated_runtime_artifacts"] = sorted(
        str(path.relative_to(package))
        for path in package.rglob("*")
        if path.name in {"__pycache__", ".pytest_cache", ".DS_Store"} or path.suffix == ".pyc"
    )
    return {"task_id": task_id, "checks": checks}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, help="write the JSON audit report")
    args = parser.parse_args()
    packages = [path for path in sorted(BENCHMARKS.iterdir()) if path.is_dir() and path.name != "__pycache__"]
    records = [audit_package(package) for package in packages]
    report = {
        "schema_version": "task_standardization_audit.v1",
        "standard_source": "改题方案与检查标准-v1.0.md",
        "package_count": len(records),
        "packages": records,
    }
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    failures = []
    for record in records:
        checks = record["checks"]
        if (
            checks["syntax_errors"]
            or checks["shell_syntax_errors"]
            or checks["instruction_copy"] == "drift"
            or checks["verifier_copy"] == "drift"
            or checks["docker_hidden_boundary_not_copied"] is False
        ):
            failures.append(record["task_id"])
    print(json.dumps({"packages": len(records), "mechanical_failures": failures}, ensure_ascii=False))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
