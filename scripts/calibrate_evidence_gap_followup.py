"""Pretrial artifact controls and independent input-variant checks for EB014."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import shutil
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TASK = ROOT / "benchmarks/eb014-evidence-gap-followup-001"


def read(path):
    return json.loads(path.read_text())


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n")


def module_from(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def verifier():
    return module_from(TASK / "verifier.py", "eb014_verifier")


def reference(out, data, module):
    exp = module.expected(data)
    for name, value in exp.items():
        write(out / name, value)
    (out / "audit.md").write_text(
        "Current evidence is distinct from hypothetical measurements. The replicate quorum "
        "is an unresolved blocker; duplicate reports are one independent group. "
        "The bridge only addresses its registered target population. Negative acceptance "
        "results can close the research question but cannot establish an opposite causal claim. "
        "All branches share the budget. Human review remains required; this plan is not experimental proof.\n"
    )
    return exp


def calibrate():
    module = verifier()
    audit = module_from(ROOT / "scripts/audit_evidence_gap_oracle.py", "independent_eb014")
    exp = module.expected(TASK / "data")
    oracle = audit.solve(TASK / "data")
    assert oracle["policy"] == exp["research_plan.json"]["policy"]
    assert oracle["objective"] == exp["research_plan.json"]["objective"]
    controls = []

    def first(values, key):
        return next(r for r in values if r["id"] == key)

    mutations = [
        ("claim-ceiling-inflation", "claim_ledger.json", lambda p: p.__setitem__("claim_ceiling", "causal")),
        ("duplicate-quorum", "claim_ledger.json", lambda p: first(p["premises"], "P-REPRO")["positive_groups"].append("G-B1")),
        ("archived-source-inclusion", "claim_ledger.json", lambda p: first(p["observations"], "O-3").__setitem__("included", True)),
        ("wrong-effect", "claim_ledger.json", lambda p: first(p["observations"], "O-2").__setitem__("effect", 99)),
        ("scope-inflation", "claim_ledger.json", lambda p: first(p["claims"], "C-DESC").__setitem__("scope", "target_population")),
        ("future-action", "research_plan.json", lambda p: p["policy"].__setitem__("action", "A-FUTURE")),
        ("overspend", "research_plan.json", lambda p: p["objective"].__setitem__("worst_cost", 6)),
        ("wrong-objective", "research_plan.json", lambda p: p["objective"].__setitem__("worst_resolved_weight", 99)),
        ("missing-feedback-state", "research_plan.json", lambda p: p["policy"]["branches"].pop("inconsistent")),
        ("illegal-conflict-continuation", "research_plan.json", lambda p: p["policy"]["branches"]["inconsistent"].__setitem__("action", "A-BRIDGE")),
        ("future-result-as-current", "claim_ledger.json", lambda p: first(p["claims"], "C-TRANSPORT").__setitem__("allowed", True)),
        ("missing-leaf", "adaptive_update.json", lambda p: p["leaves"].pop()),
        ("duplicate-leaf", "adaptive_update.json", lambda p: p["leaves"].append(copy.deepcopy(p["leaves"][0]))),
        ("unregistered-leaf", "adaptive_update.json", lambda p: p["leaves"].append(dict(p["leaves"][0], id="unexpected"))),
        ("not-hypothetical", "adaptive_update.json", lambda p: p.__setitem__("hypothetical", False)),
        ("null-cost", "adaptive_update.json", lambda p: p["leaves"][0].__setitem__("cost", None)),
        ("boolean-cost", "adaptive_update.json", lambda p: p["leaves"][0].__setitem__("cost", True)),
        ("nan-effect", "claim_ledger.json", lambda p: p["observations"][0].__setitem__("effect", float("nan"))),
        ("wrong-hash", "provenance.json", lambda p: p["input_sha256"].__setitem__("rules.json", "0" * 64)),
        ("missing-field", "claim_ledger.json", lambda p: p.pop("claim_ceiling")),
        ("invalid-document-type", "claim_ledger.json", lambda p: None),
    ]
    with tempfile.TemporaryDirectory(prefix="eb014-controls-") as tmp:
        out = Path(tmp) / "outputs"
        reference(out, TASK / "data", module)
        passed, errors = module.verify(out, TASK / "data")
        assert passed, errors
        controls.append({"id": "reference", "expected": True, "passed": passed})
        for name, filename, mutate in mutations:
            reference(out, TASK / "data", module)
            payload = read(out / filename)
            if name == "invalid-document-type":
                payload = None
            else:
                mutate(payload)
            write(out / filename, payload)
            passed, errors = module.verify(out, TASK / "data")
            assert not passed, name
            controls.append({"id": name, "expected": False, "passed": passed, "errors": errors})
        reference(out, TASK / "data", module)
        (out / "claim_ledger.json").write_text('{"premises": [], "premises": []}')
        passed, errors = module.verify(out, TASK / "data")
        assert not passed
        controls.append({"id": "duplicate-json-key", "expected": False, "passed": passed, "errors": errors})
        reference(out, TASK / "data", module)
        def equivalent(value):
            if isinstance(value, dict):
                return {key: equivalent(v) for key, v in reversed(list(value.items()))}
            if isinstance(value, list):
                if value and isinstance(value[0], dict) and "id" in value[0]:
                    return {r["id"]: equivalent({k: v for k, v in r.items() if k != "id"}) for r in reversed(value)}
                return value
            if type(value) in (int, float):
                return str(value)
            return value
        for filename in exp:
            write(out / filename, equivalent(read(out / filename)))
        provenance = read(out / "provenance.json")
        provenance["input_sha256"] = {"data/" + k: v for k, v in provenance["input_sha256"].items()}
        write(out / "provenance.json", provenance)
        passed, errors = module.verify(out, TASK / "data")
        assert passed, errors
        controls.append({"id": "keyed-rows-order-numeric-prefix-equivalence", "expected": True, "passed": passed})

        variants = []
        changes = [
            ("budget-contraction", "rules.json", lambda p: p.__setitem__("budget", 1)),
            ("archived-source-restored", "sources.json", lambda p: first(p, "E-BATCH-2").__setitem__("status", "current")),
            ("bridge-scope-repair", "sources.json", lambda p: first(p, "E-WRONG-BRIDGE").__setitem__("scope", "target_population")),
            ("independence-group-merge", "actions.json", lambda p: first(p, "A-REPLICATE").__setitem__("independence_group", "G-B1")),
            ("future-action-available", "actions.json", lambda p: first(p, "A-FUTURE").__setitem__("available_on", "2026-09-01")),
            ("measurement-threshold", "evidence.json", lambda p: first(p["premises"], "P-REPRO").__setitem__("min_effect", 0.5)),
            ("row-order", "sources.json", lambda p: p.reverse()),
            ("feedback-renamed", "feedback.json", lambda p: first(p["replication"], "consistent").__setitem__("id", "replication_positive")),
        ]
        for name, filename, change in changes:
            data = Path(tmp) / name
            shutil.copytree(TASK / "data", data)
            payload = read(data / filename)
            change(payload)
            write(data / filename, payload)
            actual = module.expected(data)
            independent = audit.solve(data)
            assert actual["research_plan.json"]["policy"] == independent["policy"], name
            assert actual["research_plan.json"]["objective"] == independent["objective"], name
            changed = independent["policy"] != oracle["policy"]
            if name == "row-order":
                assert not changed
            elif name != "feedback-renamed":
                assert changed, name
            reference(out, data, module)
            passed, errors = module.verify(out, data)
            assert passed, (name, errors)
            variants.append({"id": name, "oracle_agreement": True, "policy_changed": changed,
                             "classification": "invariance" if name == "row-order" else "label_equivalence" if name == "feedback-renamed" else "decision_flip",
                             "policy": independent["policy"], "objective": independent["objective"]})
    return exp, {"status": "PASS", "controls": controls, "variants": variants, "candidate_count": oracle["candidate_count"]}


def main():
    existing_trials = [TASK / "quality/model_trial_results.json", TASK / "quality/target_trial_evidence.json"]
    if any(path.exists() for path in existing_trials):
        raise RuntimeError("Trial evidence exists: use calibrate() for read-only checks; version changes before refreezing.")
    exp, results = calibrate()
    write(TASK / "verifier_only/reference.json", exp)
    write(TASK / "controls/calibration_results.json", results)
    write(TASK / "quality/contract_audit.json", {
        "status": "PASS", "canonical_contract": "data/output_contract.json",
        "controls": results["controls"], "prose_review": "NOT_RUN",
    })
    write(TASK / "quality/independent_verifier_audit.json", {
        "status": "AUTOMATED_CROSSCHECK_PASS", "human_review": "NOT_RUN",
        "method": "Recursive Decimal contingent-tree enumeration vs independent Fraction two-stage Cartesian-product enumeration; independent evidence and claim recomputation.",
        "oracle_script": "scripts/audit_evidence_gap_oracle.py", "variants": results["variants"],
    })
    write(TASK / "quality/readiness.json", {
        "status": "PRETRIAL_VALIDATED", "target_model_trial": "NOT_RUN",
        "cross_domain_transfer": "NOT_RUN", "human_scientific_review": "NOT_RUN",
        "isolated_container_replay": "NOT_RUN", "release_ready": False,
        "primary_module": "research_minimum_additional_evidence",
        "secondary_modules": ["judgment_claim_transportability_boundary", "horizon_adaptive_research_priority"],
        "supporting_modules": ["retrieval_independence_quorum"],
        "difficulty_claim": "No target-model difficulty claim until frozen trial and error attribution.",
    })
    paths = [TASK / "instruction.md", TASK / "task.yaml", TASK / "scenario-card.yaml",
             TASK / "verifier.py", *sorted((TASK / "data").glob("*.json")),
             TASK / "controls/calibration_results.json", TASK / "tests/test_verifier.py"]
    authoring = [ROOT / "scripts/audit_evidence_gap_oracle.py", Path(__file__)]
    write(TASK / "quality/pretrial_freeze.json", {
        "version": "1.0.0",
        "sha256": {p.relative_to(TASK).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
        "authoring_sha256": {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in authoring},
    })
    print(json.dumps({"status": "PASS", "controls": len(results["controls"]), "variants": len(results["variants"]),
                      "policy": exp["research_plan.json"]["policy"], "target_model_trial": "NOT_RUN"}, indent=2))


if __name__ == "__main__":
    main()
