import re
import tomllib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TASKS = (
    "eb001-split-leakage-001",
    "eb003-failure-recovery-003",
    "eb004-adtte-censoring-002",
    "eb005-batch-normalization-002",
    "eb008-stock-route-001",
    "eb010-next-batch-001",
)


def card_module_ids(card: Path) -> list[str]:
    ids: list[str] = []
    in_modules = False
    for line in card.read_text(encoding="utf-8").splitlines():
        if line == "difficulty_modules:":
            in_modules = True
            continue
        if in_modules and line and not line.startswith(" "):
            break
        if in_modules:
            match = re.match(r"\s+- id: ([A-Za-z0-9_]+)$", line)
            if match:
                ids.append(match.group(1))
    return ids


def configured_module_ids(contract: Path) -> set[str]:
    payload = tomllib.loads(contract.read_text(encoding="utf-8"))
    return {module for modules in payload["modules"].values() for module in modules}


def test_enterprise_cards_bind_observable_difficulty_modules() -> None:
    for task_id in TASKS:
        ids = card_module_ids(ROOT / "benchmarks" / task_id / "scenario-card.yaml")
        configured = configured_module_ids(ROOT / "candidate_pools/enterprise-v1/contracts" / f"{task_id}.toml")
        assert len(ids) >= 4, task_id
        assert set(ids) <= configured, (task_id, sorted(set(ids) - configured))


def test_each_difficulty_module_has_a_decision_flip() -> None:
    for task_id in TASKS:
        text = (ROOT / "benchmarks" / task_id / "scenario-card.yaml").read_text(encoding="utf-8")
        assert text.count("observable:") >= 4, task_id
        assert text.count("decision_flip:") >= 4, task_id
