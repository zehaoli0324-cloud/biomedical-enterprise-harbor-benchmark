from __future__ import annotations
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
