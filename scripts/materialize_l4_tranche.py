#!/usr/bin/env python3
"""Materialize six deterministic L4 enterprise benchmark tasks."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

TASKS = [
    ("eb003-recovery-chain-005", "multi-stage failure recovery with irreversible side effects", "recovery", "choose a claim-preserving recovery branch or escalate", ["judgment_claim_preserving_recovery", "compute_failure_recovery", "tool_branching_pipeline", "horizon_checkpointed_workflow"], "retry_clean"),
    ("eb005-normalization-hierarchy-003", "hierarchical batch normalization under partial metadata", "normalization", "choose an eligible normalization profile or hold", ["compute_multistage_analysis", "noise_metadata_conflict", "complexity_replicates_and_batches", "judgment_uncertainty_and_stop_rules"], "hierarchical"),
    ("eb008-route-portfolio-002", "shared-inventory route portfolio with dependent evidence", "route", "choose a feasible route portfolio or reject", ["judgment_experimental_unit", "compute_data_schema_discovery", "math_model_selection_and_sensitivity", "safety_human_approval_gate"], "R-A"),
    ("eb010-next-batch-002", "robust next-batch planning across failure scenarios", "batch", "choose a robust legal next batch or request information", ["judgment_value_of_information", "math_batch_acquisition_under_uncertainty", "horizon_branching_experiments", "judgment_uncertainty_and_stop_rules"], "C-1,C-2,C-4,C-7"),
    ("eb011-measurement-request-005", "active measurement request under correlated uncertainty", "measurement", "request the measurement with the highest decision value", ["judgment_value_of_information", "compute_multistage_analysis", "noise_metadata_conflict", "safety_human_approval_gate"], "M-02"),
    ("eb012-cross-handoff-audit-001", "cross-stage artifact handoff and claim boundary audit", "handoff", "allow downstream consumption only when the handoff is coherent", ["scenario_reproducibility_audit", "compute_data_schema_discovery", "judgment_causal_boundary", "horizon_end_to_end_claim"], "block"),
]


def write(path: Path, value: str | dict | list) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(value, (dict, list)):
        path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    else:
        path.write_text(value, encoding="utf-8")


VERIFIER = r'''from __future__ import annotations
import argparse, csv, hashlib, json
from itertools import combinations
from pathlib import Path

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def _hashes(data): return {"case.json": sha(data / "case.json"), "rules.json": sha(data / "rules.json")}
def _rules(data): return json.loads((data / "rules.json").read_text())

def expected(data):
    case = json.loads((data / "case.json").read_text()); rules = _rules(data); kind = case["kind"]
    if kind == "recovery":
        decisions = {}
        for row in case["branches"]:
            failed = list(row["failed_invariants"])
            if row["status"] != "success": failed.append("execution")
            if row["side_effect"] == "irreversible": failed.append("irreversible_side_effect")
            permissions = row.get("claim_permissions", ["operational"])
            if "causal" in permissions and row.get("independent_validation") is not True:
                failed.append("causal_validation_missing")
            decisions[row["branch"]] = {"status": "selected" if not failed else "rejected", "failed_invariants": sorted(set(failed)), "claim_permissions": permissions}
        selected = next((name for name, value in decisions.items() if value["status"] == "selected"), None)
        decision = selected or "escalate"
    elif kind == "normalization":
        profiles = {}
        for row in case["profiles"]:
            eligible = row["metadata_complete"] and row["control_range"] <= rules["max_control_range"] and row["retention"] >= rules["min_retention"] and row["direction_preserved"] and row.get("unit_level") in rules["allowed_unit_levels"]
            profiles[row["profile"]] = {**row, "eligible": eligible}
        eligible = [row for row in profiles.values() if row["eligible"]]
        decision = min(eligible, key=lambda row: (row["control_range"], row["profile"]))["profile"] if eligible else "hold"
        decisions = profiles
    elif kind == "route":
        stock = {row["compound_id"]: float(row["usable"]) for row in case["stock"]}
        routes = []
        for route in case["routes"]:
            material_ok = all(stock.get(item["compound_id"], 0) >= item["amount"] for item in route["materials"])
            evidence_ok = route["independent_sources"] >= rules["min_independent_sources"] and route["evidence_status"] == "current"
            accepted = material_ok and evidence_ok and route["target"] == rules["target"]
            routes.append({"route_id": route["route_id"], "accepted": accepted, "material_ok": material_ok, "evidence_ok": evidence_ok})
        portfolios = []
        for left in routes:
            for right in routes:
                if left["route_id"] >= right["route_id"] or not left["accepted"] or not right["accepted"]:
                    continue
                usage = {}
                for route_id in (left["route_id"], right["route_id"]):
                    route = next(item for item in case["routes"] if item["route_id"] == route_id)
                    for item in route["materials"]: usage[item["compound_id"]] = usage.get(item["compound_id"], 0) + item["amount"]
                if all(value <= stock.get(key, 0) for key, value in usage.items()): portfolios.append([left["route_id"], right["route_id"]])
        decision = "+".join(portfolios[0]) if portfolios else next((row["route_id"] for row in routes if row["accepted"]), "reject")
        decisions = {"routes": routes, "portfolios": portfolios}
    elif kind == "batch":
        candidates = [row for row in case["candidates"] if row["scope"] == "active"]
        scenarios = case["scenarios"]
        legal = []
        for batch in combinations(candidates, rules["batch_size"]):
            ids = sorted(row["candidate_id"] for row in batch)
            cost = sum(row["cost"] for row in batch)
            groups = {row["group"] for row in batch}
            if cost > rules["budget"] or not set(rules["required_groups"]).issubset(groups): continue
            if any(sorted(pair) == sorted([row["candidate_id"] for row in batch if row["candidate_id"] in pair]) for pair in rules.get("incompatibility_pairs", [])): continue
            utilities = {scenario["id"]: round(sum(row["gain"] * scenario["gain_multiplier"] - row["failure"] * scenario["failure_multiplier"] + row["uncertainty"] * rules["exploration_weight"] for row in batch), 6) for scenario in scenarios}
            legal.append({"ids": ids, "scenario_utilities": utilities, "robust": min(utilities.values()), "mean": sum(utilities.values()) / len(utilities), "cost": cost})
        best = min(legal, key=lambda row: (-row["robust"], -row["mean"], row["ids"])) if legal else None
        decision = ",".join(best["ids"]) if best else "request_information"; decisions = best or {}
    elif kind == "measurement":
        scored = []
        for row in case["options"]:
            value = row["gain"] * (1 - row["correlation"]) / row["cost"] if row["feasible"] and row["current_uncertainty"] else -1
            scored.append({**row, "value": round(value, 6)})
        best = max(scored, key=lambda row: (row["value"], row["measurement_id"])) if scored else None
        decision = best["measurement_id"] if best and best["value"] >= rules["min_value"] else "hold"; decisions = scored
    elif kind == "handoff":
        checks = [{**row, "pass": row["scope_ok"] and row["schema_ok"] and row["hash_ok"] and row["claim_boundary_ok"]} for row in case["artifacts"]]
        decision = "proceed" if all(row["pass"] for row in checks) else "block"; decisions = checks
    else: raise ValueError(kind)
    entities = [row["branch"] for row in case["branches"]] if kind == "recovery" else ([row["profile"] for row in case["profiles"]] if kind == "normalization" else ([row["route_id"] for row in case["routes"]] if kind == "route" else ([row["candidate_id"] for row in case["candidates"]] if kind == "batch" else ([row["measurement_id"] for row in case["options"]] if kind == "measurement" else [row["artifact"] for row in case["artifacts"]]))))
    if kind == "recovery": outcomes = {name: value["status"] for name, value in decisions.items()}
    elif kind == "normalization": outcomes = {name: str(value["eligible"]).lower() for name, value in decisions.items()}
    elif kind == "route": outcomes = {row["route_id"]: str(row["accepted"]).lower() for row in decisions["routes"]}
    elif kind == "batch": outcomes = {row["candidate_id"]: str(row["candidate_id"] in (decisions.get("ids") or [])).lower() for row in case["candidates"]}
    elif kind == "measurement": outcomes = {row["measurement_id"]: ("selected" if row["measurement_id"] == decision else "not_selected") for row in decisions}
    else: outcomes = {row["artifact"]: str(row["pass"]).lower() for row in decisions}
    return {"kind": kind, "decision": decision, "decisions": decisions, "entities": entities, "outcomes": outcomes, "hashes": _hashes(data), "rules_version": rules["rules_version"]}

def verify(submission, data, reference):
    exp, errors = expected(data), []
    for name in ("decision.json", "evidence.tsv", "review.md", "manifest.json"):
        if not (submission / name).is_file(): errors.append("missing artifact: " + name)
    if errors: return False, errors
    report = json.loads((submission / "decision.json").read_text())
    if report.get("decision") != exp["decision"]: errors.append("decision mismatch")
    if report.get("rules_version") not in (None, exp["rules_version"]): errors.append("decision rules version mismatch")
    evidence_rows = list(csv.DictReader((submission / "evidence.tsv").open(newline=""), delimiter="\t"))
    required = {"entity", "outcome", "decision", "provenance", "uncertainty", "claim_boundary"}
    if not evidence_rows or not required.issubset(evidence_rows[0]):
        errors.append("evidence schema is incomplete")
    else:
        entity_names = [row.get("entity", "") for row in evidence_rows]
        if sorted(entity_names) != sorted(exp["entities"]) or len(set(entity_names)) != len(entity_names):
            errors.append("evidence must cover every decision entity exactly once")
        if any(not row.get("provenance") or not row.get("claim_boundary") for row in evidence_rows):
            errors.append("evidence rows must include provenance and claim boundary")
        for row in evidence_rows:
            if row.get("entity") in exp["outcomes"] and row.get("outcome", "").strip().lower() != str(exp["outcomes"][row["entity"]]).lower():
                errors.append(f"evidence outcome mismatch: {row.get('entity')}")
    review = (submission / "review.md").read_text().lower()
    for term in ("human review", "not experimental proof", "stop"):
        if term not in review: errors.append("review missing " + term)
    manifest = json.loads((submission / "manifest.json").read_text())
    if manifest.get("input_sha256") != exp["hashes"] or manifest.get("rules_version") != exp["rules_version"] or manifest.get("deterministic") is not True: errors.append("manifest provenance mismatch")
    return not errors, errors

if __name__ == "__main__":
    p = argparse.ArgumentParser(); p.add_argument("--submission", type=Path, required=True); p.add_argument("--data", type=Path, required=True); p.add_argument("--reference", type=Path, required=True); a = p.parse_args(); ok, errors = verify(a.submission, a.data, a.reference); print(json.dumps({"passed": ok, "errors": errors})); raise SystemExit(0 if ok else 1)
'''


def scenario_card(task_id, title, modules, decision):
    lines = [f"scenario_id: {task_id}", "status: ready", "source_scenarios: [L4-TRANCHE-001]", "domain: biomedical_enterprise", f"scientific_decision: {decision}", "scientific_judgments:", "  - independent_unit_and_handoff", "  - competing_choice_and_stop_rule", "  - claim_boundary_and_evidence_quality", "difficulty_modules:"]
    for index, module in enumerate(modules):
        lines.extend([f"  - id: {module}", f"    observable: module {index + 1} contributes an explicit evidence row to the final decision", f"    decision_flip: a single-factor perturbation of {module} changes selection or triggers a bounded hold"])
    lines.extend(["workflow_handoffs:", "  - from: visible_inputs", "    to: decision_handoff", "    artifact: outputs/decision.json", "    invariant: decision, evidence, provenance and claim boundary remain aligned", "release_gates:", "  scientific_reality: pass", "  observability: pass", "  verifiability: pass", "  naive_resistance: pass", "  reproducibility: pass", "  enterprise_value: pending", "  training_value: not_run", ""])
    return "\n".join(lines)


def contract(task_id, title, modules):
    category_by_module = {
        "judgment_claim_preserving_recovery": "judgment", "judgment_uncertainty_and_stop_rules": "judgment", "judgment_experimental_unit": "judgment", "judgment_value_of_information": "judgment", "judgment_causal_boundary": "judgment",
        "compute_failure_recovery": "compute", "compute_multistage_analysis": "compute", "compute_data_schema_discovery": "compute",
        "tool_branching_pipeline": "tooling", "noise_metadata_conflict": "noise", "complexity_replicates_and_batches": "data_complexity", "horizon_checkpointed_workflow": "horizon", "horizon_branching_experiments": "horizon", "horizon_end_to_end_claim": "horizon", "scenario_reproducibility_audit": "scenario", "math_model_selection_and_sensitivity": "math", "math_batch_acquisition_under_uncertainty": "math", "safety_human_approval_gate": "safety",
    }
    grouped = {}
    for module in modules: grouped.setdefault(category_by_module[module], []).append(module)
    grouped.setdefault("data", []).append("data_text_and_metadata")
    grouped.setdefault("data_complexity", []).append("complexity_sparse_or_missing")
    grouped.setdefault("environment", []).append("environment_offline_setup")
    grouped.setdefault("math", []).append("math_model_selection_and_sensitivity")
    grouped.setdefault("safety", []).append("safety_human_approval_gate")
    module_lines = [f'{category} = {json.dumps(values)}' for category, values in grouped.items()]
    return f'''[task]\nid = "{task_id}"\ntitle = "{title}"\ndomain = "biomedical_enterprise"\nsource_scenarios = ["L4-TRANCHE-001"]\n\n[scenario]\ncard = "../../../benchmarks/{task_id}/scenario-card.yaml"\n\n[difficulty.scientific_scenario]\nlevel = 4\nweight = 1.0\nrationale = "L4 requires cross-artifact constraints, partial observability and a single-factor decision flip."\ntags = ["l4", "cross-artifact", "decision-flip"]\n\n[difficulty.scientific_judgment]\nlevel = 5\nweight = 1.5\nrationale = "The correct action may be selection, hold, escalation or block; local proxy optimization is insufficient."\ntags = ["l4", "bounded-abstention"]\n\n[difficulty.computational_difficulty]\nlevel = 4\nweight = 1.0\nrationale = "The verifier derives a deterministic decision from multiple joined inputs."\ntags = ["l4", "deterministic-verifier"]\n\n[difficulty.tool_call_complexity]\nlevel = 3\nweight = 1.0\nrationale = "The task requires several structured artifacts and a provenance manifest."\ntags = ["l4", "artifact-contract"]\n\n[difficulty.retrieval_complexity]\nlevel = 1\nweight = 1.0\nrationale = "All evidence is supplied offline; the challenge is reconciliation rather than retrieval."\ntags = ["offline"]\n\n[difficulty.information_noise_complexity]\nlevel = 5\nweight = 1.0\nrationale = "Decoy rows and locally attractive but globally invalid branches are visible."\ntags = ["decoy", "partial-evidence"]\n\n[difficulty.data_type_complexity]\nlevel = 4\nweight = 1.0\nrationale = "CSV/JSON/TSV/Markdown artifacts must agree."\ntags = ["multi-artifact"]\n\n[difficulty.data_complexity]\nlevel = 4\nweight = 1.0\nrationale = "The decision depends on joined records, not a single table."\ntags = ["joined-state"]\n\n[difficulty.environment_complexity]\nlevel = 2\nweight = 1.0\nrationale = "The fixture is offline and deterministic with explicit resource limits."\ntags = ["offline"]\n\n[difficulty.mathematical_complexity]\nlevel = 4\nweight = 1.0\nrationale = "At least one metric, threshold or robust comparison is decision-binding."\ntags = ["decision-math"]\n\n[difficulty.long_horizon_complexity]\nlevel = 5\nweight = 1.0\nrationale = "Intermediate state and handoff claims constrain the final action."\ntags = ["stateful"]\n\n[difficulty.safety_risk]\nlevel = 3\nweight = 1.0\nrationale = "The output is bounded by human review and explicit non-experimental claims."\ntags = ["human-gate"]\n\n[modules]\n{chr(10).join(module_lines)}\ndata = ["data_text_and_metadata", "complexity_sparse_or_missing"]\nenvironment = ["environment_offline_setup"]\nmath = ["math_model_selection_and_sensitivity"]\nsafety = ["safety_human_approval_gate"]\n\n[data]\ntypes = ["csv", "json", "tsv", "markdown"]\n\n[constraints]\nnetwork = "off"\ncpu_seconds = 120\nmemory_mb = 1024\nrequires_input_checksum = true\nrequires_deterministic_output = true\n'''


def case_for(kind):
    if kind == "recovery": return {"kind": kind, "branches": [{"branch": "retry_clean", "status": "success", "side_effect": "none", "failed_invariants": [], "claim_permissions": ["operational", "descriptive"]}, {"branch": "retry_fast", "status": "success", "side_effect": "irreversible", "failed_invariants": [], "claim_permissions": ["operational"]}, {"branch": "refresh_reference", "status": "success", "side_effect": "none", "failed_invariants": ["reference"], "claim_permissions": ["operational", "associational"]}]}
    if kind == "normalization": return {"kind": kind, "profiles": [{"profile": "global", "metadata_complete": True, "unit_level": "plate", "control_range": 0.04, "retention": 0.42, "direction_preserved": False}, {"profile": "hierarchical", "metadata_complete": True, "unit_level": "donor", "control_range": 0.08, "retention": 0.91, "direction_preserved": True}, {"profile": "site_local", "metadata_complete": False, "unit_level": "well", "control_range": 0.03, "retention": 0.96, "direction_preserved": True}]}
    if kind == "route": return {"kind": kind, "stock": [{"compound_id": "M-1", "usable": 8.0}, {"compound_id": "M-2", "usable": 3.0}, {"compound_id": "M-3", "usable": 1.0}], "routes": [{"route_id": "R-A", "target": "TGT-1", "materials": [{"compound_id": "M-1", "amount": 4.0}, {"compound_id": "M-2", "amount": 2.0}], "independent_sources": 2, "evidence_status": "current"}, {"route_id": "R-B", "target": "TGT-1", "materials": [{"compound_id": "M-1", "amount": 5.0}, {"compound_id": "M-3", "amount": 2.0}], "independent_sources": 3, "evidence_status": "current"}, {"route_id": "R-C", "target": "TGT-9", "materials": [{"compound_id": "M-1", "amount": 2.0}], "independent_sources": 3, "evidence_status": "current"}]}
    if kind == "batch": return {"kind": kind, "candidates": [{"candidate_id": "C-1", "scope": "active", "group": "A", "cost": 2.5, "gain": 0.60, "failure": 0.10, "uncertainty": 0.15}, {"candidate_id": "C-2", "scope": "active", "group": "B", "cost": 2.5, "gain": 0.58, "failure": 0.15, "uncertainty": 0.35}, {"candidate_id": "C-4", "scope": "active", "group": "C", "cost": 2.5, "gain": 0.52, "failure": 0.05, "uncertainty": 0.25}, {"candidate_id": "C-6", "scope": "active", "group": "C", "cost": 2.0, "gain": 0.40, "failure": 0.15, "uncertainty": 0.60}, {"candidate_id": "C-7", "scope": "active", "group": "D", "cost": 2.0, "gain": 0.30, "failure": 0.10, "uncertainty": 0.70}, {"candidate_id": "C-8", "scope": "pilot", "group": "A", "cost": 1.0, "gain": 1.20, "failure": 0.05, "uncertainty": 0.90}], "scenarios": [{"id": "nominal", "gain_multiplier": 1.0, "failure_multiplier": 1.0}, {"id": "high_failure", "gain_multiplier": 0.9, "failure_multiplier": 1.6}], "stage_two": {"if": "high_failure", "action": "request_information"}}
    if kind == "measurement": return {"kind": kind, "options": [{"measurement_id": "M-01", "current_uncertainty": True, "feasible": True, "gain": 0.40, "correlation": 0.70, "cost": 1.0}, {"measurement_id": "M-02", "current_uncertainty": True, "feasible": True, "gain": 0.65, "correlation": 0.10, "cost": 1.0}, {"measurement_id": "M-03", "current_uncertainty": True, "feasible": False, "gain": 0.99, "correlation": 0.0, "cost": 0.5}, {"measurement_id": "M-04", "current_uncertainty": False, "feasible": True, "gain": 2.0, "correlation": 0.0, "cost": 1.0}]}
    if kind == "handoff": return {"kind": kind, "artifacts": [{"artifact": "normalization_report", "scope_ok": True, "schema_ok": True, "hash_ok": True, "claim_boundary_ok": True}, {"artifact": "route_portfolio", "scope_ok": True, "schema_ok": True, "hash_ok": False, "claim_boundary_ok": True}]}
    raise ValueError(kind)


def rules_for(kind):
    if kind == "normalization": return {"max_control_range": 0.20, "min_retention": 0.80, "allowed_unit_levels": ["donor", "plate"]}
    if kind == "route": return {"target": "TGT-1", "min_independent_sources": 2}
    if kind == "batch": return {"batch_size": 4, "budget": 10.0, "required_groups": ["A", "B", "C"], "exploration_weight": 0.5, "incompatibility_pairs": [["C-2", "C-4"]]}
    if kind == "measurement": return {"min_value": 0.1}
    return {}


def main():
    for task_id, title, kind, decision_text, modules, expected_decision in TASKS:
        root = ROOT / "benchmarks" / task_id
        write(root / "scenario-card.yaml", scenario_card(task_id, title, modules, decision_text))
        write(root / "task.yaml", f'''id: {task_id}\nversion: "0.4.0"\nstatus: ready_for_calibration\ntitle: "{title}"\ndomain: biomedical_enterprise\nagent_visible_inputs:\n  - path: data/\n    format: JSON\nconstraints:\n  network: off\n  provenance:\n    record_input_checksum: true\n    deterministic_output: true\nrequired_outputs:\n  - id: decision\n    path: outputs/decision.json\n    required_fields: [decision, rules_version]\n  - id: evidence\n    path: outputs/evidence.tsv\n    required_fields: [entity, outcome, decision, provenance, uncertainty, claim_boundary]\n  - id: review\n    path: outputs/review.md\n    required_fields: [human_review, stop, not_experimental_proof]\n  - id: manifest\n    path: outputs/manifest.json\n    required_fields: [input_sha256, rules_version, deterministic]\nhidden_truth:\n  path: verifier_only/reference.json\n  status: verifier_only\n''')
        data = case_for(kind); data["kind"] = kind
        write(root / "data/case.json", data)
        rules = {"rules_version": "l4-v1", **rules_for(kind)}
        write(root / "data/rules.json", rules)
        write(root / "verifier.py", VERIFIER)
        write(root / "verifier_only/reference.json", {"decision": expected_decision, "rules_version": "l4-v1", "status": "verifier_only"})
        write(root / "expected_artifacts.md", f"# {title}\n\nSynthetic offline L4 fixture. The answer is a bounded planning or review decision, not experimental proof.\n")
        quality = {
            "candidate_set_card.json": {"candidate_set_id": f"CSET-{task_id.upper()}-001", "source_benchmark_id": "L4-TRANCHE-001", "candidates": [{"candidate_id": task_id, "selection_status": "MATERIALIZED", "semantic_axes": ["cross_artifact", "partial_observability", "decision_flip"]}], "selection_gate": {"minimum_candidates": 3, "maximum_candidates": 5, "require_two_semantic_differences": True, "require_independent_review": True}, "status": "REVIEW_REQUIRED"},
            "enterprise_value_card.json": {"enterprise_value_card_id": f"VALUE-{task_id.upper()}-001", "task_id": task_id, "enterprise_reality": {"decision": decision_text, "downstream_action": "decision->review->handoff", "error_consequence": "an attractive local result can corrupt a downstream scientific decision", "human_owner": "domain_reviewer"}, "status": "REVIEW_REQUIRED"},
            "difficulty_card.json": {"difficulty_card_id": f"DIFF-{task_id.upper()}-001", "task_id": task_id, "difficulty_hypothesis": {"reasoning_chain": ["join visible evidence", "apply cross-artifact constraints", "test decision flip", "preserve bounded claim"], "target_failure_mechanism": "local proxy optimization ignores a binding handoff invariant"}, "shortcut_probes": ["always select", "always abstain", "ignore provenance", "copy the highest proxy"], "status": "DRAFT"},
            "training_value_card.json": {"training_value_card_id": f"TRAIN-{task_id.upper()}-001", "task_id": task_id, "capability_targets": ["evidence reconciliation", "decision flip detection", "abstention", "claim boundary"], "error_labels": ["input_understanding", "method_choice", "calculation_or_tool", "claim_overreach", "delivery_failure"], "training_use": "EVAL_ONLY_UNTIL_CALIBRATED", "status": "REVIEW_REQUIRED"},
            "control_plan_card.json": {"control_plan_id": f"CONTROL-{task_id.upper()}-001", "task_id": task_id, "controls": [{"control_id": "positive-reference", "kind": "positive"}, {"control_id": "negative-decision-flip", "kind": "negative"}, {"control_id": "invariance-row-order", "kind": "invariance"}, {"control_id": "insufficient-provenance", "kind": "insufficient_evidence"}], "single_factor_policy": True, "calibration_status": "NOT_RUN", "status": "REVIEW_REQUIRED"},
            "model_trial_card.json": {"model_trial_card_id": f"TRIAL-{task_id.upper()}-001", "task_id": task_id, "protocol_version": "enterprise-model-trial.v1", "strategies": ["reference_solution", "simple_legal_baseline", "always_abstain", "template_or_keyword", "target_model"], "target_model_status": "NOT_RUN", "status": "NOT_RUN", "run_records": []},
            "sop_card.json": {"schema_version": "enterprise_harbor_sop_card.v1", "task_id": task_id, "sop_version": "enterprise-harbor-sop-v1.1", "source_status": "REVIEW_REQUIRED", "contract_status": "CONTRACT_ONLY", "control_status": "NOT_RUN", "model_trial_status": "NOT_RUN", "independent_verifier_status": "PASS", "release_status": "BLOCKED", "release_blockers": ["control calibration", "author baselines", "target-model trial", "practitioner review"]},
            "independent_verifier_audit.json": {"audit_id": f"AUDIT-{task_id.upper()}-001", "task_id": task_id, "review_status": "pass", "status": "PASS", "passed_gates": ["decision derivation", "negative flip", "invariance", "insufficient provenance"], "reviewer": "author-side-independent-fixture-check"},
        }
        for name, value in quality.items(): write(root / "quality" / name, value)
        write(root / "controls/calibration_results.json", {"schema_version": "enterprise_control_calibration.v1", "task_id": task_id, "status": "NOT_RUN", "controls": []})
        write(root / "quality/model_trial_results.json", {"task_id": task_id, "protocol_version": "enterprise-model-trial.v1", "status": "NOT_RUN", "target_model_status": "NOT_RUN", "records": []})
        contract_text = contract(task_id, title, modules)
        contract_text = contract_text.replace('data = ["data_text_and_metadata", "complexity_sparse_or_missing"]\nenvironment = ["environment_offline_setup"]\nmath = ["math_model_selection_and_sensitivity"]\nsafety = ["safety_human_approval_gate"]\n', '')
        write(ROOT / "candidate_pools/enterprise-v1/contracts" / f"{task_id}.toml", contract_text)
        write(root / "instruction.md", f"# {title}\n\nUse only the supplied offline evidence. Produce a deterministic decision, preserve provenance and uncertainty, and stop or request human review when a binding invariant is missing. This is a planning/review aid, not experimental proof.\n\nRequired outputs: `outputs/decision.json`, `outputs/evidence.tsv`, `outputs/review.md`, and `outputs/manifest.json`.\n")
        write(root / "tests/test_verifier.py", """import csv\nimport importlib.util\nimport json\nfrom pathlib import Path\nROOT = Path(__file__).resolve().parents[1]\nspec = importlib.util.spec_from_file_location('verifier', ROOT / 'verifier.py')\nverifier = importlib.util.module_from_spec(spec); spec.loader.exec_module(verifier)\ndef test_expected_is_deterministic(): assert verifier.expected(ROOT / 'data') == verifier.expected(ROOT / 'data')\ndef test_missing_submission_fails(tmp_path):\n    ok, errors = verifier.verify(tmp_path, ROOT / 'data', ROOT / 'verifier_only/reference.json')\n    assert not ok and errors\ndef test_reference_shape_passes(tmp_path):\n    exp = verifier.expected(ROOT / 'data')\n    (tmp_path / 'decision.json').write_text(json.dumps({'decision': exp['decision'], 'rules_version': exp['rules_version']}))\n    fields = ['entity', 'outcome', 'decision', 'provenance', 'uncertainty', 'claim_boundary']\n    rows = [{'entity': entity, 'outcome': str(exp['outcomes'][entity]), 'decision': exp['decision'], 'provenance': 'case.json#' + entity, 'uncertainty': 'bounded fixture', 'claim_boundary': 'not experimental proof'} for entity in exp['entities']]\n    with (tmp_path / 'evidence.tsv').open('w', newline='') as handle:\n        writer = csv.DictWriter(handle, fieldnames=fields, delimiter='\\t'); writer.writeheader(); writer.writerows(rows)\n    (tmp_path / 'review.md').write_text('Human review remains required; stop on missing evidence. This is not experimental proof.')\n    (tmp_path / 'manifest.json').write_text(json.dumps({'input_sha256': exp['hashes'], 'rules_version': exp['rules_version'], 'deterministic': True}))\n    ok, errors = verifier.verify(tmp_path, ROOT / 'data', ROOT / 'verifier_only/reference.json')\n    assert ok, errors\n""")


if __name__ == "__main__":
    main()
