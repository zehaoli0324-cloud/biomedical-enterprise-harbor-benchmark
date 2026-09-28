from pathlib import Path

from benchmark_runner.adapters.codex_gpt55 import MODEL, SUPPORTED_MODELS, build_command
from benchmark_runner.adapters.codex_sequential_feedback import (
    _completion_submission_fingerprint,
    _final_artifacts_ready,
    _required_final_files,
)


def test_codex_adapter_is_pinned_to_gpt55(tmp_path: Path):
    command = build_command("codex", tmp_path, tmp_path / "agent_final.md")
    assert MODEL == "gpt-5.5"
    assert command[command.index("--model") + 1] == "gpt-5.5"
    assert "--approve-for-me" in command
    assert "--ask-for-approval" not in command
    assert SUPPORTED_MODELS == {"gpt-5.5", "gpt-5.6", "gpt-5.6-sol"}


def test_sequential_adapter_uses_public_required_files(tmp_path: Path):
    data = tmp_path / "data"
    outputs = tmp_path / "outputs"
    data.mkdir()
    outputs.mkdir()
    (data / "output_contract.json").write_text(
        '{"required_files":["research_log.json","completion.json"]}\n'
    )
    for name in ("research_log.json", "completion.json"):
        (outputs / name).write_text("{}\n")

    assert _required_final_files(tmp_path) == ("research_log.json", "completion.json")
    before = _completion_submission_fingerprint(tmp_path)
    (outputs / "policy_certificate.json").write_text('{"unexpected":true}\n')
    assert _completion_submission_fingerprint(tmp_path) == before


def test_existing_final_files_must_change_before_turn_is_stopped(tmp_path: Path):
    data = tmp_path / "data"
    outputs = tmp_path / "outputs"
    data.mkdir()
    outputs.mkdir()
    (data / "output_contract.json").write_text(
        '{"required_files":["research_log.json","completion.json"]}\n'
    )
    (outputs / "research_log.json").write_text('{"events":[]}\n')
    (outputs / "completion.json").write_text('{"checks":{}}\n')
    initial = _completion_submission_fingerprint(tmp_path)

    assert not _final_artifacts_ready(tmp_path, initial)
    (outputs / "research_log.json").write_text('{"events":[{"action_id":"stop"}]}\n')
    assert _final_artifacts_ready(tmp_path, initial)
