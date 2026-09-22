#!/usr/bin/env python3
"""Crosscheck with a world-first Fraction oracle and independently defined CVaR."""
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
TASK = ROOT / "benchmarks/eb013-partial-observation-risk-004"


def read(path):
    return json.loads(path.read_text())


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n")


def load_verifier():
    spec = importlib.util.spec_from_file_location("partial_risk_verifier", TASK / "verifier.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def independent_oracle(data):
    rules, catalog, ledger = (read(data / f) for f in ("rules.json", "catalog.json", "evidence.json"))
    f = lambda x: Fraction(str(x))
    snapshots = {}
    for entry in sorted(ledger, key=lambda r: (r["published_at"], r["revision"])):
        if entry["published_at"] <= rules["decision_date"]:
            snapshots[entry["action_id"]] = entry
    worlds = sorted(rules["states"])
    best_by_probe = {}
    for probe in catalog["probes"]:
        choices = [a for a in catalog["actions"] if a["id"] in snapshots
                   and snapshots[a["id"]]["status"] == "active"
                   and not set(a["requires"]) - set(probe["capabilities"])]
        best = None
        # Start with world assignments, then impose equality for indistinguishable worlds.
        for assignments in itertools.product(choices, repeat=len(worlds)):
            mapping = {}
            for state, action in zip(worlds, assignments):
                obs = probe["observations"][state]
                if obs in mapping and mapping[obs] != action["id"]:
                    break
                mapping[obs] = action["id"]
            else:
                setup = sum((f(rules["setup_costs"][family]) for family in {a["family"] for a in assignments}), Fraction(0))
                upfront = f(probe["cost"]) + setup
                total = upfront + max(f(a["cost"]) for a in assignments)
                if upfront > f(rules["commitment_budget"]) or total > f(rules["total_budget"]):
                    continue
                losses = {}
                feasible = True
                for state, action in zip(worlds, assignments):
                    residuals = {k: max(Fraction(0), f(v) - f(snapshots[action["id"]]["reductions"][state][k]))
                                 for k, v in rules["initial_uncertainty"].items()}
                    if any(v > f(rules["critical_thresholds"][k]) for k, v in residuals.items()):
                        feasible = False
                    losses[state] = max(residuals.values())
                if not feasible:
                    continue
                risks, means = [], []
                for model in rules["probability_models"]:
                    probs = {s: f(p) for s, p in model["probabilities"].items()}
                    assert sum(probs.values()) == 1
                    # Convex threshold formula rather than the verifier's sorted-tail integration.
                    risks.append(min(t + sum(probs[s] * max(Fraction(0), loss - t) for s, loss in losses.items())
                                     / (1 - f(rules["alpha"])) for t in set(losses.values())))
                    means.append(sum(probs[s] * loss for s, loss in losses.items()))
                key = (max(risks), max(means), total, setup, probe["id"], tuple(sorted(mapping.items())))
                if best is None or key < best:
                    best = key
        best_by_probe[probe["id"]] = best
    options = [k for k in best_by_probe.values() if k is not None]
    return min(options) if options else None, best_by_probe


def crosscheck(data, verifier):
    winner, alternatives = independent_oracle(data)
    exp = verifier.expected(data)
    normalize = lambda key: tuple(float(x) if isinstance(x, Fraction) else x for x in key) if key else None
    assert (verifier.objective(exp["winner"]) if exp["winner"] else None) == normalize(winner)
    for row in exp["summaries"]:
        assert (verifier.objective(row["best_policy"]) if row["best_policy"] else None) == normalize(alternatives[row["probe_id"]])
    return exp


def reference(out, data, verifier, policy=None):
    exp = verifier.expected(data)
    winner = exp["winner"] if policy is None else policy
    out.mkdir(parents=True, exist_ok=True)
    write(out / "plan.json", {**verifier.selected(winner), "policies": exp["summaries"],
                              "risk_by_model": winner["risk_by_model"] if winner else [],
                              "evidence_resolution": exp["evidence_resolution"]})
    write(out / "decision.json", {**verifier.selected(winner), "decision": "execute_policy" if winner else "request_information",
                                  "human_review_required": True, "claim_boundary": "synthetic_planning_only"})
    with (out / "route.tsv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=verifier.ROUTE, delimiter="\t")
        writer.writeheader()
        writer.writerows(winner["states"] if winner else [])
    write(out / "provenance.json", {"input_sha256": verifier.hashes(data), "rules_version": read(data / "rules.json")["rules_version"],
                                   "network": "off", "deterministic": True})
    (out / "audit.md").write_text("Synthetic policy uses observation classes, as-of evidence, union setup and exact robust tail risk. Human review remains required.\n")
    return exp


def variant(data, name):
    rules, catalog, ledger = (read(data / f) for f in ("rules.json", "catalog.json", "evidence.json"))
    if name == "reveal-world":
        catalog["probes"][0]["observations"] = {s: s for s in rules["states"]}
    elif name == "nominal-only":
        rules["probability_models"] = rules["probability_models"][:1]
    elif name == "tail-confidence":
        rules["alpha"] = .9
    elif name == "commitment-budget":
        rules["commitment_budget"] = 2.0
    elif name == "remove-withdrawal":
        ledger = [r for r in ledger if not (r["action_id"] == "E" and r["revision"] == 2)]
    elif name == "no-feasible-policy":
        rules["total_budget"] = .1
    elif name == "order-invariance":
        catalog["probes"].reverse(); catalog["actions"].reverse(); ledger.reverse()
        rules["states"].reverse(); rules["probability_models"].reverse()
    else:
        raise ValueError(name)
    for filename, value in (("rules.json", rules), ("catalog.json", catalog), ("evidence.json", ledger)):
        write(data / filename, value)


def main():
    if (TASK / "quality/pretrial_freeze.json").exists():
        raise FileExistsError("Frozen package preserved; use a new version")
    v = load_verifier()
    exp = crosscheck(TASK / "data", v)
    controls, variants, baselines = [], [], []
    with tempfile.TemporaryDirectory(prefix="partial-risk-controls-") as tmp:
        out = Path(tmp) / "outputs"
        def record(name, should_pass, kind="negative"):
            passed, errors = v.verify(out, TASK / "data")
            controls.append({"control_id": name, "kind": kind, "passed": passed == should_pass, "verifier_passed": passed, "errors": errors})
        reference(out, TASK / "data", v)
        record("canonical-reference", True, "positive")
        for name, filename, mutate in [
            ("missing-field", "decision.json", lambda p: p.pop("robust_cvar")),
            ("hidden-world-policy", "decision.json", lambda p: p["observation_policy"].update({"W2": "B", "W3": "C"})),
            ("missing-observation", "decision.json", lambda p: p["observation_policy"].pop("b")),
            ("wrong-tail", "decision.json", lambda p: p.__setitem__("robust_cvar", .001)),
            ("claim-inflation", "decision.json", lambda p: p.__setitem__("human_review_required", False)),
            ("nonfinite", "decision.json", lambda p: p.__setitem__("worst_cost", "NaN")),
            ("wrong-hash", "provenance.json", lambda p: p["input_sha256"].__setitem__("rules.json", "0" * 64)),
            ("withdrawal-fallback", "plan.json", lambda p: next(r for r in p["evidence_resolution"] if r["action_id"] == "E").update(revision=1, status="active", usable=True)),
            ("missing-model", "plan.json", lambda p: p["risk_by_model"].pop()),
            ("duplicate-alternative", "plan.json", lambda p: p["policies"].append(p["policies"][0])),
        ]:
            reference(out, TASK / "data", v)
            payload = read(out / filename); mutate(payload); write(out / filename, payload)
            record(name, False, "insufficient_evidence" if name == "wrong-hash" else "negative")
        reference(out, TASK / "data", v)
        route = (out / "route.tsv").read_text()
        (out / "route.tsv").write_text(route + route.splitlines()[1] + "\n")
        record("duplicate-world", False)
        reference(out, TASK / "data", v)
        for filename in ("plan.json", "decision.json"):
            payload = read(out / filename); payload["setup_families"].reverse(); payload["setup_cost"] = str(payload["setup_cost"])
            if "policies" in payload:
                for field in ("policies", "risk_by_model", "evidence_resolution"):
                    payload[field].reverse()
            write(out / filename, payload)
        prov = read(out / "provenance.json"); prov["input_sha256"] = {"data/" + k: value for k, value in prov["input_sha256"].items()}
        write(out / "provenance.json", prov)
        record("declared-equivalences", True, "invariance")
        for name in ("reveal-world", "nominal-only", "tail-confidence", "commitment-budget", "remove-withdrawal", "no-feasible-policy", "order-invariance"):
            data = Path(tmp) / name
            shutil.copytree(TASK / "data", data)
            variant(data, name)
            changed = crosscheck(data, v)
            reference(out, data, v)
            passed, errors = v.verify(out, data)
            before, after = v.selected(exp["winner"]), v.selected(changed["winner"])
            flip = (before["probe_id"], before["observation_policy"]) != (after["probe_id"], after["observation_policy"])
            expected_flip = name not in {"order-invariance", "tail-confidence"}
            sensitivity_ok = name != "tail-confidence" or before["robust_cvar"] != after["robust_cvar"]
            controls.append({"control_id": name, "kind": "sensitivity" if name == "tail-confidence" else ("invariance" if not expected_flip else "metamorphic"),
                             "passed": passed and flip == expected_flip and sensitivity_ok, "decision_flip": flip, "errors": errors})
            variants.append({"name": name, "selected": after, "decision_flip": flip})
        policies = [p for p in v.enumerate_policies(TASK / "data") if p["eligible"]]
        reference(out, TASK / "data", v)
        for strategy in ("reference_solution", "simple_legal_baseline", "always_abstain", "template_or_keyword"):
            reference(out, TASK / "data", v)
            if strategy == "simple_legal_baseline":
                reference(out, TASK / "data", v, min(policies, key=lambda p: (p["worst_cost"], v.objective(p))))
            if strategy == "always_abstain":
                payload = read(out / "decision.json"); payload["decision"] = "request_information"; write(out / "decision.json", payload)
            if strategy == "template_or_keyword":
                write(out / "plan.json", {})
            passed, errors = v.verify(out, TASK / "data")
            baselines.append({"strategy": strategy, "status": "pass" if passed else "fail", "passed": passed, "errors": errors})
    failures = [c for c in controls if not c["passed"]]
    if failures:
        raise AssertionError(json.dumps(failures, indent=2))
    write(TASK / "verifier_only/reference.json", exp)
    write(TASK / "controls/calibration_results.json", {"status": "CALIBRATED", "controls": controls, "variants": variants})
    write(TASK / "quality/control_plan_card.json", {"status": "CALIBRATED", "calibration_status": "CALIBRATED", "controls": controls})
    write(TASK / "quality/independent_verifier_audit.json", {"status": "PASS", "review_status": "pass",
        "method": "Automated independent implementation: world-first Fraction enumeration and CVaR threshold minimization, versus observation-first Decimal sorted-tail integration.",
        "human_or_agent_review": "NOT_RUN", "cases": ["base"] + [r["name"] for r in variants]})
    write(TASK / "quality/contract_audit.json", {"status": "PASS", "canonical_outputs": read(TASK / "data/output_contract.json"),
        "checks": [{"output": name, "schema_declared": True} for name in ("plan.json", "route.tsv", "decision.json", "provenance.json", "audit.md")],
        "mutation_matrix": controls[:13]})
    for filename, key in (("model_trial_results.json", "records"), ("model_trial_card.json", "run_records")):
        write(TASK / "quality" / filename, {"task_id": TASK.name, "status": "BASELINES_COMPLETE", "target_model_status": "NOT_RUN",
              "strategies": [r["strategy"] for r in baselines] + ["target_model"], key: baselines})
    write(TASK / "quality/difficulty_card.json", {"task_id": TASK.name, "status": "CALIBRATED",
        "primary_module": "horizon_observation_nonanticipativity",
        "secondary_modules": ["math_distributionally_robust_cvar", "retrieval_asof_tombstone_resolution"],
        "retained_module": "math_ex_ante_shared_setup", "held_out_variants": [r["name"] for r in variants[:5]],
        "target_held_out_status": "NOT_RUN", "legal_policy_count": len(v.enumerate_policies(TASK / "data"))})
    write(TASK / "quality/sop_card.json", {"schema_version": "enterprise_harbor_sop_card.v1", "task_id": TASK.name,
        "sop_version": "enterprise-harbor-sop-v1.2", "source_status": "SYNTHETIC_DISCLOSED", "contract_status": "FROZEN_V1.0.0",
        "control_status": "CALIBRATED", "model_trial_status": "NOT_RUN", "independent_verifier_status": "AUTOMATED_CROSSCHECK_PASS",
        "release_status": "BLOCKED", "release_blockers": ["target-model trial", "fixed-container replay", "practitioner review", "held-out target trials"]})
    frozen = [TASK / p for p in ("task.yaml", "instruction.md", "verifier.py", "quality/contract_audit.json", "controls/calibration_results.json")]
    frozen += sorted((TASK / "data").glob("*.json"))
    write(TASK / "quality/pretrial_freeze.json", {"task_version": "1.0.0", "files": {str(p.relative_to(TASK)): hashlib.sha256(p.read_bytes()).hexdigest() for p in frozen}})
    print(json.dumps({"controls": len(controls), "winner": v.selected(exp["winner"]), "variants": variants}, indent=2))


if __name__ == "__main__":
    main()
