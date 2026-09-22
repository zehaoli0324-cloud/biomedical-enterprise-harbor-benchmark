#!/usr/bin/env python3
"""Summarize observable model turns without inspecting hidden reasoning."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from benchmark_runner.trajectory import summarize_file


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("events", nargs="+", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = {str(path): summarize_file(path) for path in args.events}
    text = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        args.output.write_text(text)
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
