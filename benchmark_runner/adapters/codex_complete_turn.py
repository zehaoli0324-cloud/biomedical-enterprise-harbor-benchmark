#!/usr/bin/env python3
"""Wait for the Codex turn to exit; artifact existence is not completion."""
from __future__ import annotations

import argparse
import json
import os
import shutil
import signal
import subprocess
import sys
from pathlib import Path

from codex_gpt55 import SUPPORTED_MODELS, build_command


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True, choices=sorted(SUPPORTED_MODELS))
    parser.add_argument("--timeout", type=int, default=840)
    args = parser.parse_args()
    workspace = Path(os.environ["BENCHMARK_WORKSPACE"]).resolve()
    event_path = Path(os.environ["BENCHMARK_EVENT_LOG"])
    codex = shutil.which("codex")
    if not codex:
        raise SystemExit("codex executable missing")
    prompt = ("Complete this benchmark inside the current workspace only. Read instruction.md and data/. "
              "Write all required files under outputs/. Do not inspect parent directories or use network access.\n\n"
              + Path(os.environ["BENCHMARK_PROMPT"]).read_text())
    with event_path.open("w") as events, (workspace / "adapter_stderr.log").open("w+") as errors:
        events.write(json.dumps({"type": "model_config", "model": args.model, "completion_policy": "process_exit_only"}) + "\n")
        events.flush()
        process = subprocess.Popen(build_command(codex, workspace, workspace / "agent_final.md", args.model),
                                   stdin=subprocess.PIPE, stdout=events, stderr=errors, text=True,
                                   cwd=workspace, start_new_session=True)
        timed_out = False
        try:
            process.communicate(prompt, timeout=args.timeout)
        except subprocess.TimeoutExpired:
            timed_out = True
            os.killpg(process.pid, signal.SIGTERM)
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()
        errors.seek(0)
        sys.stderr.write(errors.read())
    return 124 if timed_out else process.returncode


if __name__ == "__main__":
    raise SystemExit(main())
