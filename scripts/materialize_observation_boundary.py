"""Build a new versioned task without overwriting earlier trial packages."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TASK = ROOT / "benchmarks/eb013-observation-boundary-004"


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n")


def main():
    if (TASK / "quality/pretrial_freeze.json").exists():
        raise RuntimeError("frozen task; create a new version instead")
    data = TASK / "data"
    rules = {"rules_version": "observation-boundary-v1", "scope": "primary", "decision_date": "2026-09-21",
             "stage1_budget": 2.5, "commitment_budget": 4.5, "total_budget": 6.0,
             "capacity_slots": 3, "deadline_hours": 6,
             "thresholds": {"signal": 0.3, "selectivity": 0.2},
             "setup_costs": {"common": 1.0, "signal": 1.5, "select": 1.5, "fast": 0.5},
             "setup_slots": {"common": 1, "signal": 2, "select": 2, "fast": 1},
             "objective": ["minimize maximum residual/axis-threshold over ALL worlds and critical axes",
                           "minimize worst branch cost", "minimize setup cost", "lexical stage1 ID", "lexical sorted observation-action mapping"]}
    write(data / "rules.json", rules)
    worlds = [{"id": "W1", "scenario": "nominal", "initial": {"signal": .8, "selectivity": .65}},
              {"id": "W2", "scenario": "stress", "initial": {"signal": .8, "selectivity": .65}},
              {"id": "W3", "scenario": "nominal", "initial": {"signal": .65, "selectivity": .8}},
              {"id": "W4", "scenario": "stress", "initial": {"signal": .65, "selectivity": .8}}]
    write(data / "worlds.json", worlds)
    stage1 = [{"id": "Q1", "cost": 1, "hours": 1, "covers": {"signal": .2, "selectivity": .2}, "group": "G1",
               "observations": {"W1": "amber", "W2": "amber", "W3": "green", "W4": "green"}},
              {"id": "Q2", "cost": 2, "hours": 2, "covers": {"signal": .25, "selectivity": .25}, "group": "G1",
               "observations": {"W1": "a", "W2": "b", "W3": "c", "W4": "d"}},
              {"id": "Q3", "cost": .5, "hours": 1, "covers": {"signal": .1, "selectivity": .1}, "group": "G1",
               "observations": {"W1": "same", "W2": "same", "W3": "same", "W4": "same"}}]
    labels = ["amber", "green", "a", "b", "c", "d", "same"]
    def action(rid, family, normal, stress, cost=1, hours=2, group="G2", source="S1", future=False):
        return {"id": rid, "family": family, "cost": cost, "hours": hours, "group": group,
                "covers": {"nominal": dict(zip(("signal", "selectivity"), normal)),
                           "stress": dict(zip(("signal", "selectivity"), stress))},
                "allowed_observations": labels, "dependencies": [], "source_id": source, "future_outcome": future}
    actions = [action("A1", "common", (.48, .4), (.3, .4)),
               action("A2", "common", (.32, .5), (.4, .36)),
               action("A3", "signal", (.6, .3), (.5, .3)),
               action("A4", "select", (.3, .62), (.32, .57)),
               action("A5", "fast", (.43, .44), (.32, .4), cost=.5, hours=1),
               action("A6", "common", (.65, .65), (.65, .65), group="G1"),
               action("A7", "common", (.55, .55), (.55, .55), hours=6),
               action("A8", "fast", (.7, .7), (.7, .7), source="S2"),
               action("A9", "fast", (.7, .7), (.7, .7), source="S3"),
               action("A10", "fast", (.7, .7), (.7, .7), source="S4"),
               action("A11", "fast", (.7, .7), (.7, .7), future=True)]
    write(data / "requests.json", {"stage1": stage1, "stage2": actions})
    write(data / "sources.json", {
        "S1": {"status": "current", "scope": "primary", "available_at": "2026-09-20"},
        "S2": {"status": "retracted", "scope": "primary", "available_at": "2026-09-20"},
        "S3": {"status": "current", "scope": "primary", "available_at": "2026-09-22"},
        "S4": {"status": "current", "scope": "pilot", "available_at": "2026-09-20"}})
    write(data / "output_contract.json", {
        "version": "1.0.0", "numeric_tolerance": .000001,
        "decision.json": {"decision": "execute or hold", "selected": "policy summary below, or null on hold",
                          "claim_boundary": "planning_only", "human_review_required": True},
        "policy_summary": {"stage1_id": "string", "policy": "exact observable-label to action-ID object",
                           "setup_families": "sorted unique array", "setup_cost": "number", "setup_slots": "integer",
                           "worst_cost": "number", "risk": "number"},
        "plan.json": {"alternatives": "one {stage1_id, policy_count, eligible_count, best} per stage1; best is eligible policy summary or null",
                      "source_audit": "one {action_id, blockers} per stage2; source-only blockers sorted from source_status, future_source, source_scope, future_outcome",
                      "replay": "selected policy: one {world_id, observation, action_id, residuals, cost, hours, blockers} per world; [] on hold; blockers sorted from critical_threshold,total_budget,deadline"},
        "enumeration": "For policy_count enumerate mappings after source/dependency/observation gates, BEFORE budget/capacity/deadline/threshold gates. One action per observable label. Include all labels, including those shared by several worlds.",
        "provenance.json": {"input_sha256": "hash every data/*.json including this contract, paths with or without data/",
                            "rules_version": "rules.json value", "network": "off", "deterministic": True},
        "audit.md": "Nonempty explanation of observability boundary, resource commitment, alternative comparisons and human-review planning boundary.",
        "equivalences": ["JSON object and keyed row order", "extra explanatory keys", "numeric strings", "data-prefixed hashes"],
        "forbidden": ["duplicate keys or rows", "missing or fabricated worlds", "world-ID action map", "future evidence", "nonfinite or boolean numbers"]})
    write(TASK / "quality/difficulty_card.json", {
        "task_id": TASK.name, "primary_module": "horizon_observation_equivalence",
        "secondary_modules": ["math_ex_ante_shared_setup", "math_distributional_minimax"],
        "supporting_modules": ["retrieval_provenance_temporal_boundary", "math_correlation_adjusted_reduction", "environment_resource_budget"],
        "dimensions": ["information partition", "prospective resource coupling", "distribution stress", "temporal evidence join", "correlation", "asymmetric safety thresholds"],
        "status": "CALIBRATION_REQUIRED", "cross_domain_transfer": "NOT_RUN"})


if __name__ == "__main__":
    main()
