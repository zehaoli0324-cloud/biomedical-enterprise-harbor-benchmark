import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest


@pytest.mark.parametrize("timeout", [False, True])
def test_adapter_waits_for_process_even_when_outputs_exist(tmp_path, monkeypatch, timeout):
    adapters = Path(__file__).resolve().parents[1] / "adapters"
    monkeypatch.syspath_prepend(str(adapters))
    spec = importlib.util.spec_from_file_location("complete_turn_adapter_test", adapters / "codex_complete_turn.py")
    adapter = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(adapter)
    prompt = tmp_path / "prompt.md"
    prompt.write_text("Task prompt")
    outputs = tmp_path / "outputs"
    outputs.mkdir()
    for name in ("plan.json", "decision.json", "route.tsv", "provenance.json", "audit.md"):
        (outputs / name).write_text("unfinished")
    monkeypatch.setenv("BENCHMARK_WORKSPACE", str(tmp_path))
    monkeypatch.setenv("BENCHMARK_PROMPT", str(prompt))
    monkeypatch.setenv("BENCHMARK_EVENT_LOG", str(tmp_path / "events.jsonl"))
    monkeypatch.setattr(sys, "argv", ["adapter", "--model", "gpt-5.6-sol", "--timeout", "1"])
    monkeypatch.setattr(adapter.shutil, "which", lambda _: "/fake/codex")
    calls, signals = [], []

    class Process:
        pid = 999999
        returncode = 7

        def communicate(self, text, timeout):
            calls.append(text)
            if timeout_mode:
                raise subprocess.TimeoutExpired("codex", timeout)

        def wait(self, timeout=None):
            return 7

    timeout_mode = timeout
    monkeypatch.setattr(adapter.subprocess, "Popen", lambda *a, **k: Process())
    monkeypatch.setattr(adapter.os, "killpg", lambda pid, sig: signals.append((pid, sig)))
    assert adapter.main() == (124 if timeout else 7)
    assert len(calls) == 1 and "Task prompt" in calls[0]
    assert bool(signals) == timeout
    event = json.loads((tmp_path / "events.jsonl").read_text())
    assert event["completion_policy"] == "process_exit_only"
