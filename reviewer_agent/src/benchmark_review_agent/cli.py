from __future__ import annotations

import argparse
import json
import sys

from .judge import HeuristicJudge
from .pipeline import ReviewPipeline


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Review a benchmark task and emit an auditable JSON report")
    subparsers = parser.add_subparsers(dest="command", required=True)
    review = subparsers.add_parser("review", help="run deterministic checks and the offline heuristic judge")
    review.add_argument("task", help="path to a benchmark task directory")
    review.add_argument("--output", help="write JSON report to this path")
    review.add_argument("--no-judge", action="store_true", help="skip the offline heuristic judge")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "review":
        report = ReviewPipeline(None if args.no_judge else HeuristicJudge()).review(args.task)
        payload = json.dumps(report.to_dict(), ensure_ascii=False, indent=2) + "\n"
        if args.output:
            with open(args.output, "w", encoding="utf-8") as handle:
                handle.write(payload)
        else:
            sys.stdout.write(payload)
        return 0 if report.status.value != "fail" else 1
    return 2


if __name__ == "__main__":
    raise SystemExit(main())

