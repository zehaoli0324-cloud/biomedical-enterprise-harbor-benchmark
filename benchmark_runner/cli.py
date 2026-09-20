from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .files import RunnerError
from .runner import prepare_trial, run_trial


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Prepare and archive provider-neutral benchmark trials")
    sub = parser.add_subparsers(dest="command", required=True)

    prepare = sub.add_parser("prepare", help="create an agent-visible trial workspace")
    prepare.add_argument("task")
    prepare.add_argument("--out", required=True)
    prepare.add_argument("--trial-id")

    run = sub.add_parser("run", help="run an agent command and then invoke the hidden verifier")
    run.add_argument("task")
    run.add_argument("--out", required=True)
    run.add_argument("--command", required=True, help="agent adapter command; it receives BENCHMARK_* environment variables")
    run.add_argument("--trial-id")
    run.add_argument("--timeout", type=int, default=120)
    run.add_argument("--backend", choices=("process", "docker"), default="process")
    run.add_argument("--docker-image", help="container image for --backend docker")
    run.add_argument("--docker-network", choices=("none", "bridge"), default="none")
    run.add_argument("--docker-cpus", type=float, default=1.0)
    run.add_argument("--docker-memory", default="512m")
    run.add_argument("--docker-pids-limit", type=int, default=256)
    run.add_argument("--docker-user", default="1000:1000")
    run.add_argument(
        "--pass-env",
        action="append",
        default=[],
        metavar="NAME",
        help="explicitly pass one existing host environment variable to the adapter",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "prepare":
            trial = prepare_trial(args.task, args.out, args.trial_id)
            print(json.dumps({"status": "prepared", "trial_dir": str(trial.trial_dir), "workspace": str(trial.workspace)}, ensure_ascii=False, indent=2))
            return 0
        result = run_trial(
            args.task,
            args.out,
            args.command,
            args.trial_id,
            args.timeout,
            tuple(args.pass_env),
            args.backend,
            args.docker_image,
            args.docker_network,
            args.docker_cpus,
            args.docker_memory,
            args.docker_pids_limit,
            args.docker_user,
        )
        print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
        return 0 if result.status == "pass" else 1
    except (OSError, ValueError, RunnerError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
