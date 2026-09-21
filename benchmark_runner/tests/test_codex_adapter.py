from pathlib import Path

from benchmark_runner.adapters.codex_gpt55 import MODEL, SUPPORTED_MODELS, build_command


def test_codex_adapter_is_pinned_to_gpt55(tmp_path: Path):
    command = build_command("codex", tmp_path, tmp_path / "agent_final.md")
    assert MODEL == "gpt-5.5"
    assert command[command.index("--model") + 1] == "gpt-5.5"
    assert "--approve-for-me" in command
    assert "--ask-for-approval" not in command
    assert SUPPORTED_MODELS == {"gpt-5.5", "gpt-5.6", "gpt-5.6-sol"}
