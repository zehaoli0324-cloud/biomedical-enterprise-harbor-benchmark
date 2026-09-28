"""Independent world-first oracle, mutation controls, and immutable trial freeze."""
import copy
import hashlib
import importlib.util
import itertools
import json
import tempfile
from fractions import Fraction as F
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TASK = ROOT / "benchmarks/eb013-observation-boundary-004"


def read(path):
    return json.loads(path.read_text())


def write(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n")


def verifier():
    spec = importlib.util.spec_from_file_location("observation_verifier", TASK / "verifier.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def independent(data):
    """World-first assignments + equivalence constraint, using rational arithmetic."""
    rules, requests, worlds, sources = [read(data / name) for name in ("rules.json", "requests.json", "worlds.json", "sources.json")]
    rational = lambda v: F(str(v))
    all_eligible, summaries = [], []
    for first in requests["stage1"]:
        choices = []
        for world in worlds:
            choices.append([a for a in requests["stage2"]
                            if sources[a["source_id"]]["status"] == "current"
                            and sources[a["source_id"]]["scope"] == rules["scope"]
                            and sources[a["source_id"]]["available_at"] <= rules["decision_date"]
                            and not a["future_outcome"]
                            and not set(a["dependencies"]) - {first["id"]}
                            and first["observations"][world["id"]] in a["allowed_observations"]])
        count, eligible = 0, []
        for picks in itertools.product(*choices):
            mapping = {}
            for world, action in zip(worlds, picks):
                label = first["observations"][world["id"]]
                if label in mapping and mapping[label] != action["id"]:
                    break
                mapping[label] = action["id"]
            else:
                count += 1
                families = {a["family"] for a in picks}
                setup = sum((rational(rules["setup_costs"][f]) for f in families), F(0))
                upfront = rational(first["cost"]) + setup
                if (rational(first["cost"]) > rational(rules["stage1_budget"])
                        or upfront > rational(rules["commitment_budget"])
                        or sum(rules["setup_slots"][f] for f in families) > rules["capacity_slots"]):
                    continue
                ratios, costs = [], []
                for world, action in zip(worlds, picks):
                    cost = upfront + rational(action["cost"])
                    if cost > rational(rules["total_budget"]) or rational(first["hours"]) + rational(action["hours"]) > rational(rules["deadline_hours"]):
                        break
                    costs.append(cost)
                    for axis, threshold in rules["thresholds"].items():
                        a = rational(first["covers"].get(axis, 0))
                        b = rational(action["covers"][world["scenario"]].get(axis, 0))
                        reduced = (a + b) if first["group"] != action["group"] else max(a, b)
                        ratio = max(F(0), rational(world["initial"][axis]) - reduced) / rational(threshold)
                        ratios.append(ratio)
                    if max(ratios) > 1:
                        break
                else:
                    eligible.append((max(ratios), max(costs), setup, first["id"], tuple(sorted(mapping.items()))))
        summaries.append((first["id"], count, len(eligible), min(eligible) if eligible else None))
        all_eligible.extend(eligible)
    return min(all_eligible) if all_eligible else None, summaries


def numeric(key):
    return tuple(round(float(v), 6) if isinstance(v, (F, int, float)) or type(v).__name__ == "Decimal" else v for v in key) if key else None


def crosscheck(data, module):
    wanted, alternatives = independent(data)
    exp = module.expected(data)
    actual = numeric(module.objective(exp["winner"])) if exp["winner"] else None
    assert actual == numeric(wanted), (actual, wanted)
    for stage1, count, eligible_count, best in alternatives:
        row = next(r for r in exp["summaries"] if r["stage1_id"] == stage1)
        assert (count, eligible_count) == (row["policy_count"], row["eligible_count"])
        assert (numeric(module.objective(row["best"])) if row["best"] else None) == numeric(best)
    return exp


def reference(out, data, module):
    exp = module.expected(data)
    winner = exp["winner"]
    write(out / "decision.json", {"decision": "execute" if winner else "hold",
          "selected": module.summary(winner) if winner else None, "claim_boundary": "planning_only", "human_review_required": True})
    write(out / "plan.json", {"alternatives": exp["summaries"], "source_audit": exp["source_audit"],
                              "replay": winner["replay"] if winner else []})
    write(out / "provenance.json", {"input_sha256": exp["hashes"], "rules_version": read(data / "rules.json")["rules_version"], "network": "off", "deterministic": True})
    (out / "audit.md").write_text("One action per observable label, not per latent world. All preparations committed upfront; review worst-world risk and human approval. Synthetic planning only.\n")
    return exp


def run_controls():
    module = verifier()
    exp = crosscheck(TASK / "data", module)
    controls, variants = [], []
    with tempfile.TemporaryDirectory(prefix="observation-controls-") as directory:
        root = Path(directory)
        out = root / "outputs"
        def record(name, expected_pass):
            passed, errors = module.verify(out, TASK / "data")
            assert passed == expected_pass, (name, errors)
            controls.append({"id": name, "expected_pass": expected_pass, "passed": True, "errors": errors})
        reference(out, TASK / "data", module)
        record("reference", True)
        for name, file, mutate in [
            ("missing-field", "decision.json", lambda p: p.pop("selected")),
            ("wrong-action", "decision.json", lambda p: p["selected"]["policy"].update({next(iter(p["selected"]["policy"])): "A8"})),
            ("world-id-shortcut", "decision.json", lambda p: p["selected"].update({"policy": {"W1": "A1", "W2": "A2", "W3": "A4", "W4": "A4"}})),
            ("extra-observation", "decision.json", lambda p: p["selected"]["policy"].update({"unknown": "A1"})),
            ("mean-risk", "decision.json", lambda p: p["selected"].update({"risk": .01})),
            ("missing-world", "plan.json", lambda p: p["replay"].pop()),
            ("duplicate-world", "plan.json", lambda p: p["replay"].append(p["replay"][0])),
            ("wrong-residual", "plan.json", lambda p: p["replay"][0]["residuals"].update({"signal": .999})),
            ("wrong-source-join", "plan.json", lambda p: p["source_audit"][-1].update({"blockers": []})),
            ("wrong-hash", "provenance.json", lambda p: p["input_sha256"].update({"rules.json": "0" * 64})),
            ("claim-inflation", "decision.json", lambda p: p.update({"claim_boundary": "validated"})),
            ("nan-risk", "decision.json", lambda p: p["selected"].update({"risk": "NaN"})),
            ("boolean-risk", "decision.json", lambda p: p["selected"].update({"risk": True})),
        ]:
            reference(out, TASK / "data", module)
            payload = read(out / file)
            mutate(payload)
            write(out / file, payload)
            record(name, False)
        reference(out, TASK / "data", module)
        plan = read(out / "plan.json")
        for rows in plan.values():
            rows.reverse()
        write(out / "plan.json", plan)
        prov = read(out / "provenance.json")
        prov["input_sha256"] = {"data/" + k: v for k, v in prov["input_sha256"].items()}
        write(out / "provenance.json", prov)
        decision = read(out / "decision.json")
        decision["selected"]["risk"] = str(decision["selected"]["risk"])
        write(out / "decision.json", decision)
        record("row-order-path-numeric-equivalence", True)
        rules = read(TASK / "data/rules.json")
        eligible = [p for p in exp["policies"] if p["eligible"]]
        for name, metric in (
            ("mean-objective-baseline", lambda p: sum(max(r["residuals"][a] / t for a, t in rules["thresholds"].items()) for r in p["replay"]) / len(p["replay"])),
            ("absolute-residual-baseline", lambda p: max(max(r["residuals"].values()) for r in p["replay"])),
            ("cheapest-baseline", lambda p: p["worst_cost"]),
        ):
            naive = min(eligible, key=lambda p: (round(metric(p), 8), *module.objective(p)[1:]))
            assert module.summary(naive) != module.summary(exp["winner"]), name
            reference(out, TASK / "data", module)
            decision = read(out / "decision.json")
            decision["selected"] = module.summary(naive)
            write(out / "decision.json", decision)
            plan = read(out / "plan.json")
            plan["replay"] = naive["replay"]
            write(out / "plan.json", plan)
            record(name, False)
        for name in ("partition-collapse", "capacity-contract", "deadline-relax", "source-release", "correlation-release", "threshold-change", "no-feasible", "world-order"):
            changed = root / name
            for path in (TASK / "data").glob("*.json"):
                write(changed / path.name, read(path))
            rules, requests, worlds, sources = [read(changed / n) for n in ("rules.json", "requests.json", "worlds.json", "sources.json")]
            if name == "partition-collapse":
                for first in requests["stage1"]:
                    first["observations"] = {w["id"]: "same" for w in worlds}
            if name == "capacity-contract": rules["capacity_slots"] = 2
            if name == "deadline-relax": rules["deadline_hours"] = 9
            if name == "source-release": sources["S2"]["status"] = "current"
            if name == "correlation-release": requests["stage2"][5]["group"] = "G9"
            if name == "threshold-change": rules["thresholds"]["selectivity"] = .05
            if name == "no-feasible": rules["total_budget"] = .1
            if name == "world-order": worlds.reverse()
            for filename, payload in zip(("rules.json", "requests.json", "worlds.json", "sources.json"), (rules, requests, worlds, sources)):
                write(changed / filename, payload)
            result = crosscheck(changed, module)
            reference(out, changed, module)
            passed, errors = module.verify(out, changed)
            assert passed, errors
            flip = (module.summary(result["winner"]) if result["winner"] else None) != module.summary(exp["winner"])
            assert flip == (name != "world-order"), (name, flip)
            variants.append({"id": name, "decision_flip": flip, "passed": passed,
                             "winner": module.summary(result["winner"]) if result["winner"] else None})
    return exp, controls, variants


def main():
    if (TASK / "quality/pretrial_freeze.json").exists():
        raise RuntimeError("already frozen; tests may recheck without replacing evidence")
    exp, controls, variants = run_controls()
    write(TASK / "verifier_only/reference.json", {k: v for k, v in exp.items() if k != "policies"})
    write(TASK / "controls/calibration_results.json", {"status": "PASS", "controls": controls, "variants": variants})
    write(TASK / "quality/contract_audit.json", {"status": "PASS", "contract": "data/output_contract.json", "mutation_controls": controls})
    write(TASK / "quality/independent_verifier_audit.json", {"status": "AUTOMATED_CROSSCHECK_PASS", "human_review": "NOT_RUN", "method": "label-first Decimal oracle vs world-first Fraction oracle", "variant_count": len(variants)})
    paths = [TASK / "verifier.py", TASK / "instruction.md", TASK / "task.yaml", *sorted((TASK / "data").glob("*.json")), TASK / "controls/calibration_results.json"]
    write(TASK / "quality/pretrial_freeze.json", {"version": "1.0.0", "sha256": {p.relative_to(TASK).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}})
    print(json.dumps({"status": "PASS", "controls": len(controls), "variants": variants, "winner": exp["winner"]}, indent=2))


if __name__ == "__main__":
    main()
