from __future__ import annotations

import argparse
import csv
import hashlib
import itertools
import json
from pathlib import Path


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _as_bool(value):
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        if value.strip().lower() in {"true", "yes", "1"}:
            return True
        if value.strip().lower() in {"false", "no", "0"}:
            return False
    return None


def _selected(payload: dict) -> list[str]:
    value = payload.get("selected_request_ids", payload.get("route", []))
    if isinstance(value, str):
        value = [item.strip() for item in value.replace("+", ",").split(",") if item.strip()]
    return list(value) if isinstance(value, list) else []


def _numeric(payload: dict, *paths: tuple[str, ...]):
    for path in paths:
        value = payload
        for key in path:
            if not isinstance(value, dict) or key not in value:
                break
            value = value[key]
        else:
            return value
    return None


def _normalized_blockers(value: str) -> list[str]:
    values = [item.strip().lower().replace("-", "_") for item in value.replace(",", ";").split(";") if item.strip()]
    return [] if values == ["none"] else values


def _has_blocker_concept(values: list[str], concept: str) -> bool:
    aliases = {
        "scope": ("scope", "not_current", "provenance_not_current", "archived"),
        "future_outcome_leakage": ("future", "post_decision"),
        "missing_dependency": ("missing_dependency", "missing_prerequisite", "missing prerequisite"),
    }
    return any(any(alias in value for alias in aliases[concept]) for value in values)


def _request_blockers(request: dict, catalog: dict[str, dict], rules: dict) -> list[str]:
    blockers = []
    if request["status"] != rules["required_scope"]:
        blockers.append("scope")
    if request["future_outcome"]:
        blockers.append("future_outcome_leakage")
    if any(dep not in catalog for dep in request["dependency_ids"]):
        blockers.append("missing_dependency")
    return blockers


def _route_metrics(route: tuple[str, ...], catalog: dict[str, dict], uncertainties: list[dict], rules: dict) -> dict:
    selected = set(route)
    blockers = []
    cost = 0.0
    grouped: dict[tuple[str, str], float] = {}
    for request_id in route:
        request = catalog[request_id]
        blockers.extend(_request_blockers(request, catalog, rules))
        if any(dep not in selected for dep in request["dependency_ids"]):
            blockers.append("dependency")
        cost += float(request["cost"])
        for uncertainty_id, reduction in request["covers"].items():
            key = (request["correlation_group"], uncertainty_id)
            grouped[key] = max(grouped.get(key, 0.0), float(reduction))
    if cost > float(rules["max_budget"]):
        blockers.append("budget")
    reductions = {row["uncertainty_id"]: 0.0 for row in uncertainties}
    for (_, uncertainty_id), reduction in grouped.items():
        reductions[uncertainty_id] = reductions.get(uncertainty_id, 0.0) + reduction
    residuals = {
        row["uncertainty_id"]: round(max(float(row["initial"]) - reductions.get(row["uncertainty_id"], 0.0), 0.0), 6)
        for row in uncertainties
    }
    critical = [row for row in uncertainties if row["critical"]]
    crosses = all(residuals[row["uncertainty_id"]] <= float(row["threshold"]) for row in critical)
    if not crosses:
        blockers.append("critical_threshold")
    return {
        "cost": round(cost, 6),
        "reductions": {key: round(value, 6) for key, value in reductions.items()},
        "residuals": residuals,
        "max_critical_residual": max(residuals[row["uncertainty_id"]] for row in critical),
        "blockers": sorted(set(blockers)),
        "valid": not blockers,
    }


def expected(data: Path) -> dict:
    rules = json.loads((data / "rules.json").read_text())
    manifest = json.loads((data / "inputs/run_manifest.json").read_text())
    uncertainties = json.loads((data / "inputs/uncertainty_map.json").read_text())["uncertainties"]
    requests = json.loads((data / "inputs/request_catalog.json").read_text())
    catalog = {row["request_id"]: row for row in requests}
    routes = []
    request_ids = sorted(catalog)
    for size in range(1, len(request_ids) + 1):
        for route in itertools.combinations(request_ids, size):
            metrics = _route_metrics(route, catalog, uncertainties, rules)
            if metrics["valid"]:
                routes.append((route, metrics))
    if routes:
        selected_route, selected_metrics = min(
            routes,
            key=lambda item: (item[1]["max_critical_residual"], item[1]["cost"], item[0]),
        )
        decision = "execute_route"
        human_review = False
        stop_condition = "route_selected"
    else:
        selected_route, selected_metrics = (), {
            "cost": 0.0,
            "residuals": {row["uncertainty_id"]: row["initial"] for row in uncertainties},
            "max_critical_residual": max(row["initial"] for row in uncertainties if row["critical"]),
        }
        decision = "human_review"
        human_review = True
        stop_condition = "human_review_required"
    request_rows = {}
    selected_set = set(selected_route)
    for request in requests:
        blockers = _request_blockers(request, catalog, rules)
        if request["request_id"] in selected_set and any(dep not in selected_set for dep in request["dependency_ids"]):
            blockers.append("dependency")
        request_rows[request["request_id"]] = {
            "status": request["status"],
            "included": request["request_id"] in selected_set,
            "blockers": sorted(set(blockers)),
            "effective_reductions": request["covers"] if not blockers else {},
            "route_position": selected_route.index(request["request_id"]) + 1 if request["request_id"] in selected_set else None,
        }
    files = sorted(path for path in data.rglob("*.json"))
    return {
        "selected_request_ids": list(selected_route),
        "decision": decision,
        "human_review_required": human_review,
        "stop_condition": stop_condition,
        "route_cost": selected_metrics["cost"],
        "residual_uncertainty": selected_metrics["residuals"],
        "max_critical_residual": selected_metrics["max_critical_residual"],
        "request_rows": request_rows,
        "rules_version": rules["rules_version"],
        "network": manifest["network"],
        "hashes": {str(path.relative_to(data)): sha(path) for path in files},
    }


def verify(submission: Path, data: Path, reference: Path) -> tuple[bool, list[str]]:
    exp, errors = expected(data), []
    for name in ("plan.json", "route.tsv", "decision.json", "provenance.json", "audit.md"):
        if not (submission / name).is_file():
            errors.append("missing artifact: " + name)
    if errors:
        return False, errors
    plan = json.loads((submission / "plan.json").read_text())
    decision = json.loads((submission / "decision.json").read_text())
    for name, payload in (("plan", plan), ("decision", decision)):
        if sorted(_selected(payload)) != sorted(exp["selected_request_ids"]):
            errors.append(name + " selected request mismatch")
    if plan.get("network_used") is not False:
        errors.append("plan must remain offline")
    if plan.get("stop_condition") != exp["stop_condition"]:
        errors.append("plan stop condition mismatch")
    if not isinstance(plan.get("total_cost"), (int, float)) or abs(plan["total_cost"] - exp["route_cost"]) > 1e-6:
        errors.append("plan total cost mismatch")
    decision_value = decision.get("decision", decision.get("stop_condition"))
    accepted_decisions = {"execute_route", "route_selected", "execute_bounded_evidence_route", "execute_bounded_route"} if exp["decision"] == "execute_route" else {"human_review", "human_review_required", "hold"}
    if decision_value not in accepted_decisions:
        errors.append("decision decision mismatch")
    if _as_bool(decision.get("human_review_required")) != exp["human_review_required"]:
        errors.append("decision human_review_required mismatch")
    route_cost = _numeric(decision, ("route_cost",), ("total_cost",), ("objective_values", "total_cost"))
    if not isinstance(route_cost, (int, float)) or abs(route_cost - exp["route_cost"]) > 1e-6:
        errors.append("decision route_cost mismatch")
    residuals = decision.get("residual_uncertainty", decision.get("residual_uncertainty_map"))
    if residuals != exp["residual_uncertainty"]:
        errors.append("decision residual_uncertainty mismatch")
    max_residual = _numeric(decision, ("max_critical_residual",), ("objective_values", "maximum_critical_residual"))
    if not isinstance(max_residual, (int, float)) or abs(max_residual - exp["max_critical_residual"]) > 1e-6:
        errors.append("decision max_critical_residual mismatch")
    rows = list(csv.DictReader((submission / "route.tsv").open(newline=""), delimiter="\t"))
    by_id = {row.get("request_id"): row for row in rows}
    if len(by_id) != len(rows) or set(by_id) != set(exp["request_rows"]):
        errors.append("route table must cover every request exactly once")
    for request_id, wanted in exp["request_rows"].items():
        row = by_id.get(request_id, {})
        if row.get("status") != wanted["status"] or _as_bool(row.get("included")) != wanted["included"]:
            errors.append(request_id + " route disposition mismatch")
        actual_blockers = _normalized_blockers(row.get("blockers", ""))
        for blocker in wanted["blockers"]:
            if not _has_blocker_concept(actual_blockers, blocker):
                errors.append(request_id + " blockers mismatch")
        try:
            reductions = json.loads(row.get("effective_reductions", "{}") or "{}")
        except json.JSONDecodeError:
            reductions = None
        allowed_reductions = [wanted["effective_reductions"]]
        if not wanted["included"]:
            allowed_reductions.append({})
        if reductions not in allowed_reductions:
            errors.append(request_id + " effective reductions mismatch")
    provenance = json.loads((submission / "provenance.json").read_text())
    submitted_hashes = provenance.get("input_sha256", provenance.get("sha256", {}))
    hashes = {str(path).removeprefix("data/"): value for path, value in submitted_hashes.items()}
    if hashes != exp["hashes"] or provenance.get("rules_version") != exp["rules_version"]:
        errors.append("provenance mismatch")
    network = provenance.get("network", provenance.get("network_state"))
    if network is None and provenance.get("network_used") is False:
        network = "off"
    if network != exp["network"] or provenance.get("deterministic") is not True:
        errors.append("environment provenance mismatch")
    audit = (submission / "audit.md").read_text().lower().replace("_", " ")
    concepts = {
        "bottleneck": ("bottleneck", "critical uncertainty"),
        "dependency": ("dependency", "prerequisite"),
        "correlation": ("correlation", "correlated"),
        "future": ("future", "post-decision"),
        "budget": ("budget", "cost"),
        "stop": ("stop", "route selected", "human review"),
        "claim": ("not experimental proof", "not experimental validation", "planning only not experimental proof"),
    }
    for concept, terms in concepts.items():
        if not any(term in audit for term in terms):
            errors.append("audit missing " + concept)
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
