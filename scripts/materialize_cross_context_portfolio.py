#!/usr/bin/env python3
"""Materialize the context-stratified evidence portfolio fixture."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TASK = ROOT / "benchmarks/eb013-cross-context-evidence-portfolio-005"


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def main():
    if (TASK / "data").exists():
        raise FileExistsError("Existing package preserved; create a new version instead")
    rules = {
        "rules_version": "context-evidence-portfolio-v1.1",
        "followup_budget": 4.4,
        "minimum_independent_groups": 2,
        "effect_threshold": 0.3,
        "contexts": ["C1", "C2", "C3", "C4", "C5"],
        "objective": ["supported_count_desc", "conflicted_count_asc", "insufficient_count_asc", "cost_asc", "sorted_followup_ids"],
        "claim_boundary": "context_evidence_only",
    }
    evidence = {"baseline": [
        {"record_id": "C1-G1", "context_id": "C1", "group_id": "G1", "independence": "independent", "quality": "pass", "effect": 0.55},
        {"record_id": "C1-G2", "context_id": "C1", "group_id": "G2", "independence": "independent", "quality": "pass", "effect": 0.45},
        {"record_id": "C2-G1", "context_id": "C2", "group_id": "G3", "independence": "independent", "quality": "pass", "effect": 0.50},
        {"record_id": "C2-G2", "context_id": "C2", "group_id": "G4", "independence": "independent", "quality": "pass", "effect": -0.42},
        {"record_id": "C3-G1", "context_id": "C3", "group_id": "G5", "independence": "independent", "quality": "pass", "effect": 0.48},
        {"record_id": "C4-G1", "context_id": "C4", "group_id": "G10", "independence": "independent", "quality": "pass", "effect": 0.22},
        {"record_id": "C4-G2", "context_id": "C4", "group_id": "G11", "independence": "independent", "quality": "pass", "effect": 0.25},
        {"record_id": "C5-G1", "context_id": "C5", "group_id": "G12", "independence": "independent", "quality": "pass", "effect": 0.51},
        {"record_id": "C5-G1R", "context_id": "C5", "group_id": "G12R", "independence": "related", "quality": "pass", "effect": 0.49},
    ]}
    followups = {"options": [
        {"option_id": "F1", "kind": "add", "cost": 1.0, "description": "new independent C3 group", "evidence": {"record_id": "F1-C3-G6", "context_id": "C3", "group_id": "G6", "independence": "independent", "quality": "pass", "effect": 0.44}},
        {"option_id": "F2", "kind": "add", "cost": 0.8, "description": "related C3 replicate", "evidence": {"record_id": "F2-C3-G5R", "context_id": "C3", "group_id": "G5R", "independence": "related", "quality": "pass", "effect": 0.46}},
        {"option_id": "F3", "kind": "add", "cost": 0.7, "description": "redundant independent C1 group", "evidence": {"record_id": "F3-C1-G7", "context_id": "C1", "group_id": "G7", "independence": "independent", "quality": "pass", "effect": 0.36}},
        {"option_id": "F4", "kind": "replace", "cost": 1.4, "description": "quality-reviewed C2 replacement", "replaces": "C2-G2", "evidence": {"record_id": "F4-C2-G8", "context_id": "C2", "group_id": "G8", "independence": "independent", "quality": "pass", "effect": 0.41}},
        {"option_id": "F5", "kind": "add", "cost": 1.2, "description": "new independent C2 group without resolving conflict", "evidence": {"record_id": "F5-C2-G9", "context_id": "C2", "group_id": "G9", "independence": "independent", "quality": "pass", "effect": 0.40}},
        {"option_id": "F6", "kind": "replace", "cost": 1.1, "description": "quality-reviewed C4 replacement that crosses the mean threshold", "replaces": "C4-G2", "evidence": {"record_id": "F6-C4-G13", "context_id": "C4", "group_id": "G13", "independence": "independent", "quality": "pass", "effect": 0.52}},
        {"option_id": "F7", "kind": "add", "cost": 0.9, "description": "new independent C5 group", "evidence": {"record_id": "F7-C5-G14", "context_id": "C5", "group_id": "G14", "independence": "independent", "quality": "pass", "effect": 0.43}},
        {"option_id": "F8", "kind": "add", "cost": 0.6, "description": "negative independent C4 row that preserves conflict", "evidence": {"record_id": "F8-C4-G15", "context_id": "C4", "group_id": "G15", "independence": "independent", "quality": "pass", "effect": -0.41}},
        {"option_id": "F9", "kind": "add", "cost": 0.5, "description": "related C5 repeat that does not satisfy independence", "evidence": {"record_id": "F9-C5-G12R2", "context_id": "C5", "group_id": "G12R2", "independence": "related", "quality": "pass", "effect": 0.47}},
    ]}
    contract = {
        "version": "1.0.0", "numeric_tolerance": 0.000001,
        "required_hash_paths": ["rules.json", "evidence.json", "followups.json", "output_contract.json"],
        "selected_fields": ["selected_followups", "total_cost", "supported_count", "conflicted_count", "insufficient_count"],
        "context_fields": ["context_id", "n_independent", "mean_effect", "min_effect", "max_effect", "decision", "pooled_shortcut_invalid"],
        "portfolio_columns": ["option_id", "selected", "cost", "kind", "description"],
        "context_columns": ["context_id", "n_independent", "mean_effect", "min_effect", "max_effect", "decision", "pooled_shortcut_invalid"],
        "equivalents": ["JSON key order", "keyed row order", "selected_followups order", "finite numeric strings", "data/ hash prefix"],
        "forbidden": ["duplicate keys/rows", "pooled-only decision", "related replicate counted as independent", "missing context", "wrong hash", "nonfinite number"]
    }
    write(TASK / "data/rules.json", rules)
    write(TASK / "data/evidence.json", evidence)
    write(TASK / "data/followups.json", followups)
    write(TASK / "data/output_contract.json", contract)
    write(TASK / "quality/source_ledger.json", {"status": "SYNTHETIC_DISCLOSED", "source": "locally authored evidence portfolio fixture", "empirical_claim": False, "claim_boundary": rules["claim_boundary"]})


if __name__ == "__main__":
    main()
