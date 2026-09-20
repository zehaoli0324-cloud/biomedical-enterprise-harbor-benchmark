from pathlib import Path

from benchmark_runner.adapters.codex_gpt55 import MODEL, build_command


def test_codex_adapter_is_pinned_to_gpt55(tmp_path: Path):
    command = build_command("codex", tmp_path, tmp_path / "agent_final.md")
    assert MODEL == "gpt-5.5"
    assert command[command.index("--model") + 1] == "gpt-5.5"
    assert command[1:3] == ["--ask-for-approval", "never"]
    assert "--sandbox" in command
    assert command[command.index("--sandbox") + 1] == "workspace-write"
    assert "--ask-for-approval" in command
    assert command[command.index("--ask-for-approval") + 1] == "never"
