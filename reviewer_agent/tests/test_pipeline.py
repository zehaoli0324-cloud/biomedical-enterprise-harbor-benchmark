from pathlib import Path

from benchmark_review_agent.models import ReviewStatus
from benchmark_review_agent.pipeline import ReviewPipeline


def write_task(root: Path, *, include_verifier: bool = True) -> Path:
    root.mkdir()
    (root / "task.toml").write_text(
        '[metadata]\nname = "demo"\ndescription = "A demo task"\nauthors = ["reviewer"]\n',
        encoding="utf-8",
    )
    (root / "README.md").write_text(
        "# Demo\n\n## Task\nDo the task.\n\n## Solution\nUse the oracle.\n\n## Verification\nThe expected answer is checked.\n",
        encoding="utf-8",
    )
    for directory in ("environment", "solution", "verifier"):
        (root / directory).mkdir()
    if include_verifier:
        (root / "verifier" / "test.sh").write_text("#!/bin/sh\n", encoding="utf-8")
    return root


def test_valid_task_passes(tmp_path: Path) -> None:
    report = ReviewPipeline().review(write_task(tmp_path / "task"))
    assert report.status == ReviewStatus.PASS


def test_missing_verifier_is_blocking(tmp_path: Path) -> None:
    report = ReviewPipeline().review(write_task(tmp_path / "task", include_verifier=False))
    assert report.status == ReviewStatus.FAIL
    assert any(f.check == "trial-artifact" for f in report.findings)

