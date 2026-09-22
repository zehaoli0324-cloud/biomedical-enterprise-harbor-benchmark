from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _files(data: Path) -> list[Path]:
    return sorted(path for path in data.rglob("*") if path.is_file())


def _canonical_status(value: str) -> str:
    aliases = {
        "ambiguous": "human_review",
        "explicit_review": "human_review",
        "clear_proceed": "proceed",
        "future_outcome": "future_outcome_leakage",
        "out_of_scope": "out_of_scope",
    }
    return aliases.get(str(value), str(value))


def _canonical_blockers(values) -> list[str]:
    if not isinstance(values, list):
        return []
    result = []
    for value in values:
        value = str(value)
        if value.startswith("numeric_blocker:"):
            value = value.split(":", 1)[1].strip()
            if "uncertainty" in value:
                value = "uncertainty"
            elif "signal" in value:
                value = "signal_threshold"
            elif "budget" in value:
                value = "budget"
        elif value in {"ambiguous_proceed_and_review_cues", "explicit_human_review"}:
            value = "semantic_ambiguity"
        elif value.startswith("out_of_scope:"):
            value = "scope"
        result.append(value)
    return result


def _status_matches(actual, expected: str, blockers) -> bool:
    actual = _canonical_status(actual)
    canonical_blockers = _canonical_blockers(blockers)
    if actual == expected:
        return True
    return (
        actual in {"proceed", "unresolved"}
        and (
            (expected == "future_outcome_leakage" and "future_outcome_leakage" in canonical_blockers)
            or (expected == "out_of_scope" and "scope" in canonical_blockers)
        )
    )


def _blockers_match(actual, expected, semantic_status) -> bool:
    actual = _canonical_blockers(actual)
    if "semantic_ambiguity" in expected and _canonical_status(semantic_status) == "human_review":
        actual.append("semantic_ambiguity")
    return sorted(set(actual)) == sorted(set(expected))


def _submitted_records(decision: dict) -> dict:
    values = decision.get("records", {})
    if isinstance(values, dict):
        return values
    if isinstance(values, list):
        return {row.get("record_id"): row for row in values if isinstance(row, dict)}
    return {}


def _submitted_discovery(discovery: dict) -> tuple[list[str], dict, str | None]:
    def normalize(path) -> str:
        return str(path).removeprefix("data/")

    if isinstance(discovery.get("files"), list):
        files = [row for row in discovery["files"] if isinstance(row, dict)]
        paths = sorted(normalize(row.get("path")) for row in files)
        hashes = {normalize(row.get("path")): row.get("sha256") for row in files}
        return paths, hashes, discovery.get("manifest_declared_network", discovery.get("network"))
    paths = sorted(normalize(path) for path in discovery.get("discovered_files", []))
    hashes = {normalize(path): digest for path, digest in discovery.get("input_hashes", {}).items()}
    return paths, hashes, discovery.get("network")


def _plan_spec(data: Path) -> dict:
    mission = json.loads((data / "workflow/mission.json").read_text())
    catalog = json.loads((data / "workflow/operation_catalog.json").read_text())
    operations = {row["operation_id"]: row for row in catalog["operations"]}
    return {"mission": mission, "operations": operations}


def _submitted_operations(plan: dict) -> list[dict]:
    values = plan.get("operations", [])
    if not isinstance(values, list):
        return []
    result = []
    for value in values:
        if isinstance(value, str):
            result.append({"operation_id": value})
        elif isinstance(value, dict):
            result.append(value)
    return result


def expected(data: Path) -> dict:
    rules = json.loads((data / "rules.json").read_text())
    manifest = json.loads((data / "inputs/run_manifest.json").read_text())
    lexicon = json.loads((data / "inputs/semantic_lexicon.json").read_text())
    records = json.loads((data / "inputs/policy_records.json").read_text())
    proceed_terms = tuple(lexicon["terms"]["proceed"])
    review_terms = tuple(lexicon["terms"]["review"])
    future_terms = tuple(lexicon["terms"]["future_outcome"])
    rows = {}
    for record in records:
        text = " ".join((record["label"], record["narrative"])).lower()
        proceed = any(term in text for term in proceed_terms)
        review = any(term in text for term in review_terms)
        if proceed and review:
            semantic_status = "ambiguous"
        elif review:
            semantic_status = "human_review"
        else:
            semantic_status = "proceed" if proceed else "unresolved"
        gains = [float(value) for value in record["replays"]]
        utility = round(sum(gains) / len(gains), 6) if gains else None
        utility_range = round(max(gains) - min(gains), 6) if gains else None
        blockers = []
        if record["scope"] != rules["required_scope"]:
            blockers.append("scope")
        if semantic_status != "proceed":
            blockers.append("semantic_ambiguity")
        if record["future_outcome_used"] or any(term in text for term in future_terms):
            blockers.append("future_outcome_leakage")
        if record["signal"] < lexicon["thresholds"]["minimum_signal"]:
            blockers.append("signal_threshold")
        if record["uncertainty"] > lexicon["thresholds"]["maximum_uncertainty_for_proceed"]:
            blockers.append("uncertainty")
        if record["cost"] > rules["max_budget"]:
            blockers.append("budget")
        if len(gains) < rules["min_replay_count"] or utility_range > rules["max_utility_range"]:
            blockers.append("replay_stability")
        if record["future_outcome_used"] or any(term in text for term in future_terms):
            semantic_status = "future_outcome_leakage"
        elif record["scope"] != rules["required_scope"]:
            semantic_status = "out_of_scope"
        elif semantic_status in {"ambiguous", "human_review"}:
            semantic_status = "human_review"
        rows[record["record_id"]] = {
            "semantic_status": semantic_status,
            "utility": utility,
            "utility_range": utility_range,
            "replay_count": len(gains),
            "eligible": not blockers,
            "blocker_reasons": blockers,
        }
    eligible = [(record_id, row) for record_id, row in rows.items() if row["eligible"]]
    selected = min(eligible, key=lambda item: (-item[1]["utility"], item[0]))[0] if eligible else "human_review"
    hashes = {
        str(path.relative_to(data)): sha(path)
        for path in _files(data)
    }
    return {
        "selected_record": selected,
        "records": rows,
        "hashes": hashes,
        "rules_version": rules["rules_version"],
        "network": manifest["network"],
        "discovered_files": sorted(hashes),
    }


def verify(submission: Path, data: Path, reference: Path) -> tuple[bool, list[str]]:
    exp, errors = expected(data), []
    for name in ("plan.json", "decision.json", "evidence.tsv", "discovery.json", "audit.md"):
        if not (submission / name).is_file():
            errors.append("missing artifact: " + name)
    if errors:
        return False, errors
    plan = json.loads((submission / "plan.json").read_text())
    plan_spec = _plan_spec(data)
    mission = plan_spec["mission"]
    operations = plan_spec["operations"]
    submitted_operations = _submitted_operations(plan)
    operation_ids = [row.get("operation_id", row.get("id")) for row in submitted_operations]
    required_ids = set(mission["required_operations"])
    if len(operation_ids) != len(set(operation_ids)) or set(operation_ids) != required_ids:
        errors.append("plan must cover each required operation exactly once")
    seen = set()
    expected_cost = 0.0
    for operation_id in operation_ids:
        operation = operations.get(operation_id)
        if operation is None:
            errors.append(f"unknown plan operation: {operation_id}")
            continue
        if any(dep not in seen for dep in operation["depends_on"]):
            errors.append(f"plan dependency order mismatch: {operation_id}")
        if operation.get("network") is True:
            errors.append(f"plan operation requires network: {operation_id}")
        expected_cost += float(operation["cost"])
        seen.add(operation_id)
    actual_cost = plan.get("total_cost")
    if not isinstance(actual_cost, (int, float)) or abs(float(actual_cost) - expected_cost) > 1e-6:
        errors.append("plan total cost mismatch")
    if float(actual_cost or 0) > float(mission["max_planning_cost"]):
        errors.append("plan exceeds planning budget")
    if plan.get("network_used") is not False:
        errors.append("plan must declare network_used=false")
    if plan.get("stop_condition") not in mission["stop_conditions"]:
        errors.append("plan stop condition mismatch")
    decision = json.loads((submission / "decision.json").read_text())
    if decision.get("selected_record") != exp["selected_record"]:
        errors.append("selected record mismatch")
    if decision.get("rules_version") not in (None, exp["rules_version"]):
        errors.append("rules version mismatch")
    if decision.get("claim_boundary") != "planning_only_not_experimental_proof":
        errors.append("claim boundary mismatch")
    if decision.get("human_review_required") is not True:
        errors.append("human review gate mismatch")
    submitted = _submitted_records(decision)
    if not isinstance(submitted, dict) or set(submitted) != set(exp["records"]):
        errors.append("decision must cover every policy record exactly once")
    for record_id, expected_row in exp["records"].items():
        row = submitted.get(record_id, {}) if isinstance(submitted, dict) else {}
        actual_eligible = row.get("eligible", row.get("eligibility"))
        if not _status_matches(row.get("semantic_status"), expected_row["semantic_status"], row.get("blocker_reasons", [])):
            errors.append(f"{record_id} semantic_status mismatch")
        for field in ("replay_count", "utility", "utility_range"):
            if row.get(field) != expected_row[field]:
                errors.append(f"{record_id} {field} mismatch")
        if actual_eligible != expected_row["eligible"]:
            errors.append(f"{record_id} eligible mismatch")
        if not _blockers_match(row.get("blocker_reasons", []), expected_row["blocker_reasons"], row.get("semantic_status")):
            errors.append(f"{record_id} blocker reasons mismatch")
    evidence = list(csv.DictReader((submission / "evidence.tsv").open(newline=""), delimiter="\t"))
    if {row.get("record_id") for row in evidence} != set(exp["records"]) or len(evidence) != len(exp["records"]):
        errors.append("evidence must cover every policy record once")
    for row in evidence:
        expected_row = exp["records"].get(row.get("record_id"), {})
        actual_eligible = row.get("eligible", row.get("eligibility", ""))
        if not _status_matches(row.get("semantic_status"), expected_row.get("semantic_status"), str(row.get("blocker_reasons", "")).split(";")) or str(actual_eligible).lower() != str(expected_row.get("eligible")).lower():
            errors.append(f"{row.get('record_id')} evidence decision mismatch")
    discovery = json.loads((submission / "discovery.json").read_text())
    discovered_files, input_hashes, network = _submitted_discovery(discovery)
    if discovered_files != exp["discovered_files"] or input_hashes != exp["hashes"]:
        errors.append("discovery manifest mismatch")
    if network != exp["network"] or discovery.get("deterministic") is not True:
        errors.append("environment provenance mismatch")
    audit = (submission / "audit.md").read_text().lower().replace("_", " ")
    term_alternatives = {
        "ambigu": ("ambigu",),
        "scope": ("scope",),
        "future": ("future",),
        "stability": ("stability", "stable", "replay range", "replay count", "replay spread"),
        "human review": ("human review", "review"),
        "not experimental proof": ("not experimental proof", "planning only not experimental proof"),
    }
    term_alternatives["plan"] = ("plan", "workflow", "operation")
    term_alternatives["stop"] = ("stop", "selected", "review")
    for term, alternatives in term_alternatives.items():
        if not any(option in audit for option in alternatives):
            errors.append("audit missing " + term)
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
