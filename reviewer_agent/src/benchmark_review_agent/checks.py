from __future__ import annotations

import re
import tomllib
from pathlib import Path
from typing import Iterable

from .models import Finding, GateResult, Severity, TaskContext


REQUIRED_FILES = ("task.toml", "README.md")
RECOMMENDED_DIRS = ("environment", "solution", "verifier")


def load_context(root: Path) -> TaskContext:
    metadata: dict = {}
    task_file = root / "task.toml"
    if task_file.is_file():
        try:
            with task_file.open("rb") as handle:
                metadata = tomllib.load(handle)
        except (tomllib.TOMLDecodeError, OSError):
            metadata = {}
    files = tuple(sorted(str(path.relative_to(root)) for path in root.rglob("*") if path.is_file()))
    return TaskContext(root=root, metadata=metadata, files=files)


def run_structure_checks(context: TaskContext) -> GateResult:
    findings: list[Finding] = []
    for filename in REQUIRED_FILES:
        if not (context.root / filename).is_file():
            findings.append(Finding(
                check="required-file",
                message=f"Required file is missing: {filename}",
                severity=Severity.BLOCKER,
                path=filename,
            ))

    for dirname in RECOMMENDED_DIRS:
        if not (context.root / dirname).is_dir():
            findings.append(Finding(
                check="recommended-directory",
                message=f"Recommended directory is missing: {dirname}",
                severity=Severity.WARNING,
                path=dirname,
            ))

    return GateResult("structure", not any(f.severity == Severity.BLOCKER for f in findings), tuple(findings))


def run_metadata_checks(context: TaskContext) -> GateResult:
    findings: list[Finding] = []
    metadata = context.metadata.get("metadata", context.metadata)
    if not metadata:
        findings.append(Finding(
            check="metadata-parse",
            message="task.toml is missing or could not be parsed",
            severity=Severity.BLOCKER,
            path="task.toml",
        ))
        return GateResult("metadata", False, tuple(findings))

    for key in ("name", "description"):
        value = metadata.get(key)
        if not isinstance(value, str) or not value.strip():
            findings.append(Finding(
                check="metadata-field",
                message=f"Metadata field '{key}' must be a non-empty string",
                severity=Severity.BLOCKER,
                path="task.toml",
            ))

    authors = metadata.get("authors")
    if authors is not None and not isinstance(authors, list):
        findings.append(Finding(
            check="metadata-type",
            message="Metadata field 'authors' should be a list",
            severity=Severity.WARNING,
            path="task.toml",
        ))
    return GateResult("metadata", not any(f.severity == Severity.BLOCKER for f in findings), tuple(findings))


def run_readme_checks(context: TaskContext) -> GateResult:
    findings: list[Finding] = []
    readme = context.root / "README.md"
    if not readme.is_file():
        return GateResult("readme", False, (Finding("readme", "README.md is missing", Severity.BLOCKER, "README.md"),))
    text = readme.read_text(encoding="utf-8", errors="replace")
    required_sections = ("## Task", "## Solution", "## Verification")
    for section in required_sections:
        if not re.search(rf"^#{{1,3}}\s*{re.escape(section.lstrip('# '))}\s*$", text, re.MULTILINE | re.IGNORECASE):
            findings.append(Finding(
                check="readme-section",
                message=f"README.md should contain a '{section}' section",
                severity=Severity.WARNING,
                path="README.md",
            ))
    return GateResult("readme", True, tuple(findings))


def run_trial_checks(context: TaskContext) -> GateResult:
    """Check for the evidence produced by an oracle/verifier run.

    This intentionally checks evidence shape rather than interpreting model output.
    A later adapter can map Harbor CTRF/result files into this gate.
    """
    findings: list[Finding] = []
    verifier_dir = context.root / "verifier"
    if not verifier_dir.is_dir():
        findings.append(Finding("trial-artifact", "verifier directory is missing", Severity.BLOCKER, "verifier"))
        return GateResult("trial-evidence", False, tuple(findings))
    if verifier_dir.is_dir() and not any(verifier_dir.iterdir()):
        findings.append(Finding("trial-artifact", "verifier directory is empty", Severity.BLOCKER, "verifier"))
    if (context.root / "verifier").is_dir() and not any(path.is_file() for path in (context.root / "verifier").rglob("*")):
        findings.append(Finding("trial-artifact", "no verifier artifact was found", Severity.BLOCKER, "verifier"))
    return GateResult("trial-evidence", not any(f.severity == Severity.BLOCKER for f in findings), tuple(findings))


def run_deterministic_checks(root: Path) -> tuple[GateResult, ...]:
    context = load_context(root)
    return (
        run_structure_checks(context),
        run_metadata_checks(context),
        run_readme_checks(context),
        run_trial_checks(context),
    )
