from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Any


class Severity(StrEnum):
    BLOCKER = "blocker"
    WARNING = "warning"
    INFO = "info"


class ReviewStatus(StrEnum):
    PASS = "pass"
    NEEDS_REVIEW = "needs_review"
    FAIL = "fail"


@dataclass(frozen=True)
class Finding:
    check: str
    message: str
    severity: Severity = Severity.WARNING
    path: str | None = None
    evidence: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class GateResult:
    name: str
    passed: bool
    findings: tuple[Finding, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "passed": self.passed,
            "findings": [finding.to_dict() for finding in self.findings],
        }


@dataclass(frozen=True)
class ReviewReport:
    task_path: str
    status: ReviewStatus
    gates: tuple[GateResult, ...]
    findings: tuple[Finding, ...]
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_path": self.task_path,
            "status": self.status,
            "gates": [gate.to_dict() for gate in self.gates],
            "findings": [finding.to_dict() for finding in self.findings],
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class TaskContext:
    root: Path
    metadata: dict[str, Any]
    files: tuple[str, ...]

