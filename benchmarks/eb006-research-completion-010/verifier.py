from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import math
import shutil
import tempfile
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path


def load(path):
    def unique(pairs):
        result = {}
        for k, v in pairs:
            if k in result:
                raise ValueError("duplicate JSON key")
            result[k] = v
        return result
    def invalid(v):
        raise ValueError("non-finite JSON")
    return json.loads(path.read_text(), object_pairs_hook=unique, parse_constant=invalid)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rounded(value):
    return None if value is None else float(value.quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP))


def expected(data):
    policy = load(data / "policy.json")
    with (data / "observations.csv").open(newline="") as handle:
        rows = list(csv.DictReader(handle))
    cs, ss, ds = policy["active_candidates"], policy["registered_states"], policy["registered_donors"]
    rows = [r for r in rows if r["candidate_id"] in cs and r["state"] in ss and r["donor"] in ds
            and r["condition"] in policy["conditions"] and r["qc_status"] == "PASS" and r["adjusted_signal"] != ""]
    effects, cells = {}, {}
    units, pooled, checks, summaries = [], [], [], []
    means, statuses, pooled_means = {}, {}, {}
    def avg(values):
        return sum(values) / len(values) if values else None
    def minimum(values):
        return min(values) if values and all(v is not None for v in values) else None
    for c in cs:
        for s in ss:
            for d in ds:
                groups = [[Decimal(r["adjusted_signal"]) for r in rows if (r["candidate_id"], r["state"], r["donor"], r["condition"]) == (c,s,d,condition)] for condition in ("control", "treatment")]
                cells[c,s,d] = tuple(map(len, groups))
                effects[c,s,d] = avg(groups[1]) - avg(groups[0]) if all(groups) else None
                units.append({"id": "|".join([c,s,d]), "effect": rounded(effects[c,s,d]), "control_rows": len(groups[0]), "treatment_rows": len(groups[1])})
            groups = [[Decimal(r["adjusted_signal"]) for r in rows if (r["candidate_id"],r["state"],r["condition"]) == (c,s,condition)] for condition in ("control", "treatment")]
            pooled_means[c,s] = avg(groups[1]) - avg(groups[0]) if all(groups) else None
            pooled.append({"id": c+"|"+s, "effect": rounded(pooled_means[c,s]), "control_rows": len(groups[0]), "treatment_rows": len(groups[1])})
            for scenario in policy["scenarios"]:
                omitted = None if scenario == "base" else scenario.removeprefix("omit:")
                remaining = [d for d in ds if d != omitted]
                present = {d: effects[c,s,d] for d in remaining if effects[c,s,d] is not None}
                values = list(present.values())
                mean, spread = avg(values), max(values)-min(values) if values else None
                minimum_count = policy["minimum_identifiable_donors"][s] if omitted is None else max(2, policy["minimum_identifiable_donors"][s]-1)
                negative = sorted(d for d,v in present.items() if v <= 0)
                if len(values) < minimum_count:
                    status = "INSUFFICIENT"
                elif negative:
                    status = "CONTRADICTORY"
                elif mean < Decimal(str(policy["minimum_state_mean_effect"][s])) or spread > Decimal(str(policy["maximum_state_effect_range"][s])):
                    status = "WEAK"
                else:
                    status = "SUPPORTED"
                means[scenario,c,s], statuses[scenario,c,s] = mean, status
                checks.append({"id": "|".join([scenario,c,s]), "count": len(values),
                               "missing_donors": sorted(set(remaining)-set(present)), "nonpositive_donors": negative,
                               "mean_effect": rounded(mean), "effect_range": rounded(spread), "status": status})
    nominal_scores, robust_scores, pooled_scores = {}, {}, {}
    for c in cs:
        nominal = minimum([means["base",c,s] for s in ss])
        robust = minimum([means[x,c,s] for x in policy["scenarios"] for s in ss])
        pooled_score = minimum([pooled_means[c,s] for s in ss])
        failed = sorted(x for x in policy["scenarios"] if any(statuses[x,c,s] != "SUPPORTED" for s in ss))
        nominal_ok, robust_ok = "base" not in failed, not failed
        if nominal_ok:
            nominal_scores[c] = nominal
        if robust_ok:
            robust_scores[c] = robust
        if pooled_score is not None:
            pooled_scores[c] = pooled_score
        summaries.append({"id": c, "nominal_eligible": nominal_ok, "robust_eligible": robust_ok,
                          "nominal_worst_mean": rounded(nominal), "robust_worst_mean": rounded(robust),
                          "pooled_worst_mean": rounded(pooled_score), "failed_scenarios": failed})
    def winner(scores):
        return min(scores, key=lambda c: (-scores[c],c)) if scores else None
    nominal, robust, pooled_choice = map(winner, (nominal_scores,robust_scores,pooled_scores))
    assay_rows = []
    with (data / "assay_observations.csv").open(newline="") as handle:
        assay_rows = list(csv.DictReader(handle))
    assay_effects = {}
    assay_checks = []
    assay_statuses = {}
    for c in cs:
        for s in ss:
            by_assay = {}
            for assay in policy["registered_assays"]:
                effects_by_donor = {}
                for d in ds:
                    groups = [[Decimal(r["adjusted_signal"]) for r in assay_rows if
                               (r["candidate_id"], r["state"], r["donor"], r["assay"], r["condition"]) ==
                               (c, s, d, assay, condition) and r["qc_status"] == "PASS" and r["adjusted_signal"] != ""]
                              for condition in ("control", "treatment")]
                    effects_by_donor[d] = avg(groups[1]) - avg(groups[0]) if all(groups) else None
                values = [v for v in effects_by_donor.values() if v is not None]
                by_assay[assay] = (avg(values), effects_by_donor)
            a_mean, a_donors = by_assay["A"]
            b_mean, b_donors = by_assay["B"]
            a_values, b_values = list(a_donors.values()), list(b_donors.values())
            complete = all(v is not None for v in a_values + b_values)
            nonpositive = any(v is not None and v <= 0 for v in a_values + b_values)
            concordant = a_mean is not None and b_mean is not None and a_mean * b_mean > 0
            effect_range = abs(a_mean - b_mean) if a_mean is not None and b_mean is not None else None
            if not complete:
                status = "INSUFFICIENT"
            elif nonpositive or not concordant:
                status = "CONTRADICTORY"
            elif a_mean < Decimal(str(policy["minimum_assay_effect"])) or b_mean < Decimal(str(policy["minimum_assay_effect"])) or effect_range > Decimal(str(policy["maximum_state_effect_range"][s])):
                status = "WEAK"
            else:
                status = "SUPPORTED"
            assay_statuses[c, s] = status
            assay_checks.append({"id": f"{c}|{s}", "assay_a_effect": rounded(a_mean), "assay_b_effect": rounded(b_mean),
                                 "direction_concordant": concordant, "effect_range": rounded(effect_range), "status": status})
    assay_selected = robust if robust is not None and all(assay_statuses[c, s] == "SUPPORTED" for s in ss) else None
    reasons = []
    if nominal != pooled_choice:
        reasons.append("pooled_ranking_disagrees")
    if nominal != robust:
        reasons.append("nominal_selection_not_robust")
    if any(len({cells[c,s,d][i] for d in ds}) > 1 for c in cs for s in ss for i in (0,1)):
        reasons.append("technical_replication_imbalance")
    if any(v is None for v in effects.values()):
        reasons.append("missing_pair_evidence")
    if assay_selected != robust:
        reasons.append("cross_assay_disagreement")
    return {"unit_effects": units, "pooled": pooled, "checks": checks, "summaries": summaries,
            "assay_checks": assay_checks,
            "decision": {"nominal_selected": nominal, "pooled_selected": pooled_choice, "selected": assay_selected,
                         "assay_selected": assay_selected, "cross_assay_hold": assay_selected is None,
                         "reason_codes": sorted(reasons), "claim_boundary": policy["claim_boundary"], "human_review_required": True}}


def compare(actual, wanted, path="results", errors=None):
    errors = [] if errors is None else errors
    if isinstance(wanted, bool) or wanted is None or isinstance(wanted, str):
        if type(actual) is not type(wanted) or actual != wanted:
            errors.append(path + ": mismatch")
    elif isinstance(wanted, (int,float)):
        if type(actual) not in (int,float) or not math.isfinite(actual) or abs(actual-wanted) > 1e-6:
            errors.append(path + ": numeric mismatch")
    elif isinstance(wanted, dict):
        if not isinstance(actual, dict) or set(actual) != set(wanted):
            errors.append(path + ": key coverage")
        if isinstance(actual, dict):
            for key in wanted:
                compare(actual.get(key), wanted[key], path+"."+key, errors)
    elif isinstance(wanted, list):
        if wanted and isinstance(wanted[0], dict):
            if not isinstance(actual, list) or any(not isinstance(row, dict) or not isinstance(row.get("id"), str) for row in actual):
                errors.append(path + ": identified rows required")
            else:
                by_id = {row["id"]: row for row in actual}
                if len(by_id) != len(actual) or set(by_id) != {row["id"] for row in wanted}:
                    errors.append(path + ": row coverage")
                for row in wanted:
                    compare(by_id.get(row["id"]), row, path+"["+row["id"]+"]", errors)
        elif path.endswith(".reason_codes"):
            if sorted(actual) != sorted(wanted):
                errors.append(path + ": members mismatch")
        elif actual != wanted:
            errors.append(path + ": members mismatch")
    return errors


def verify(submission, data, reference=None):
    errors = []
    for name in ("analysis.py", "results.json", "provenance.json", "research_audit.md"):
        if not (submission/name).is_file() or (submission/name).is_symlink():
            errors.append("delivery: missing or invalid " + name)
    if errors:
        return False, errors
    try:
        errors.extend(compare(load(submission/"results.json"), expected(data)))
        p = load(data/"policy.json")
        provenance = {"input_sha256": {f.name: sha(f) for f in data.iterdir() if f.is_file()},
                      "analysis_sha256": sha(submission/"analysis.py"), "rules_version": p["rules_version"], "network": "off", "deterministic": True}
        errors.extend(compare(load(submission/"provenance.json"), provenance, "provenance"))
        if not (submission/"research_audit.md").read_text().strip():
            errors.append("delivery: empty audit")
        # A declared input-perturbation replay rejects constant-output programs.
        root = Path(__file__).resolve().parents[2]
        spec = importlib.util.spec_from_file_location("research_gate", root/"benchmark_runner/research_gate.py")
        gate = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(gate)
        with tempfile.TemporaryDirectory(prefix="research-score-") as tmp:
            tmp = Path(tmp)
            variant = tmp/"data"
            shutil.copytree(data, variant)
            with (variant/"observations.csv").open(newline="") as handle:
                reader = csv.DictReader(handle)
                fields, rows = reader.fieldnames, list(reader)
            candidate = p["active_candidates"][0]
            for row in rows:
                if row["candidate_id"] == candidate and row["condition"] == "treatment" and row["adjusted_signal"]:
                    row["adjusted_signal"] = str(Decimal(row["adjusted_signal"])-Decimal("0.21"))
            with (variant/"observations.csv").open("w", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=fields)
                writer.writeheader()
                writer.writerows(rows)
            run = gate.run_program((submission/"analysis.py").resolve(), variant, tmp/"out", tmp/"execution.log", 10)
            if run["exit_code"]:
                errors.append("replay: program execution failed")
            else:
                errors.extend(compare(load(tmp/"out/results.json"), expected(variant), "perturbation"))
    except (ValueError, OSError, TypeError, KeyError) as exc:
        errors.append("delivery_or_contract: " + str(exc))
    return not errors, errors


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--submission", type=Path, required=True)
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--reference", type=Path, required=True)
    args = parser.parse_args()
    passed, errors = verify(args.submission,args.data,args.reference)
    print(json.dumps({"passed": passed,"errors": errors}))
    raise SystemExit(0 if passed else 1)
