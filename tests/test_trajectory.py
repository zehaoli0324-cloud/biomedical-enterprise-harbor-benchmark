import json

from benchmark_runner.trajectory import summarize


def event(kind, item=None):
    row = {"type": kind}
    if item is not None:
        row["item"] = item
    return row


def test_parallel_tools_are_one_model_turn():
    rows = [
        event("turn.started"),
        event("item.started", {"type": "command_execution"}),
        event("item.started", {"type": "command_execution"}),
        event("item.completed", {"type": "command_execution"}),
        event("item.completed", {"type": "command_execution"}),
        event("item.completed", {"type": "agent_message"}),
        event("turn.completed"),
    ]
    result = summarize(rows)
    assert result["model_turns"] == 1
    assert result["agent_messages_with_tools"] == 1
    assert result["tool_calls_started"] == 2
    assert result["agent_messages"] == 1
    assert result["over_40_model_turns"] is False


def test_gate_statuses_and_long_target():
    rows = [{"type": "turn.started"} for _ in range(41)]
    rows += [{"type": "completion_gate", "status": "returned"}, {"type": "completion_gate", "status": "accepted"}]
    result = summarize(rows)
    assert result["model_turns"] == 41
    assert result["over_40_model_turns"] is True
    assert result["completion_gate_statuses"] == {"accepted": 1, "returned": 1}
