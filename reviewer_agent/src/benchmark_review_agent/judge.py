from __future__ import annotations

from typing import Protocol

from .models import Finding, Severity, TaskContext


class LLMJudge(Protocol):
    def review(self, context: TaskContext) -> list[Finding]:
        """Return evidence-backed findings; never mutate deterministic gate results."""


class HeuristicJudge:
    """Offline fallback that surfaces obvious review smells without an API call."""

    def review(self, context: TaskContext) -> list[Finding]:
        findings: list[Finding] = []
        readme = context.root / "README.md"
        if readme.is_file():
            text = readme.read_text(encoding="utf-8", errors="replace").lower()
            if "expected" not in text and "answer" not in text:
                findings.append(Finding(
                    check="review-clarity",
                    message="README does not clearly describe the expected outcome or answer",
                    severity=Severity.WARNING,
                    path="README.md",
                ))
        return findings

