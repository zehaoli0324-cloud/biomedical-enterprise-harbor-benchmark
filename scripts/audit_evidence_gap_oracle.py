"""Independent Fraction-based two-stage product oracle; no verifier imports."""
from fractions import Fraction
from itertools import product
import json


def solve(data):
    def read(name):
        return json.loads((data / name).read_text())

    rules, registry = read("rules.json"), read("evidence.json")
    assert rules["max_actions"] == 2, "This cross-check independently covers two-stage designs only"
    sources = {s["id"]: s for s in read("sources.json")}
    actions = {a["id"]: a for a in read("actions.json")}
    feedback = read("feedback.json")
    premises = {p["id"]: p for p in registry["premises"]}

    def f(value):
        return Fraction(str(value))

    def effect(row):
        return sum(map(f, row["treatment"])) / len(row["treatment"]) - sum(map(f, row["control"])) / len(row["control"])

    initial = []
    for row in registry["observations"]:
        source = sources[row["source_id"]]
        if source["status"] == "current" and source["available_on"] <= rules["decision_date"] and source["scope"] == premises[row["premise_id"]]["scope"]:
            initial.append((row["premise_id"], source["independence_group"], effect(row)))

    def states(obs):
        statuses = {}
        for key, premise in premises.items():
            rows = [(group, value) for pid, group, value in obs if pid == key]
            bad = {g for g, value in rows if value < f(premise["min_effect"])}
            good = {g for g, value in rows if value >= f(premise["min_effect"])} - bad
            statuses[key] = "refuted" if bad else "supported" if len(good) >= premise["quorum"] else "unknown"
        claims = {}
        for claim in registry["claims"]:
            values = [statuses[p] for p in claim["requires"]]
            claims[claim["id"]] = "refuted" if "refuted" in values else "unknown" if "unknown" in values else "supported"
        return statuses, claims

    def choices(obs, spent, used):
        ps, cs = states(obs)
        eligible = [None]
        if all(cs[c["id"]] != "unknown" for c in registry["claims"] if c["resolution_weight"] > 0):
            return eligible
        for action in actions.values():
            if action["id"] not in used and action["status"] == "current" and action["available_on"] <= rules["decision_date"] and spent + f(action["cost"]) <= f(rules["budget"]) and all(ps[p] == "supported" for p in action["depends_on"]):
                eligible.append(action)
        return eligible

    def append(obs, action, result):
        if action["scope"] != premises[action["premise_id"]]["scope"]:
            return list(obs)
        return obs + [(action["premise_id"], action["independence_group"], effect(result))]

    def leaf(obs, cost, depth):
        ps, cs = states(obs)
        score = sum(c["resolution_weight"] for c in registry["claims"] if cs[c["id"]] != "unknown")
        return (score, cost, depth)

    def hold():
        return {"action": "hold", "branches": {}}

    candidates = []

    def save(tree, outcomes):
        key = json.dumps(tree, sort_keys=True, separators=(",", ":"))
        rank = (-min(r[0] for r in outcomes), max(r[1] for r in outcomes), max(r[2] for r in outcomes), key)
        candidates.append((rank, tree))

    save(hold(), [leaf(initial, f(0), 0)])
    for first in choices(initial, f(0), ()):
        if first is None:
            continue
        first_cost = f(first["cost"])
        outcomes = feedback[first["outcomes"]]
        after = [append(initial, first, result) for result in outcomes]
        second_options = [choices(obs, first_cost, (first["id"],)) for obs in after]
        for seconds in product(*second_options):
            tree = {"action": first["id"], "branches": {}}
            terminal = []
            for result, obs, second in zip(outcomes, after, seconds):
                if second is None:
                    tree["branches"][result["id"]] = hold()
                    terminal.append(leaf(obs, first_cost, 1))
                else:
                    branch = {"action": second["id"], "branches": {}}
                    for result2 in feedback[second["outcomes"]]:
                        branch["branches"][result2["id"]] = hold()
                        terminal.append(leaf(append(obs, second, result2), first_cost + f(second["cost"]), 2))
                    tree["branches"][result["id"]] = branch
            save(tree, terminal)
    best, tree = min(candidates, key=lambda row: row[0])
    return {"policy": tree, "objective": {"worst_resolved_weight": -best[0], "worst_cost": float(best[1]), "max_action_count": best[2], "policy_key": best[3]}, "candidate_count": len(candidates)}
