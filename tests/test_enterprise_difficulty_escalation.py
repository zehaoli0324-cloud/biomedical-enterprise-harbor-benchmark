import json
import tomllib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TASKS = {
    "eb003-replay-provenance-004": {"judgment_claim_permission_lattice", "data_evidence_graph_join"},
    "eb006-signal-noise-004": {"data_experimental_unit_hierarchy", "math_sensitivity_frontier"},
    "eb009-diversity-coverage-004": {"data_evidence_graph_join", "math_sensitivity_frontier"},
    "eb010-next-batch-001": {"horizon_two_stage_acquisition", "math_sensitivity_frontier"},
}


def test_v04_modules_are_registered_and_bound_to_four_tasks():
    catalog = json.loads((ROOT / "config/module_catalog.json").read_text(encoding="utf-8"))
    registered = {item["id"] for item in catalog["modules"]}
    tranche = json.loads((ROOT / "candidate_pools/enterprise-v1/scale_tranche_005.json").read_text(encoding="utf-8"))
    assert tranche["status"] == "CONTRACT_ONLY_DIFFICULTY_ESCALATION"
    assert len(tranche["recommended_candidates"]) == 4
    for task_id, required in TASKS.items():
        assert required <= registered
        contract = tomllib.loads((ROOT / "candidate_pools/enterprise-v1/contracts" / f"{task_id}.toml").read_text(encoding="utf-8"))
        selected = {module for values in contract["modules"].values() for module in values}
        assert required <= selected, (task_id, required - selected)


def test_v04_scenario_cards_declare_observable_decision_flips():
    for task_id, required in TASKS.items():
        text = (ROOT / "benchmarks" / task_id / "scenario-card.yaml").read_text(encoding="utf-8")
        assert "difficulty_modules:" in text
        for module_id in required:
            marker = f"- id: {module_id}"
            start = text.index(marker)
            end = text.find("\n  - id:", start + len(marker))
            block = text[start:] if end == -1 else text[start:end]
            assert "observable:" in block
            assert "decision_flip:" in block
