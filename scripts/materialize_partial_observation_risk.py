#!/usr/bin/env python3
"""Author synthetic partial-observation fixtures without replacing earlier trials."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TASK = ROOT / "benchmarks/eb013-partial-observation-risk-004"


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n")


def main():
    if (TASK / "data").exists():
        raise FileExistsError("Existing version preserved; do not regenerate over trials")
    states = ["W" + str(i) for i in range(1, 7)]
    rules = {"rules_version": "partial-observation-risk-v1", "decision_date": "2026-09-22",
             "states": states, "initial_uncertainty": {"signal": 1, "selectivity": 1},
             "critical_thresholds": {"signal": .42, "selectivity": .42}, "alpha": .6,
             "commitment_budget": 2.8, "total_budget": 4.2,
             "setup_costs": {"basic": .6, "select": .9, "targeted": 1.1},
             "probability_models": [{"id": name, "probabilities": dict(zip(states, weights))} for name, weights in [
                 ("nominal", [.3, .25, .1, .15, .15, .05]),
                 ("shift", [.05, .05, .2, .1, .25, .35]),
                 ("rare", [.1, .15, .1, .25, .2, .2])]],
             "objective": ["robust_cvar", "worst_mean_loss", "worst_cost", "setup_cost", "probe_id", "sorted_observation_policy"]}
    probes = [{"id": pid, "cost": cost, "capabilities": caps, "observations": dict(zip(states, labels))}
              for pid, cost, caps, labels in [
                  ("P0", .4, [], ["red", "red", "red", "blue", "blue", "blue"]),
                  ("P1", .9, [], ["a", "a", "b", "c", "c", "d"]),
                  ("P2", .8, ["orthogonal"], ["a", "b", "b", "c", "d", "d"])]]
    actions = [{"id": aid, "cost": cost, "family": family, "requires": requires}
               for aid, cost, family, requires in [
                   ("A", 1.2, "basic", []), ("B", .8, "select", []), ("C", .9, "select", []),
                   ("D", 1, "targeted", ["orthogonal"]), ("E", .1, "basic", []), ("F", .1, "basic", [])]]
    residuals = {
        "A": [[.22, .22]] * 6,
        "B": [[.08, .1], [.08, .1], [.38, .3], [.12, .18], [.28, .22], [.4, .35]],
        "C": [[.32, .28], [.28, .36], [.1, .08], [.3, .28], [.09, .11], [.12, .1]],
        "D": [[.14, .16], [.4, .4], [.16, .16], [.07, .08], [.4, .35], [.15, .14]],
        "E": [[.01, .01]] * 6, "F": [[.001, .001]] * 6,
    }
    ledger = []
    for aid, values in residuals.items():
        ledger.append({"action_id": aid, "revision": 1, "published_at": "2026-09-01", "status": "active",
                       "reductions": {s: {axis: round(1 - r, 6) for axis, r in zip(("signal", "selectivity"), pair)} for s, pair in zip(states, values)}})
    # A newer snapshot supersedes B's optimistic historical estimate; withdrawal is a tombstone.
    b = next(r for r in ledger if r["action_id"] == "B")
    ledger.append({**b, "revision": 2, "published_at": "2026-09-15"})
    b["reductions"] = {s: {"signal": .99, "selectivity": .99} for s in states}
    ledger.append({"action_id": "E", "revision": 2, "published_at": "2026-09-20", "status": "withdrawn", "reductions": {}})
    next(r for r in ledger if r["action_id"] == "F")["published_at"] = "2026-09-25"
    ledger.append({"action_id": "B", "revision": 3, "published_at": "2026-09-25", "status": "active",
                   "reductions": {s: {"signal": 1, "selectivity": 1} for s in states}})
    write(TASK / "data/rules.json", rules)
    write(TASK / "data/catalog.json", {"probes": probes, "actions": actions})
    write(TASK / "data/evidence.json", ledger)
    write(TASK / "data/output_contract.json", {
        "version": "1.0.0", "numeric_tolerance": .000001,
        "selected_fields": ["probe_id", "observation_policy", "setup_families", "setup_cost", "worst_cost", "robust_cvar", "worst_mean_loss"],
        "plan_extra_fields": ["policies", "risk_by_model", "evidence_resolution"],
        "route_columns": ["state", "observation", "action_id", "signal_residual", "selectivity_residual", "loss", "cost"],
        "required_hash_paths": ["rules.json", "catalog.json", "evidence.json", "output_contract.json"],
        "equivalents": ["JSON field order", "all keyed row orders", "setup family order", "finite numeric strings", "data/ hash prefix"],
        "forbidden": ["duplicate keys/rows", "extra observation keys", "NaN/Infinity", "missing values", "invented hash", "hidden-state-conditioned actions"]})
    write(TASK / "quality/source_ledger.json", {"status": "SYNTHETIC_DISCLOSED", "source": "scripts/materialize_partial_observation_risk.py",
        "empirical_claim": False, "scope": "Finite illustrative assay planning; probabilities and reductions are synthetic."})


if __name__ == "__main__":
    main()
