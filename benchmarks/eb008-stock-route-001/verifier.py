from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _as_bool(value):
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        if value.strip().lower() in {"true", "yes", "pass", "accepted", "available"}:
            return True
        if value.strip().lower() in {"false", "no", "fail", "rejected", "unavailable"}:
            return False
    return None


def expected(data: Path) -> dict:
    routes = json.loads((data / "routes.json").read_text())
    evidence = json.loads((data / "reaction_evidence.json").read_text())
    rules = json.loads((data / "rules.json").read_text())
    stock = {row["compound_id"] for row in csv.DictReader((data / "stock.csv").open()) if row["available"] == "true"}
    rows = []
    for route in routes:
        steps = [row for row in evidence if row["route_id"] == route["route_id"]]
        failed_gates = []
        if not all(item in stock for item in route["starting_materials"]):
            failed_gates.append("stock")
        if route["steps"] > rules["max_steps"] or len(steps) != route["steps"]:
            failed_gates.append("step_budget_or_evidence_coverage")
        if any(row["precedent_scope"] not in rules["allowed_precedent_scope"] for row in steps):
            failed_gates.append("precedent_scope")
        if any(row["chemoselectivity_risk"] not in rules["allowed_risk"] for row in steps):
            failed_gates.append("chemoselectivity")
        if rules["require_stereochemistry_resolved"] and any(not row["stereochemistry_resolved"] for row in steps):
            failed_gates.append("stereochemistry")
        if rules["require_protection_strategy_resolved"] and any(not row["protection_strategy_resolved"] for row in steps):
            failed_gates.append("protection_strategy")
        reaction_valid = not any(gate != "stock" for gate in failed_gates)
        rows.append({
            "route_id": route["route_id"],
            "target": route["target"],
            "score": route["score"],
            "stock_ok": "stock" not in failed_gates,
            "reaction_valid": reaction_valid,
            "failed_gates": failed_gates,
            "accepted": not failed_gates,
        })
    accepted = [row["route_id"] for row in rows if row["accepted"]]
    return {
        "routes": rows,
        "accepted_routes": accepted,
        "accepted_route": accepted[0] if len(accepted) == 1 else None,
        "evidence_pairs": sorted((row["route_id"], str(row["step"])) for row in evidence),
        "hashes": {name: sha(data / name) for name in ("routes.json", "stock.csv", "rules.json", "reaction_evidence.json")},
        "rules_version": rules["rules_version"],
    }


def verify(submission: Path, data: Path, reference: Path) -> tuple[bool, list[str]]:
    exp, errors = expected(data), []
    for name in ("route_table.tsv", "stock_compliance.json", "route_evidence.tsv", "approval_gate.md"):
        if not (submission / name).is_file():
            errors.append("missing artifact: " + name)
    if errors:
        return False, errors
    report = json.loads((submission / "stock_compliance.json").read_text())
    submitted = report.get("routes", report.get("route_rows", []))
    by_id = {row.get("route_id"): row for row in submitted if isinstance(row, dict)}
    if set(by_id) != {row["route_id"] for row in exp["routes"]}:
        errors.append("route report must cover every route")
    for expected_row in exp["routes"]:
        row = by_id.get(expected_row["route_id"], {})
        stock_value = next((row[name] for name in ("stock_ok", "stock_compliant", "stock_available") if name in row), None)
        if _as_bool(stock_value) != expected_row["stock_ok"]:
            errors.append(f"{expected_row['route_id']} stock evidence mismatch")
        if _as_bool(row.get("accepted")) != expected_row["accepted"]:
            errors.append(f"{expected_row['route_id']} accepted mismatch")
    selected = report.get("selected_route_ids", report.get("accepted_routes", []))
    if sorted(selected) != sorted(exp["accepted_routes"]):
        errors.append("accepted route set mismatch")

    evidence_rows = list(csv.DictReader((submission / "route_evidence.tsv").open(), delimiter="\t"))
    submitted_pairs = sorted((row.get("route_id", "").upper(), row.get("step", "")) for row in evidence_rows)
    if submitted_pairs != exp["evidence_pairs"]:
        errors.append("route evidence must cover every reaction step")
    table_rows = list(csv.DictReader((submission / "route_table.tsv").open(), delimiter="\t"))
    table_by_id = {row.get("route_id"): row for row in table_rows}
    if set(table_by_id) != {row["route_id"] for row in exp["routes"]}:
        errors.append("route table must cover every route")
    gate_terms = {
        "stock": ("stock", "unavailable"),
        "step_budget_or_evidence_coverage": ("step", "budget", "evidence"),
        "precedent_scope": ("precedent", "scope"),
        "chemoselectivity": ("chemoselect",),
        "stereochemistry": ("stereo",),
        "protection_strategy": ("protect",),
    }
    for expected_row in exp["routes"]:
        row = table_by_id.get(expected_row["route_id"], {})
        reaction_text = str(next((row[name] for name in ("reaction_valid", "derived_reaction_validity", "reaction_validity") if name in row), "")).lower()
        reaction_valid = bool(reaction_text) and "invalid" not in reaction_text and any(term in reaction_text for term in ("valid", "true", "pass"))
        if reaction_valid != expected_row["reaction_valid"]:
            errors.append(f"{expected_row['route_id']} reaction validity mismatch")
        failed_text = str(next((row[name] for name in ("failed_gates", "failure_basis") if name in row), "")).lower()
        for gate in expected_row["failed_gates"]:
            if not any(term in failed_text for term in gate_terms[gate]):
                errors.append(f"{expected_row['route_id']} failed gate missing: {gate}")
        if _as_bool(row.get("accepted")) != expected_row["accepted"]:
            errors.append(f"{expected_row['route_id']} table decision mismatch")
    table_header = list(table_rows[0]) if table_rows else []
    for concept, alternatives in {
        "stock": ("stock_ok", "stock_compliant", "stock_evidence"),
        "reaction": ("reaction_valid", "derived_reaction_validity", "reaction_validity"),
        "failed gates": ("failed_gates", "failure_basis"),
        "decision": ("accepted",),
    }.items():
        if not any(term in table_header for term in alternatives):
            errors.append("route table lacks " + concept)
    text = (submission / "approval_gate.md").read_text().lower()
    for concept, alternatives in {
        "human review": ("human", "chemist"),
        "experimental boundary": ("experimental", "laboratory"),
        "chemistry evidence": ("precedent", "chemoselect", "stereochem", "protection"),
    }.items():
        if not any(term in text for term in alternatives):
            errors.append("approval gate omits " + concept)
    return not errors, errors


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--submission", type=Path, required=True)
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--reference", type=Path, required=True)
    args = parser.parse_args()
    ok, errors = verify(args.submission, args.data, args.reference)
    print(json.dumps({"passed": ok, "errors": errors}))
    raise SystemExit(0 if ok else 1)
