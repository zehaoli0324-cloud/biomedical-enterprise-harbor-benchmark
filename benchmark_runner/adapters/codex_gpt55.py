#!/usr/bin/env python3
"""Run the local Codex CLI with the explicitly requested GPT-5.5 model."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path


MODEL = "gpt-5.5"


def build_command(codex: str, workspace: Path, final_message: Path) -> list[str]:
    return [
        codex,
        "--ask-for-approval",
        "never",
        "exec",
        "--model",
        MODEL,
        "--cd",
        str(workspace),
        "--sandbox",
        "workspace-write",
        "--skip-git-repo-check",
        "--ephemeral",
        "--json",
        "--output-last-message",
        str(final_message),
        "-",
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description="GPT-5.5 Codex CLI benchmark adapter")
    parser.add_argument("--model", default=MODEL)
    args = parser.parse_args()
    if args.model != MODEL:
        print(f"this adapter is pinned to {MODEL}; got {args.model}", file=sys.stderr)
        return 2
    workspace = Path(os.environ["BENCHMARK_WORKSPACE"]).resolve()
    prompt_path = Path(os.environ["BENCHMARK_PROMPT"]).resolve()
    event_path = Path(os.environ["BENCHMARK_EVENT_LOG"]).resolve()
    final_message = workspace / "agent_final.md"
    codex = shutil.which("codex")
    if not codex:
        print("codex executable was not found on PATH", file=sys.stderr)
        return 2
    prompt = prompt_path.read_text(encoding="utf-8")
    prompt = (
        "You are running a benchmark trial with GPT-5.5. Work only inside the current "
        "workspace. Read instruction.md and the data files, then complete the task. "
        "Write every required artifact under outputs/. Do not use the network, do not "
        "inspect parent directories, and do not merely describe what should be done.\n\n"
        + prompt
    )
    command = build_command(codex, workspace, final_message)
    event_path.parent.mkdir(parents=True, exist_ok=True)
    with event_path.open("w", encoding="utf-8") as events:
        events.write(json.dumps({"type": "model_config", "provider": "codex-cli", "model": MODEL}) + "\n")
        events.flush()
        result = subprocess.run(
            command,
            input=prompt,
            text=True,
            stdout=events,
            stderr=subprocess.PIPE,
            cwd=workspace,
            check=False,
        )
    if result.stderr:
        print(result.stderr, file=sys.stderr, end="")
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
