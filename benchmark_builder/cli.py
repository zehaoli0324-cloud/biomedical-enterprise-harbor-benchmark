from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .candidates import (
    CandidateError,
    build_candidate_iteration_plan,
    candidate_protocol,
    load_candidate_set,
    select_candidates,
)
from .compiler import compile_spec
from .config import load_spec
from .evaluation import EvaluationError, build_iteration_plan, evaluate_submission, evaluation_protocol
from .scoring import score_spec
from .provenance import validate_registry


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Compile scientific scenarios into benchmark contracts")
    subparsers = parser.add_subparsers(dest="command", required=True)

    for name in ("validate", "score"):
        command = subparsers.add_parser(name)
        command.add_argument("config")
        command.add_argument("--catalog")

    compile_command = subparsers.add_parser("compile")
    compile_command.add_argument("config")
    compile_command.add_argument("--out", required=True)
    compile_command.add_argument("--catalog")

    protocol_command = subparsers.add_parser("protocol")
    protocol_command.add_argument("config")
    protocol_command.add_argument("--out", required=True)
    protocol_command.add_argument("--catalog")

    evaluate_command = subparsers.add_parser("evaluate")
    evaluate_command.add_argument("config")
    evaluate_command.add_argument("--judgments", required=True)
    evaluate_command.add_argument("--out", required=True)
    evaluate_command.add_argument("--catalog")

    iterate_command = subparsers.add_parser("iterate")
    iterate_command.add_argument("config")
    iterate_command.add_argument("--evaluation", required=True)
    iterate_command.add_argument("--previous-evaluation")
    iterate_command.add_argument("--out", required=True)
    iterate_command.add_argument("--catalog")

    validate_candidates = subparsers.add_parser("validate-candidates")
    validate_candidates.add_argument("manifest")
    validate_candidates.add_argument("--catalog")

    candidate_protocol_command = subparsers.add_parser("candidate-protocol")
    candidate_protocol_command.add_argument("manifest")
    candidate_protocol_command.add_argument("--out", required=True)
    candidate_protocol_command.add_argument("--catalog")

    select_command = subparsers.add_parser("select-candidates")
    select_command.add_argument("manifest")
    select_command.add_argument("--judgments", required=True)
    select_command.add_argument("--out", required=True)
    select_command.add_argument("--min-agreement", type=float, default=0.75)
    select_command.add_argument("--catalog")

    iterate_candidates = subparsers.add_parser("iterate-candidates")
    iterate_candidates.add_argument("manifest")
    iterate_candidates.add_argument("--selection", required=True)
    iterate_candidates.add_argument("--out", required=True)
    iterate_candidates.add_argument("--catalog")
    evidence_check = subparsers.add_parser("validate-evidence", help="validate public data and literature registry")
    evidence_check.add_argument("registry")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "validate-evidence":
        result = validate_registry(args.registry)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result["status"] == "PASS" else 1
    if args.command in {
        "validate-candidates",
        "candidate-protocol",
        "select-candidates",
        "iterate-candidates",
    }:
        try:
            candidate_set = load_candidate_set(args.manifest, args.catalog)
            if args.command == "validate-candidates":
                print(
                    f"valid: {candidate_set.workflow_id} "
                    f"({len(candidate_set.candidates)} candidates, digest={candidate_set.digest})"
                )
                return 0
            output = Path(args.out)
            output.parent.mkdir(parents=True, exist_ok=True)
            if args.command == "candidate-protocol":
                result = candidate_protocol(candidate_set)
                label = "candidate protocol"
            elif args.command == "select-candidates":
                if not 0 <= args.min_agreement <= 1:
                    raise CandidateError("--min-agreement must be between 0 and 1")
                result = select_candidates(candidate_set, args.judgments, args.min_agreement)
                label = f"candidate selection ({result['status']})"
            else:
                with Path(args.selection).open(encoding="utf-8") as handle:
                    selection = json.load(handle)
                result = build_candidate_iteration_plan(candidate_set, selection)
                label = f"candidate iteration ({result['status']})"
            output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            print(f"{label}: {output}")
            return 0
        except (OSError, ValueError, TypeError, json.JSONDecodeError, CandidateError) as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2
    try:
        spec = load_spec(args.config, args.catalog)
    except (OSError, ValueError, TypeError, EvaluationError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    report = score_spec(spec)
    try:
        if args.command == "validate":
            print(f"valid: {spec.task_id} ({len(spec.modules)} module categories)")
        elif args.command == "score":
            print(json.dumps(report.to_dict(), ensure_ascii=False, indent=2))
        elif args.command == "compile":
            path = compile_spec(spec, report, args.out)
            print(f"compiled: {path}")
        elif args.command == "protocol":
            output = Path(args.out)
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(json.dumps(evaluation_protocol(spec), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            print(f"protocol: {output}")
        elif args.command == "evaluate":
            output = Path(args.out)
            output.parent.mkdir(parents=True, exist_ok=True)
            result = evaluate_submission(spec, args.judgments)
            output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            print(f"evaluation: {output} ({result['status']})")
        else:
            evaluation_path = Path(args.evaluation)
            with evaluation_path.open(encoding="utf-8") as handle:
                evaluation = json.load(handle)
            previous = None
            if args.previous_evaluation:
                with Path(args.previous_evaluation).open(encoding="utf-8") as handle:
                    previous = json.load(handle)
            plan = build_iteration_plan(spec, evaluation, previous)
            output = Path(args.out)
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(json.dumps(plan, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            print(f"iteration: {output} ({plan['status']})")
    except (OSError, ValueError, TypeError, json.JSONDecodeError, EvaluationError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
