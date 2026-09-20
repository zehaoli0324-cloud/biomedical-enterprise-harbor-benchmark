from __future__ import annotations

from pathlib import Path

from .checks import load_context, run_deterministic_checks
from .judge import LLMJudge
from .models import Finding, ReviewReport, ReviewStatus, Severity


class ReviewPipeline:
    def __init__(self, judge: LLMJudge | None = None) -> None:
        self.judge = judge

    def review(self, task_path: str | Path) -> ReviewReport:
        root = Path(task_path).expanduser().resolve()
        context = load_context(root)
        gates = list(run_deterministic_checks(root))
        findings = [finding for gate in gates for finding in gate.findings]
        if self.judge is not None:
            llm_findings = self.judge.review(context)
            findings.extend(llm_findings)
            if llm_findings:
                gates.append(type(gates[0])("llm-review", True, tuple(llm_findings)))

        if any(f.severity == Severity.BLOCKER for f in findings):
            status = ReviewStatus.FAIL
        elif any(f.severity == Severity.WARNING for f in findings):
            status = ReviewStatus.NEEDS_REVIEW
        else:
            status = ReviewStatus.PASS
        return ReviewReport(str(root), status, tuple(gates), tuple(findings), {"judge": type(self.judge).__name__ if self.judge else None})

