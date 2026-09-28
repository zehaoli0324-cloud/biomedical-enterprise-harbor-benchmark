#!/usr/bin/env python3
"""Calibrate context-stratified evidence decisions and information-gain controls."""
from __future__ import annotations

import argparse
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
TASK = ROOT / "benchmarks/eb013-cross-context-evidence-portfolio-005"


def read(path): return json.loads(path.read_text())
def write(path, value): path.parent.mkdir(parents=True, exist_ok=True); path.write_text(json.dumps(value, indent=2) + "\n")


def verifier():
    spec = importlib.util.spec_from_file_location("cross_context_verifier", TASK / "verifier.py")
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module); return module


def independent(data):
    rules, evidence, options = (read(data / f) for f in ("rules.json", "evidence.json", "followups.json"))
    best = None; best_by_option_count = []
    for size in range(len(options["options"]) + 1):
        for ids in itertools.combinations([row["option_id"] for row in options["options"]], size):
            selected = set(ids); rows = list(evidence["baseline"]); cost = Fraction(0)
            for option in options["options"]:
                if option["option_id"] not in selected: continue
                cost += Fraction(str(option["cost"]))
                if option["kind"] == "add": rows.append({**option["evidence"], "source": option["option_id"]})
                else:
                    rows = [row for row in rows if row["record_id"] != option["replaces"]]
                    rows.append({**option["evidence"], "source": option["option_id"]})
            contexts = []
            for context in rules["contexts"]:
                eligible = [row for row in rows if row["context_id"] == context and row["quality"] == "pass" and row["independence"] == "independent"]
                effects = [Fraction(str(row["effect"])) for row in eligible]
                if len(effects) < rules["minimum_independent_groups"]: decision = "INSUFFICIENT"
                elif min(effects) < -Fraction(str(rules["effect_threshold"])) and max(effects) > Fraction(str(rules["effect_threshold"])): decision = "CONFLICTED"
                elif abs(sum(effects, Fraction(0)) / len(effects)) >= Fraction(str(rules["effect_threshold"])): decision = "SUPPORTED"
                else: decision = "INSUFFICIENT"
                contexts.append(decision)
            if cost <= Fraction(str(rules["followup_budget"])):
                key = (-contexts.count("SUPPORTED"), contexts.count("CONFLICTED"), contexts.count("INSUFFICIENT"), cost, tuple(ids))
                best_by_option_count.append((key, ids))
                if best is None or key < best[0]: best = (key, ids)
    return best, best_by_option_count


def reference(out, data, v, selected=None):
    exp = v.expected(data); winner = exp["winner"] if selected is None else selected
    out.mkdir(parents=True, exist_ok=True)
    write(out / "plan.json", {**v.selected(winner), "contexts": winner["contexts"] if winner else []})
    write(out / "decision.json", {**v.selected(winner), "decision": "execute_followups" if winner else "request_information", "human_review_required": True, "claim_boundary": "context_evidence_only"})
    with (out / "portfolio.tsv").open("w", newline="") as h:
        writer = csv.DictWriter(h, fieldnames=["option_id", "selected", "cost", "kind", "description"], delimiter="\t"); writer.writeheader()
        for row in read(data / "followups.json")["options"]: writer.writerow({"option_id": row["option_id"], "selected": str(row["option_id"] in (winner["selected_followups"] if winner else [])).lower(), "cost": row["cost"], "kind": row["kind"], "description": row["description"]})
    with (out / "context.tsv").open("w", newline="") as h:
        writer = csv.DictWriter(h, fieldnames=["context_id", "n_independent", "mean_effect", "min_effect", "max_effect", "decision", "pooled_shortcut_invalid"], delimiter="\t"); writer.writeheader(); writer.writerows(winner["contexts"] if winner else [])
    write(out / "provenance.json", {"input_sha256": v.hashes(data), "rules_version": read(data / "rules.json")["rules_version"], "network": "off", "deterministic": True})
    (out / "audit.md").write_text("Context decisions count independent groups, preserve conflicts and select follow-ups by supported-context gain under one budget. This is synthetic context evidence only.\n")
    shutil.copy2(TASK / "solution/solve.py", out / "planner.py")


def mutate(data, name):
    rules, evidence, options = (read(data / f) for f in ("rules.json", "evidence.json", "followups.json"))
    if name == "pooled-shortcut": evidence["baseline"][3]["effect"] = .42
    elif name == "related-repeat": rules["followup_budget"] = .8
    elif name == "independent-gain": rules["followup_budget"] = 1.0
    elif name == "budget-contraction": rules["followup_budget"] = 1.4
    elif name == "conflict-resolution": rules["followup_budget"] = 2.4
    elif name == "order-invariance":
        evidence["baseline"].reverse(); options["options"].reverse(); rules["contexts"].reverse()
    elif name == "insufficient": evidence["baseline"] = [r for r in evidence["baseline"] if r["context_id"] != "C3"]
    else: raise ValueError(name)
    for filename, value in (("rules.json", rules), ("evidence.json", evidence), ("followups.json", options)): write(data / filename, value)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--preserve-historical-trials", action="store_true")
    args = parser.parse_args()
    if (TASK / "quality/target_trial_evidence.json").exists() and not args.preserve_historical_trials:
        raise FileExistsError("Target trial preserved; pass --preserve-historical-trials for a versioned recalibration")
    v = verifier(); base = v.expected(TASK / "data"); independent_result, _ = independent(TASK / "data")
    assert tuple(base["winner"]["selected_followups"]) == independent_result[1]
    controls = []; variants = []; baselines = []
    with tempfile.TemporaryDirectory(prefix="context-portfolio-controls-") as tmp:
        out = Path(tmp) / "out"; reference(out, TASK / "data", v)
        def check(cid, expected_pass=True, kind="negative"):
            passed, errors = v.verify(out, TASK / "data"); controls.append({"control_id": cid, "kind": kind, "passed": passed == expected_pass, "verifier_passed": passed, "errors": errors})
        check("reference", True, "positive")
        for cid, filename, fn, kind in [("missing-context", "context.tsv", None, "negative"), ("pooled-only", "decision.json", lambda p: p.__setitem__("supported_count", 3), "negative"), ("wrong-independent-count", "context.tsv", None, "negative"), ("wrong-hash", "provenance.json", lambda p: p["input_sha256"].__setitem__("rules.json", "0" * 64), "insufficient_evidence"), ("claim-inflation", "decision.json", lambda p: p.__setitem__("claim_boundary", "biological_proof"), "negative")]:
            reference(out, TASK / "data", v)
            if cid == "missing-context":
                path = out / filename; path.write_text(path.read_text().splitlines()[0] + "\n")
            elif cid == "wrong-independent-count":
                path = out / filename; path.write_text(path.read_text().replace("\t2\t", "\t1\t", 1))
            elif cid == "pooled-only":
                payload = read(out / filename); payload["supported_count"] = 2; write(out / filename, payload)
            else:
                payload = read(out / filename); fn(payload); write(out / filename, payload)
            check(cid, False, kind)
        reference(out, TASK / "data", v)
        (out / "planner.py").write_text("raise SystemExit(0)\n")
        check("constant-output-planner", False, "negative")
        reference(out, TASK / "data", v)
        for name in ("pooled-shortcut", "related-repeat", "independent-gain", "budget-contraction", "conflict-resolution", "order-invariance", "insufficient"):
            changed = Path(tmp) / name; shutil.copytree(TASK / "data", changed); mutate(changed, name)
            exp = v.expected(changed); reference(out, changed, v); passed, errors = v.verify(out, changed)
            before, after = v.selected(base["winner"]), v.selected(exp["winner"])
            flip = (before["selected_followups"], before["supported_count"], before["conflicted_count"], before["insufficient_count"]) != (after["selected_followups"], after["supported_count"], after["conflicted_count"], after["insufficient_count"])
            expected_flip = name != "order-invariance"
            controls.append({"control_id": name, "kind": "invariance" if not expected_flip else "metamorphic", "passed": passed and (flip == expected_flip), "decision_flip": flip, "errors": errors}); variants.append({"name": name, "selected": after, "decision_flip": flip})
        policies = [p for p in v.enumerate_portfolios(TASK / "data") if p["eligible"]]
        for strategy in ("reference_solution", "simple_legal_baseline", "always_abstain", "template_or_keyword"):
            reference(out, TASK / "data", v)
            if strategy == "simple_legal_baseline": reference(out, TASK / "data", v, min(policies, key=lambda p: (p["total_cost"], v.objective(p))))
            if strategy == "always_abstain": payload = read(out / "decision.json"); payload["decision"] = "request_information"; write(out / "decision.json", payload)
            if strategy == "template_or_keyword": write(out / "plan.json", {})
            passed, errors = v.verify(out, TASK / "data"); baselines.append({"strategy": strategy, "passed": passed, "status": "pass" if passed else "fail", "errors": errors})
    assert all(c["passed"] for c in controls), json.dumps([c for c in controls if not c["passed"]], indent=2)
    write(TASK / "verifier_only/reference.json", base)
    write(TASK / "controls/calibration_results.json", {"status": "CALIBRATED", "controls": controls, "variants": variants})
    write(TASK / "quality/control_plan_card.json", {"status": "CALIBRATED", "calibration_status": "CALIBRATED", "controls": controls})
    write(TASK / "quality/independent_verifier_audit.json", {"status": "PASS", "review_status": "pass", "method": "Independent Fraction portfolio enumeration and context classification crosscheck against Decimal verifier.", "human_or_agent_review": "NOT_RUN"})
    write(TASK / "quality/contract_audit.json", {"status": "PASS", "canonical_outputs": read(TASK / "data/output_contract.json"), "checks": [{"output": x, "schema_declared": True} for x in ("planner.py", "plan.json", "decision.json", "portfolio.tsv", "context.tsv", "provenance.json", "audit.md")], "mutation_matrix": controls})
    for name, key in (("model_trial_results.json", "records"), ("model_trial_card.json", "run_records")): write(TASK / "quality" / name, {"task_id": TASK.name, "status": "BASELINES_COMPLETE", "target_model_status": "NOT_RUN", "strategies": [b["strategy"] for b in baselines] + ["target_model"], key: baselines})
    write(TASK / "quality/difficulty_card.json", {"task_id": TASK.name, "status": "CALIBRATED", "primary_module": "judgment_evidence_sufficiency_abstention", "secondary_modules": ["data_context_stratified_concordance", "executable_schema_preserving_replay"], "retained_module": "math_ex_ante_shared_setup", "held_out_variants": [x["name"] for x in variants] + ["budget_contraction_replay", "relationship_and_order_replay"], "legal_portfolio_count": len(v.enumerate_portfolios(TASK / "data"))})
    write(TASK / "quality/sop_card.json", {"schema_version": "enterprise_harbor_sop_card.v1", "task_id": TASK.name, "sop_version": "enterprise-harbor-sop-v1.2", "source_status": "SYNTHETIC_DISCLOSED", "contract_status": "FROZEN_V1.2.0", "control_status": "CALIBRATED", "model_trial_status": "NOT_RUN_CURRENT_VERSION", "independent_verifier_status": "AUTOMATED_CROSSCHECK_PASS", "release_status": "BLOCKED", "release_blockers": ["current-version target-model trial", "fixed-container replay", "practitioner review", "held-out target trials"]})
    frozen = [TASK / x for x in ("task.yaml", "instruction.md", "verifier.py", "quality/contract_audit.json", "controls/calibration_results.json")] + sorted((TASK / "data").glob("*.json"))
    write(TASK / "quality/pretrial_freeze.json", {"task_version": "1.2.0", "files": {str(p.relative_to(TASK)): hashlib.sha256(p.read_bytes()).hexdigest() for p in frozen}})
    print(json.dumps({"controls": len(controls), "winner": v.selected(base["winner"]), "variants": variants}, indent=2))


if __name__ == "__main__": main()
