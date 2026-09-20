"""Small, dependency-free loader for the scenario-card contract."""

from __future__ import annotations

import hashlib
import re
from pathlib import Path

from .models import ScenarioCard


class ScenarioCardError(ValueError):
    pass


def _scalar(text: str, key: str) -> str:
    match = re.search(rf"^\s*{re.escape(key)}:\s*([^#\n]+)", text, re.MULTILINE)
    if not match:
        raise ScenarioCardError(f"scenario card is missing {key}")
    return match.group(1).strip().strip('"\'')


def _list(text: str, key: str) -> tuple[str, ...]:
    match = re.search(rf"^\s*{re.escape(key)}:\s*\[([^\]]*)\]", text, re.MULTILINE)
    if match:
        return tuple(item.strip().strip('"\'') for item in match.group(1).split(",") if item.strip())
    start = re.search(rf"^\s*{re.escape(key)}:\s*$", text, re.MULTILINE)
    if not start:
        raise ScenarioCardError(f"scenario card is missing {key}")
    values: list[str] = []
    for line in text[start.end() :].splitlines():
        if not line.strip():
            continue
        if not line.startswith("  -") and not line.startswith("    -"):
            break
        values.append(line.split("-", 1)[1].strip().strip('"\''))
    return tuple(values)


def _gate_values(text: str) -> dict[str, str]:
    section = re.search(r"^release_gates:\s*$([\s\S]*?)(?=^\S|\Z)", text, re.MULTILINE)
    if not section:
        raise ScenarioCardError("scenario card is missing release_gates")
    gates: dict[str, str] = {}
    for line in section.group(1).splitlines():
        match = re.match(r"^\s{2}([a-zA-Z0-9_-]+):\s*([^#\n]+)", line)
        if match:
            gates[match.group(1)] = match.group(2).strip().strip('"\'')
    return gates


def load_scenario_card(path: str | Path) -> ScenarioCard:
    card_path = Path(path).resolve()
    text = card_path.read_text(encoding="utf-8")
    status = _scalar(text, "status")
    if status not in {"candidate", "needs-data", "contract_only", "ready"}:
        raise ScenarioCardError(f"unsupported scenario card status: {status}")
    judgments = _list(text, "scientific_judgments")
    handoffs = len(re.findall(r"^\s{2}- from:\s*", text, re.MULTILINE))
    if not judgments:
        raise ScenarioCardError("scenario card requires at least one scientific judgment")
    if handoffs == 0:
        raise ScenarioCardError("scenario card requires at least one workflow handoff")
    gates = _gate_values(text)
    required_gates = {"scientific_reality", "observability", "verifiability", "naive_resistance"}
    missing = required_gates - set(gates)
    if missing:
        raise ScenarioCardError(f"scenario card missing release gates: {sorted(missing)}")
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return ScenarioCard(
        path=str(card_path),
        digest=digest,
        scenario_id=_scalar(text, "scenario_id"),
        status=status,
        source_scenarios=_list(text, "source_scenarios"),
        scientific_judgments=judgments,
        handoff_count=handoffs,
        release_gates=gates,
    )


def validate_scenario_link(card: ScenarioCard, task_scenarios: tuple[str, ...]) -> None:
    if not set(task_scenarios).issubset(set(card.source_scenarios)):
        missing = sorted(set(task_scenarios) - set(card.source_scenarios))
        raise ScenarioCardError(f"task scenarios are absent from scenario card: {missing}")
    if card.status not in {"contract_only", "ready"}:
        raise ScenarioCardError(f"scenario card status {card.status!r} cannot feed difficulty generation")
    blocked = [name for name, value in card.release_gates.items() if value in {"fail", "blocked"}]
    if blocked:
        raise ScenarioCardError(f"scenario card has failed release gates: {blocked}")
