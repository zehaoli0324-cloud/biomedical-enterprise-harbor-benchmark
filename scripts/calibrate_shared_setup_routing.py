#!/usr/bin/env python3
"""Independent Fraction oracle, real artifact mutations and held-out controls."""
from __future__ import annotations

import copy
import csv
import hashlib
import importlib.util
import itertools
import json
import shutil
import tempfile
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TASK = ROOT / "benchmarks/eb013-shared-setup-routing-003"


def load_verifier():
    spec = importlib.util.spec_from_file_location("shared_setup_verifier", TASK / "verifier.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def read(path):
    return json.loads(path.read_text())


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n")


def independent_oracle(data):
    """Enumerate setup subsets first, unlike the verifier's action-first search."""
    rules, inputs = read(data / "rules.json"), read(data / "requests.json")
    rational = lambda x: Fraction(str(x))
    families = list(rules["setup_costs"])
    best_by_first = {}
    for first in inputs["stage1"]:
        candidates = []
        if first["status"] != "current" or first["future_outcome"] or first["available_at"] > rules["decision_date"]:
            best_by_first[first["request_id"]] = None
            continue
        for size in range(len(families) + 1):
            for subset in itertools.combinations(families, size):
                setup = sum((rational(rules["setup_costs"][f]) for f in subset), Fraction(0))
                prepaid = rational(first["cost"]) + setup
                if rational(first["cost"]) > rational(rules["stage1_budget"]) or prepaid > rational(rules["commitment_budget"]):
                    continue
                states = sorted(first["outcomes"])
                choices = []
                for state in states:
                    options = []
                    for action in inputs["stage2"]:
                        if (action["setup_family"] not in subset or action["status"] != "current"
                                or action["future_outcome"] or action["available_at"] > rules["decision_date"]
                                or state not in action["allowed_observations"]
                                or set(action["dependency_ids"]) - {first["request_id"]}):
                            continue
                        cost = prepaid + rational(action["cost"])
                        residuals = []
                        for axis, threshold in rules["critical_thresholds"].items():
                            a, b = rational(first["covers"].get(axis, 0)), rational(action["covers"].get(axis, 0))
                            reduction = max(a, b) if first["correlation_group"] == action["correlation_group"] else a + b
                            residual = max(Fraction(0), rational(rules["initial_uncertainty"][axis]) - reduction
                                           - rational(first["outcomes"][state].get(axis, 0)))
                            if residual > rational(threshold):
                                break
                            residuals.append(residual)
                        else:
                            if cost <= rational(rules["total_budget"]):
                                options.append((action, max(residuals), cost))
                    choices.append(options)
                for branches in itertools.product(*choices):
                    if {b[0]["setup_family"] for b in branches} != set(subset):
                        continue
                    mapping = tuple((s, b[0]["request_id"]) for s, b in zip(states, branches))
                    candidates.append((max(b[1] for b in branches), max(b[2] for b in branches), setup,
                                       first["request_id"], mapping))
        best_by_first[first["request_id"]] = min(candidates) if candidates else None
    possible = [x for x in best_by_first.values() if x is not None]
    return min(possible) if possible else None, best_by_first


def reference(out, data, verifier, selected=None):
    out.mkdir(parents=True, exist_ok=True)
    exp = verifier.expected(data)
    winner = exp["winner"] if selected is None else selected
    fields = ("stage1_request_id", "stage2_policy", "setup_families", "setup_cost", "worst_case_cost", "worst_case_max_critical_residual")
    values = ({k: winner[k] for k in fields} if winner else dict(zip(fields, (None, {}, [], None, None, None))))
    write(out / "plan.json", {**values, "policies": exp["summaries"]})
    write(out / "decision.json", {**values, "decision": "execute_adaptive_route" if winner else "request_information",
                                  "human_review_required": True, "claim_boundary": "planning_only"})
    with (out / "route.tsv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["observation", "stage2_request_id", "residual_uncertainty", "cost", "eligible"], delimiter="\t")
        writer.writeheader()
        for row in winner["states"] if winner else []:
            writer.writerow({"observation": row["observation"], "stage2_request_id": row["stage2_request_id"],
                             "residual_uncertainty": json.dumps(row["residual_uncertainty"]),
                             "cost": row["cost"], "eligible": str(row["eligible"]).lower()})
    write(out / "provenance.json", {"input_sha256": exp["hashes"], "rules_version": read(data / "rules.json")["rules_version"], "network": "off", "deterministic": True})
    (out / "audit.md").write_text("All setup families are committed before observation. Shared setup is paid once. Branch costs are mutually exclusive. Human review is required for this synthetic planning recommendation.\n")
    return exp


def check_oracle(data, verifier):
    winner, best = independent_oracle(data)
    expected = verifier.expected(data)
    actual = verifier.objective(expected["winner"]) if expected["winner"] else None
    def numeric_key(key):
        return tuple(float(v) if isinstance(v, Fraction) else v for v in key) if key else None
    assert actual == numeric_key(winner), (actual, winner)
    for row in expected["summaries"]:
        policy = row["best_policy"]
        assert (verifier.objective(policy) if policy else None) == numeric_key(best[row["stage1_request_id"]])
    return expected


def main():
    if (TASK / "quality/target_trial_evidence.json").exists():
        raise FileExistsError("Target trial recorded; create a new task version instead of replacing its freeze.")
    verifier = load_verifier()
    data = TASK / "data"
    exp = check_oracle(data, verifier)
    controls, baselines = [], []
    with tempfile.TemporaryDirectory(prefix="shared-setup-controls-") as temp:
        out = Path(temp) / "outputs"
        reference(out, data, verifier)
        def record(name, kind, should_pass):
            passed, errors = verifier.verify(out, data)
            controls.append({"control_id": name, "kind": kind, "passed": passed == should_pass, "verifier_passed": passed, "errors": errors})
            return passed, errors
        ok, errors = record("positive-reference", "positive", True)
        baselines.append({"strategy": "reference_solution", "passed": ok, "status": "pass" if ok else "fail", "errors": errors})
        for name, kind, mutate in [
            ("wrong-hash", "insufficient_evidence", lambda p: p["input_sha256"].__setitem__("rules.json", "0" * 64)),
            ("missing-hash", "insufficient_evidence", lambda p: p["input_sha256"].pop("output_contract.json")),
        ]:
            path = out / "provenance.json"
            payload = read(path); mutate(payload); write(path, payload)
            record(name, kind, False); reference(out, data, verifier)
        for name, mutate in [
            ("field-deletion", lambda p: p.pop("setup_cost")),
            ("wrong-selected-action", lambda p: p["stage2_policy"].__setitem__("high", "M10")),
            ("missing-state", lambda p: p["stage2_policy"].pop("mid")),
            ("extra-state", lambda p: p["stage2_policy"].__setitem__("unknown", "M01")),
            ("claim-inflation", lambda p: p.__setitem__("claim_boundary", "experimentally_validated")),
        ]:
            path = out / "decision.json"
            payload = read(path); mutate(payload); write(path, payload)
            record(name, "negative", False); reference(out, data, verifier)
        route = (out / "route.tsv").read_text()
        (out / "route.tsv").write_text(route + route.splitlines()[1] + "\n")
        record("duplicate-route-row", "negative", False); reference(out, data, verifier)
        (out / "route.tsv").write_text(route.replace("6.8", "1.3"))
        record("wrong-route-cost", "negative", False); reference(out, data, verifier)
        path = out / "plan.json"; plan = read(path); plan["policies"].reverse(); plan["setup_families"].reverse(); write(path, plan)
        path = out / "provenance.json"; prov = read(path); prov["input_sha256"] = {"data/" + k: v for k, v in prov["input_sha256"].items()}; write(path, prov)
        record("order-and-path-equivalence", "invariance", True)
        cheapest = min((p for p in verifier.enumerate_policies(data) if p["eligible"]), key=lambda p: (p["worst_case_cost"], verifier.objective(p)))
        reference(out, data, verifier, cheapest); passed, errors = verifier.verify(out, data)
        baselines.append({"strategy": "simple_legal_baseline", "status": "pass" if passed else "fail", "passed": passed, "errors": errors, "selection": cheapest["stage2_policy"]})
        reference(out, data, verifier)
        decision = read(out / "decision.json"); decision["decision"] = "request_information"; write(out / "decision.json", decision)
        passed, errors = verifier.verify(out, data)
        baselines.append({"strategy": "always_abstain", "status": "pass" if passed else "fail", "passed": passed, "errors": errors})
        reference(out, data, verifier)
        (out / "plan.json").write_text("{}\n")
        passed, errors = verifier.verify(out, data)
        baselines.append({"strategy": "template_or_keyword", "status": "pass" if passed else "fail", "passed": passed, "errors": errors})
        first = read(data / "requests.json")["stage1"][0]
        greedy_actions = [next(a for a in read(data / "requests.json")["stage2"] if a["request_id"] == rid) for rid in ("M01", "M04", "M07")]
        greedy = verifier.evaluate_policy(first, greedy_actions, read(data / "rules.json"))
        controls.append({"control_id": "branchwise-greedy-overspends", "kind": "adversarial", "passed": not greedy["budget_ok"], "worst_case_cost": greedy["worst_case_cost"]})
        variants = []
        for name in ("budget-contraction", "setup-price", "retraction", "no-feasible-policy", "input-order"):
            changed = Path(temp) / name
            shutil.copytree(data, changed)
            rules, requests = read(changed / "rules.json"), read(changed / "requests.json")
            if name == "budget-contraction": rules["total_budget"] = 5.0
            if name == "setup-price": rules["setup_costs"].update({"F3": .1, "F4": .1, "F5": .1})
            if name == "retraction": requests["stage2"][0]["status"] = "retracted"
            if name == "no-feasible-policy": rules["total_budget"] = 1.0
            if name == "input-order":
                requests["stage1"].reverse(); requests["stage2"].reverse()
                for first in requests["stage1"]: first["outcomes"] = dict(reversed(list(first["outcomes"].items())))
            write(changed / "rules.json", rules); write(changed / "requests.json", requests)
            result = check_oracle(changed, verifier)
            selection = result["winner"]["stage2_policy"] if result["winner"] else None
            flip = selection != exp["winner"]["stage2_policy"]
            assert flip == (name != "input-order"), name
            reference(out, changed, verifier)
            passed, errors = verifier.verify(out, changed)
            controls.append({"control_id": name, "kind": "invariance" if name == "input-order" else "metamorphic", "passed": passed, "errors": errors})
            variants.append({"variant": name, "decision_flip": flip, "selected_policy": selection})
    assert all(c["passed"] for c in controls), controls
    assert baselines[0]["passed"] and all(not b["passed"] for b in baselines[1:]), baselines
    write(TASK / "verifier_only/reference.json", exp)
    write(TASK / "controls/calibration_results.json", {"status": "CALIBRATED", "controls": controls, "variants": variants})
    write(TASK / "quality/control_plan_card.json", {"calibration_status": "CALIBRATED", "controls": controls})
    write(TASK / "quality/independent_verifier_audit.json", {"status": "PASS", "review_status": "pass", "method": "independent setup-subset-first Fraction oracle vs action-first Decimal verifier on base and five variants", "human_or_agent_review": "NOT_RUN", "scope": "automated mathematical cross-check only"})
    contract = read(data / "output_contract.json")
    write(TASK / "quality/contract_audit.json", {"task_version": "1.0.0", "status": "PASS", "canonical_outputs": contract,
        "checks": [{"output": "outputs/" + name, "schema_declared": True} for name in ("plan.json", "decision.json", "route.tsv", "provenance.json", "audit.md")],
        "mutation_matrix": controls})
    # Recalibration preserves target records; old results remain tied to their freeze hashes.
    results_path = TASK / "quality/model_trial_results.json"
    old = read(results_path) if results_path.exists() else {}
    records = baselines + [r for r in old.get("records", []) if r.get("strategy") == "target_model"]
    status = old.get("target_model_status", "NOT_RUN")
    write(results_path, {"task_id": TASK.name, "status": "BASELINES_COMPLETE", "target_model_status": status, "records": records})
    write(TASK / "quality/model_trial_card.json", {"task_id": TASK.name, "status": "BASELINES_COMPLETE", "target_model_status": status,
        "strategies": ["reference_solution", "simple_legal_baseline", "always_abstain", "template_or_keyword", "target_model"], "run_records": records})
    sop = read(TASK / "quality/sop_card.json"); sop.update({"control_status": "CALIBRATED", "independent_verifier_status": "AUTOMATED_CROSSCHECK_PASS"}); write(TASK / "quality/sop_card.json", sop)
    freeze_paths = [TASK / "instruction.md", TASK / "task.yaml", TASK / "verifier.py", TASK / "quality/contract_audit.json", TASK / "controls/calibration_results.json", *sorted(data.rglob("*.json"))]
    write(TASK / "quality/pretrial_freeze.json", {"task_version": "1.0.0", "files": {p.relative_to(TASK).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in freeze_paths}})
    print(json.dumps({"status": "CALIBRATED", "controls": len(controls), "legal_policy_count": len(verifier.enumerate_policies(data)), "winner": exp["winner"], "variants": variants}, indent=2))


if __name__ == "__main__":
    main()
