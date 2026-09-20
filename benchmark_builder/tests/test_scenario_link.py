from pathlib import Path

from benchmark_builder.config import load_spec
from benchmark_builder.scenario import ScenarioCardError, load_scenario_card, validate_scenario_link


ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "config/examples/crispr-resistance-e2e-001.toml"
CARD = ROOT / "benchmarks/crispr-resistance-e2e-001/scenario-card.yaml"


def test_card_has_scientific_context_contract():
    card = load_scenario_card(CARD)
    assert card.status == "contract_only"
    assert "C20" in card.source_scenarios
    assert card.handoff_count >= 3
    assert card.release_gates["scientific_reality"] == "pass"


def test_config_requires_scenario_link():
    spec = load_spec(CONFIG)
    assert spec.scenario_card is not None
    assert spec.scenario_card.digest


def test_candidate_card_cannot_feed_difficulty(tmp_path: Path):
    card = CARD.read_text(encoding="utf-8").replace("status: contract_only", "status: candidate", 1)
    path = tmp_path / "candidate.yaml"
    path.write_text(card, encoding="utf-8")
    loaded = load_scenario_card(path)
    try:
        validate_scenario_link(loaded, ("C20",))
    except ScenarioCardError:
        return
    raise AssertionError("candidate scenario card must not feed difficulty generation")
