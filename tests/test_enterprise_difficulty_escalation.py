import json
import importlib.util
import tomllib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TASKS = {
    "eb003-replay-provenance-004": {"judgment_claim_permission_lattice", "data_evidence_graph_join"},
    "eb006-signal-noise-004": {"data_experimental_unit_hierarchy", "math_sensitivity_frontier"},
    "eb009-diversity-coverage-004": {"data_evidence_graph_join", "math_sensitivity_frontier"},
    "eb010-next-batch-001": {"horizon_two_stage_acquisition", "math_sensitivity_frontier"},
    "eb003-recovery-chain-005": {"judgment_claim_permission_lattice", "data_evidence_graph_join", "horizon_end_to_end_claim"},
    "eb005-normalization-hierarchy-003": {"data_experimental_unit_hierarchy", "math_sensitivity_frontier", "judgment_blocker_and_abstention"},
    "eb008-route-portfolio-002": {"data_shared_inventory_allocation", "data_evidence_graph_join", "judgment_blocker_and_abstention"},
    "eb010-next-batch-002": {"horizon_two_stage_acquisition", "math_sensitivity_frontier", "judgment_value_of_information"},
    "eb011-measurement-request-005": {"judgment_value_of_information", "math_sensitivity_frontier", "judgment_blocker_and_abstention"},
    "eb012-cross-handoff-audit-001": {"data_evidence_graph_join", "judgment_claim_permission_lattice", "horizon_end_to_end_claim"},
    "eb010-closed-loop-replay-003": {"horizon_adaptive_policy_replay", "math_replay_stability"},
    "eb010-closed-loop-ambiguity-004": {"judgment_semantic_ambiguity_resolution", "retrieval_schema_discovery", "environment_schema_discovery_under_offline"},
    "eb010-adaptive-policy-regret-005": {"horizon_adaptive_policy_replay", "math_robust_scenario_optimization", "judgment_blocker_and_abstention"},
    "eb010-distributional-policy-stress-006": {"horizon_adaptive_policy_replay", "math_robust_scenario_optimization", "math_sensitivity_frontier", "judgment_blocker_and_abstention"},
    "eb012-cross-stage-chain-002": {"horizon_end_to_end_claim", "judgment_claim_permission_lattice", "data_evidence_graph_join"},
    "eb012-revocation-portfolio-003": {"horizon_checkpointed_workflow", "data_shared_inventory_allocation", "math_robust_scenario_optimization"},
    "eb013-evidence-budget-routing-001": {"judgment_evidence_route_selection", "data_dependency_graph_routing", "math_correlation_adjusted_reduction", "retrieval_provenance_temporal_boundary"},
    "eb013-evidence-budget-routing-002": {"horizon_adaptive_policy_replay", "judgment_evidence_route_selection", "math_minimax_evidence_route_selection", "retrieval_provenance_temporal_boundary"},
}

L4_TASKS = {
    "eb003-recovery-chain-005",
    "eb005-normalization-hierarchy-003",
    "eb008-route-portfolio-002",
    "eb010-next-batch-002",
    "eb011-measurement-request-005",
    "eb012-cross-handoff-audit-001",
}


def test_escalation_modules_are_registered_and_bound_to_tasks():
    catalog = json.loads((ROOT / "config/module_catalog.json").read_text(encoding="utf-8"))
    registered = {item["id"] for item in catalog["modules"]}
    tranche = json.loads((ROOT / "candidate_pools/enterprise-v1/scale_tranche_005.json").read_text(encoding="utf-8"))
    assert tranche["status"] == "TARGET_TRIALS_PASS_RELEASE_BLOCKED"
    assert len(tranche["recommended_candidates"]) == 6
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


def test_l4_reference_oracles_match_independent_recomputation():
    for task_id in L4_TASKS:
        task = ROOT / "benchmarks" / task_id
        spec = importlib.util.spec_from_file_location(f"oracle_{task_id}", task / "verifier.py")
        verifier = importlib.util.module_from_spec(spec)
        assert spec and spec.loader
        spec.loader.exec_module(verifier)
        expected = verifier.expected(task / "data")
        reference = json.loads((task / "verifier_only/reference.json").read_text(encoding="utf-8"))
        assert reference["decision"] == expected["decision"], task_id
        assert reference["rules_version"] == expected["rules_version"], task_id
