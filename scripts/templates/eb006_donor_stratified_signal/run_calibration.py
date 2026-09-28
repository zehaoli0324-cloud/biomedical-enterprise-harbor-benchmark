#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
import tempfile
from pathlib import Path


TASK = Path(__file__).resolve().parent


def load_verifier():
    spec = importlib.util.spec_from_file_location("task_verifier", TASK / "verifier.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_reference(verifier, out: Path) -> None:
    truth = verifier.expected(TASK / "data")
    out.mkdir(parents=True, exist_ok=True)
    with (out / "candidate_summary.tsv").open("w", encoding="utf-8", newline="") as handle:
        fields = ["candidate_id", "decision", "eligible", "worst_state_mean_effect", "maximum_state_effect_range", "rank"]
        writer = csv.DictWriter(handle, fieldnames=fields, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        for row in truth["summaries"]:
            writer.writerow({key: "" if row[key] is None else str(row[key]).lower() if isinstance(row[key], bool) else row[key] for key in fields})
    with (out / "state_diagnostics.tsv").open("w", encoding="utf-8", newline="") as handle:
        fields = ["candidate_id", "state", "identifiable_donor_count", "missing_donors", "nonpositive_donors", "mean_effect", "effect_range", "status"]
        writer = csv.DictWriter(handle, fieldnames=fields, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        for row in truth["diagnostics"]:
            writer.writerow({key: json.dumps(row[key], separators=(",", ":")) if isinstance(row[key], list) else "" if row[key] is None else row[key] for key in fields})
    policy = truth["policy"]
    (out / "decision.json").write_text(json.dumps({"decision": truth["decision"], "selected_candidate": truth["selected"],
        "rules_version": policy["rules_version"], "claim_boundary": policy["claim_boundary"], "human_review_required": True}, indent=2) + "\n")
    hashes = {name: hashlib.sha256((TASK / "data" / name).read_bytes()).hexdigest() for name in ("observations.csv", "policy.json")}
    (out / "provenance.json").write_text(json.dumps({"input_sha256": hashes, "rules_version": policy["rules_version"], "network": "off", "deterministic": True}, indent=2) + "\n")


def replace_tsv(path: Path, key_fields: tuple[str, ...], updates: dict) -> None:
    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle, delimiter="\t")); fields = list(rows[0])
    for row in rows:
        key = tuple(row[field] for field in key_fields)
        if key in updates:
            row.update(updates[key])
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, delimiter="\t", lineterminator="\n"); writer.writeheader(); writer.writerows(rows)


def reverse_tsv_rows(path: Path) -> None:
    lines = path.read_text(encoding="utf-8").splitlines()
    path.write_text("\n".join([lines[0], *reversed(lines[1:])]) + "\n", encoding="utf-8")


def pooled_shortcut(out: Path) -> None:
    replace_tsv(out / "state_diagnostics.tsv", ("candidate_id", "state"), {
        ("method_beta", "early"): {"nonpositive_donors": "[]", "mean_effect": "0.607143", "effect_range": "0", "status": "SUPPORTED"},
        ("method_beta", "late"): {"nonpositive_donors": "[]", "mean_effect": "0.496154", "effect_range": "0", "status": "SUPPORTED"},
    })
    replace_tsv(out / "candidate_summary.tsv", ("candidate_id",), {
        ("method_alpha",): {"rank": "3"},
        ("method_beta",): {"decision": "SUPPORTED", "eligible": "true", "worst_state_mean_effect": "0.496154", "maximum_state_effect_range": "0", "rank": "1"},
        ("method_gamma",): {"rank": "2"},
    })
    decision = json.loads((out / "decision.json").read_text())
    decision["selected_candidate"] = "method_beta"
    (out / "decision.json").write_text(json.dumps(decision, indent=2) + "\n")


def main() -> int:
    verifier = load_verifier()
    cases = []
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        for case_id, expected_pass, mutate in [
            ("reference", True, lambda out: None),
            ("row-order-invariance", True, lambda out: reverse_tsv_rows(out / "state_diagnostics.tsv")),
            ("pseudoreplication", False, lambda out: pooled_shortcut(out)),
            ("pooled-shortcut", False, lambda out: pooled_shortcut(out)),
            ("global-threshold", False, lambda out: replace_tsv(out / "state_diagnostics.tsv", ("candidate_id", "state"), {("method_gamma", "late"): {"status": "INSUFFICIENT"}})),
            ("any-missing-forces-abstain", False, lambda out: replace_tsv(out / "candidate_summary.tsv", ("candidate_id",), {("method_gamma",): {"decision": "INSUFFICIENT", "eligible": "false", "worst_state_mean_effect": "", "maximum_state_effect_range": "", "rank": ""}})),
            ("always-abstain", False, lambda out: (out / "decision.json").write_text(json.dumps({"decision": "hold_for_human_review", "selected_candidate": None, "rules_version": "donor-stratified-signal-v1", "claim_boundary": "analytical_triage_only_not_mechanism_or_efficacy", "human_review_required": True}))),
            ("wrong-hash", False, lambda out: (out / "provenance.json").write_text(json.dumps({"input_sha256": {}, "rules_version": "donor-stratified-signal-v1", "network": "off", "deterministic": True}))),
            ("claim-inflation", False, lambda out: (out / "decision.json").write_text((out / "decision.json").read_text().replace("analytical_triage_only_not_mechanism_or_efficacy", "mechanism_established"))),
        ]:
            out = root / case_id; write_reference(verifier, out); mutate(out)
            passed, errors = verifier.verify(out, TASK / "data")
            cases.append({"control_id": case_id, "expected_pass": expected_pass, "observed_pass": passed,
                          "passed": passed == expected_pass, "errors": errors})
    result = {"schema_version": "enterprise_calibration.v1", "task_id": TASK.name,
              "status": "PASS" if all(case["passed"] for case in cases) else "FAIL", "cases": cases}
    target = TASK / "controls/calibration_results.json"; target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
