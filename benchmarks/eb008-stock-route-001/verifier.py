from __future__ import annotations

import argparse
import csv
import hashlib
import json
from datetime import date
from pathlib import Path


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _as_bool(value):
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        if value.strip().lower() in {"true", "yes", "pass", "accepted"}:
            return True
        if value.strip().lower() in {"false", "no", "fail", "rejected"}:
            return False
    return None


def expected(data: Path) -> dict:
    routes = json.loads((data / "routes.json").read_text())
    evidence = json.loads((data / "reaction_evidence.json").read_text())
    rules = json.loads((data / "rules.json").read_text())
    stock_rows = list(csv.DictReader((data / "stock.csv").open()))
    source_rows = list(csv.DictReader((data / "evidence_sources.csv").open()))
    sources = {row["source_id"]: row for row in source_rows}
    if len(sources) != len(source_rows) or any(row["source_id"] not in sources for row in evidence):
        raise ValueError("evidence source join is incomplete or non-unique")
    decision_date = date.fromisoformat(rules["decision_date"])
    usable_stock = {}
    for row in stock_rows:
        eligible = row["status"] in rules["eligible_lot_status"] and date.fromisoformat(row["expiry_date"]) >= decision_date
        usable = max(float(row["on_hand"]) - float(row["reserved"]), 0.0) if eligible else 0.0
        usable_stock[row["compound_id"]] = usable_stock.get(row["compound_id"], 0.0) + usable
    usable_stock = {key: round(value, 6) for key, value in sorted(usable_stock.items())}

    joined_evidence = []
    for row in evidence:
        source = sources[row["source_id"]]
        included = source["status"] in rules["eligible_source_status"] and source["scope"] == rules["target"]
        joined_evidence.append({**row, **{f"source_{k}": v for k, v in source.items() if k != "source_id"}, "included": included})

    route_rows = []
    for route in routes:
        failed = []
        material_status = {
            item["compound_id"]: {
                "required": item["required_amount"],
                "usable": usable_stock.get(item["compound_id"], 0.0),
                "sufficient": usable_stock.get(item["compound_id"], 0.0) >= item["required_amount"],
            }
            for item in route["materials"]
        }
        if route["target"] != rules["target"]:
            failed.append("target_identity")
        if not all(item["sufficient"] for item in material_status.values()):
            failed.append("stock")
        route_evidence = [row for row in joined_evidence if row["route_id"] == route["route_id"] and row["included"]]
        if route["steps"] > rules["max_steps"]:
            failed.append("step_budget")
        quorum = {}
        for step in range(1, route["steps"] + 1):
            step_rows = [row for row in route_evidence if int(row["step"]) == step]
            groups = {row["source_independence_group"] for row in step_rows}
            quorum[str(step)] = len(groups)
            if len(groups) < rules["min_independent_sources_per_step"]:
                failed.append("evidence_quorum")
            if any(row["precedent_scope"] not in rules["allowed_precedent_scope"] for row in step_rows):
                failed.append("precedent_scope")
            if any(row["chemoselectivity_risk"] not in rules["allowed_risk"] for row in step_rows):
                failed.append("chemoselectivity")
            if rules["require_stereochemistry_resolved"] and any(not row["stereochemistry_resolved"] for row in step_rows):
                failed.append("stereochemistry")
            if rules["require_protection_strategy_resolved"] and any(not row["protection_strategy_resolved"] for row in step_rows):
                failed.append("protection_strategy")
        failed = list(dict.fromkeys(failed))
        chemistry_gates = {"step_budget", "evidence_quorum", "precedent_scope", "chemoselectivity", "stereochemistry", "protection_strategy", "target_identity"}
        route_rows.append({
            "route_id": route["route_id"], "target": route["target"], "score": route["score"],
            "material_status": material_status, "stock_ok": "stock" not in failed,
            "evidence_quorum": quorum, "reaction_valid": not bool(set(failed) & chemistry_gates),
            "failed_gates": failed, "accepted": not failed,
        })
    accepted = [row["route_id"] for row in route_rows if row["accepted"]]
    return {
        "routes": route_rows, "accepted_routes": accepted,
        "accepted_route": accepted[0] if len(accepted) == 1 else None,
        "usable_stock": usable_stock, "joined_evidence": joined_evidence,
        "evidence_keys": sorted((row["route_id"], str(row["step"]), row["source_id"]) for row in evidence),
        "hashes": {name: sha(data / name) for name in ("routes.json", "stock.csv", "rules.json", "reaction_evidence.json", "evidence_sources.csv")},
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
    if report.get("usable_stock") != exp["usable_stock"]:
        errors.append("usable stock calculation mismatch")
    for expected_row in exp["routes"]:
        row = by_id.get(expected_row["route_id"], {})
        if _as_bool(row.get("stock_ok", row.get("stock_compliant", row.get("stock_available")))) != expected_row["stock_ok"]:
            errors.append(f"{expected_row['route_id']} stock evidence mismatch")
        submitted_quorum = row.get("evidence_quorum")
        if isinstance(submitted_quorum, str):
            try:
                submitted_quorum = json.loads(submitted_quorum)
            except json.JSONDecodeError:
                submitted_quorum = None
        if submitted_quorum is not None and submitted_quorum != expected_row["evidence_quorum"]:
            errors.append(f"{expected_row['route_id']} evidence quorum mismatch")
        if "failed_gates" in row and sorted(row.get("failed_gates", [])) != sorted(expected_row["failed_gates"]):
            errors.append(f"{expected_row['route_id']} failed gates mismatch")
        if _as_bool(row.get("accepted")) != expected_row["accepted"]:
            errors.append(f"{expected_row['route_id']} accepted mismatch")
    selected = report.get("selected_route_ids", report.get("accepted_routes", []))
    if sorted(selected) != sorted(exp["accepted_routes"]):
        errors.append("accepted route set mismatch")

    evidence_rows = list(csv.DictReader((submission / "route_evidence.tsv").open(), delimiter="\t"))
    submitted_keys = sorted((row.get("route_id", "").lower(), row.get("step", ""), row.get("source_id", "").lower()) for row in evidence_rows)
    expected_keys = sorted((route.lower(), step, source.lower()) for route, step, source in exp["evidence_keys"])
    if submitted_keys != expected_keys:
        errors.append("route evidence must cover every source record")
    evidence_by_key = {(row.get("route_id", "").lower(), row.get("step", ""), row.get("source_id", "").lower()): row for row in evidence_rows}
    for expected_row in exp["joined_evidence"]:
        row = evidence_by_key.get((expected_row["route_id"].lower(), str(expected_row["step"]), expected_row["source_id"].lower()), {})
        if row.get("source_status", "").lower() != str(expected_row["source_status"]).lower() or row.get("independence_group", "").lower() != str(expected_row["source_independence_group"]).lower() or _as_bool(row.get("included")) != expected_row["included"]:
            errors.append(f"{expected_row['source_id']} source join mismatch")

    table_rows = list(csv.DictReader((submission / "route_table.tsv").open(), delimiter="\t"))
    table_by_id = {row.get("route_id"): row for row in table_rows}
    if set(table_by_id) != {row["route_id"] for row in exp["routes"]}:
        errors.append("route table must cover every route")
    for expected_row in exp["routes"]:
        row = table_by_id.get(expected_row["route_id"], {})
        if _as_bool(row.get("reaction_valid")) != expected_row["reaction_valid"] or _as_bool(row.get("accepted")) != expected_row["accepted"]:
            errors.append(f"{expected_row['route_id']} table decision mismatch")
        failed_text = row.get("failed_gates", "").lower()
        if any(gate.replace("_", " ") not in failed_text.replace("_", " ") for gate in expected_row["failed_gates"]):
            errors.append(f"{expected_row['route_id']} table omits a failed gate")
    header = list(table_rows[0]) if table_rows else []
    for field in ("route_id", "usable_stock", "stock_ok", "evidence_quorum", "reaction_valid", "failed_gates", "accepted"):
        if field not in header:
            errors.append("route table lacks " + field)
    text = (submission / "approval_gate.md").read_text().lower()
    for concept, terms in {
        "human review": ("human", "chemist"), "experimental boundary": ("experimental", "laboratory"),
        "chemistry evidence": ("precedent", "chemoselect", "stereo", "protection"),
    }.items():
        if not any(term in text for term in terms):
            errors.append("approval gate omits " + concept)
    excluded_statuses = {"retracted", "wrong-target"}
    if not any(term in text for term in ("retracted", "wrong-target", "excluded source")):
        excluded_rows = [row for row in evidence_rows if row.get("source_status", "").lower() in excluded_statuses]
        if excluded_rows and any(_as_bool(row.get("included")) for row in excluded_rows):
            errors.append("approval gate omits excluded sources")
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
