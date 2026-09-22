"""Observable trajectory metrics; parallel tool calls count as one model turn."""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Iterable


def read_events(path: str | Path) -> list[dict]:
    return [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]


def summarize(events: Iterable[dict]) -> dict[str, object]:
    rows = list(events)
    turn_started = sum(row.get("type") == "turn.started" for row in rows)
    turn_completed = sum(row.get("type") == "turn.completed" for row in rows)
    tool_started = sum(row.get("type") == "item.started" and row.get("item", {}).get("type") == "command_execution" for row in rows)
    tool_completed = sum(row.get("type") == "item.completed" and row.get("item", {}).get("type") == "command_execution" for row in rows)
    model_messages = sum(row.get("type") == "item.completed" and row.get("item", {}).get("type") == "agent_message" for row in rows)
    agent_messages_with_tools = 0
    current_message_has_tool = False
    for row in rows:
        item_type = row.get("item", {}).get("type")
        if row.get("type") == "item.completed" and item_type == "agent_message":
            if current_message_has_tool:
                agent_messages_with_tools += 1
            current_message_has_tool = False
        elif row.get("type") == "item.started" and item_type == "command_execution":
            current_message_has_tool = True
    if current_message_has_tool:
        agent_messages_with_tools += 1
    interaction_rounds = agent_messages_with_tools or turn_started
    gate_events = [row for row in rows if row.get("type") == "completion_gate"]
    statuses = Counter(row.get("status") for row in gate_events)
    return {
        "model_turns": interaction_rounds,
        "explicit_turn_events": turn_started,
        "completed_turns": turn_completed,
        "tool_calls_started": tool_started,
        "tool_calls_completed": tool_completed,
        "agent_messages": model_messages,
        "agent_messages_with_tools": agent_messages_with_tools,
        "completion_gate_events": len(gate_events),
        "completion_gate_statuses": dict(sorted((str(k), v) for k, v in statuses.items())),
        "long_trace_target": "over_40_model_turns",
        "over_40_model_turns": turn_started > 40,
    }


def summarize_file(path: str | Path) -> dict[str, object]:
    return summarize(read_events(path))
