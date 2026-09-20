from __future__ import annotations

import argparse
import csv
import hashlib
import json
from datetime import date
from pathlib import Path


REQUIRED_ADSL = [
    "USUBJID",
    "ARMCD",
    "TRT01P",
    "ITTFL",
    "SAFFL",
    "PPROTFL",
    "TRTSDT",
    "TRTEDT",
    "TRTEDT_DTYPE",
]
TRACE_TARGETS = {"ITTFL", "SAFFL", "PPROTFL", "TRTSDT", "TRTEDT"}


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _d(value: str) -> date:
    return date.fromisoformat(value)


def expected(data_dir: Path) -> dict:
    dm = _read_csv(data_dir / "dm.csv")
    ex = _read_csv(data_dir / "ex.csv")
    rules = json.loads((data_dir / "rules.json").read_text(encoding="utf-8"))
    cutoff = _d(rules["analysis_cutoff"])
    randomized = set(rules["randomized_armcd"])
    by_subject: dict[str, list[dict[str, str]]] = {}
    for row in ex:
        by_subject.setdefault(row["USUBJID"], []).append(row)

    rows: list[dict[str, str]] = []
    edge_cases: list[dict[str, str]] = []
    for subject in sorted(dm, key=lambda row: row["USUBJID"]):
        sid = subject["USUBJID"]
        exposure = []
        for record in by_subject.get(sid, []):
            if record["EXSTDTC"] and _d(record["EXSTDTC"]) <= cutoff and float(record["EXDOSE"]) > 0:
                exposure.append(record)
        randomized_flag = subject["ARMCD"] in randomized and bool(subject["RFSTDTC"])
        treated_flag = bool(exposure)
        pprot_flag = (
            randomized_flag
            and treated_flag
            and bool(subject["RFENDTC"])
            and _d(subject["RFENDTC"]) <= cutoff
        )
        start = min((record["EXSTDTC"] for record in exposure), default="")
        end_candidates = [record["EXENDTC"] or record["EXSTDTC"] for record in exposure]
        uncapped_end = max(end_candidates, default="")
        end = min(uncapped_end, rules["analysis_cutoff"]) if uncapped_end else ""
        dtype = "CUTOFF" if uncapped_end and _d(uncapped_end) > cutoff else "NONE"
        if subject["ARMCD"] == "SCRN":
            edge_cases.append({"id": sid, "type": "screen_failure"})
        if not exposure and randomized_flag:
            edge_cases.append({"id": sid, "type": "no_exposure"})
        if exposure and not subject["RFENDTC"]:
            edge_cases.append({"id": sid, "type": "missing_rfendtc"})
        if dtype == "CUTOFF":
            edge_cases.append({"id": sid, "type": "cutoff_capping"})
        rows.append(
            {
                "USUBJID": sid,
                "ARMCD": subject["ARMCD"],
                "TRT01P": rules["arm_labels"].get(subject["ARMCD"], subject["ARM"]),
                "ITTFL": "Y" if randomized_flag else "N",
                "SAFFL": "Y" if treated_flag else "N",
                "PPROTFL": "Y" if pprot_flag else "N",
                "TRTSDT": start,
                "TRTEDT": end,
                "TRTEDT_DTYPE": dtype,
            }
        )
    summary = {
        "subject_count": len(rows),
        "randomized_count": sum(row["ARMCD"] in randomized for row in dm),
        "treated_count": sum(row["SAFFL"] == "Y" for row in rows),
        "itt_count": sum(row["ITTFL"] == "Y" for row in rows),
        "saffl_count": sum(row["SAFFL"] == "Y" for row in rows),
        "pprot_count": sum(row["PPROTFL"] == "Y" for row in rows),
    }
    hashes = {name: _sha256(data_dir / name) for name in ("dm.csv", "ex.csv", "rules.json")}
    return {"rows": rows, "summary": summary, "edge_cases": edge_cases, "hashes": hashes, "rules_version": rules["rules_version"]}


def verify(submission: Path, data_dir: Path, reference_path: Path) -> tuple[bool, list[str]]:
    truth = json.loads(reference_path.read_text(encoding="utf-8"))
    exp = expected(data_dir)
    errors: list[str] = []

    adsl_path = submission / "adsl.csv"
    trace_path = submission / "derivation_trace.csv"
    report_path = submission / "audit_report.json"
    notes_path = submission / "derivation_notes.md"
    manifest_path = submission / "run_manifest.json"
    for path in (adsl_path, trace_path, report_path, notes_path, manifest_path):
        if not path.exists():
            errors.append(f"missing artifact: {path.name}")
    if errors:
        return False, errors

    adsl = _read_csv(adsl_path)
    if list(adsl_path.read_text(encoding="utf-8").splitlines()[0].split(",")) != REQUIRED_ADSL:
        errors.append("adsl.csv has the wrong header")
    if adsl != exp["rows"]:
        errors.append("adsl.csv rows do not match the independently recomputed derivation")
    if [row["USUBJID"] for row in adsl] != sorted(row["USUBJID"] for row in adsl):
        errors.append("adsl.csv must be sorted by USUBJID")

    trace = _read_csv(trace_path)
    trace_fields = {"USUBJID", "target_variable", "source_domain", "source_rows", "rule_id", "derived_value"}
    if not trace or not trace_fields.issubset(trace[0]):
        errors.append("derivation_trace.csv is missing required fields")
    seen = {(row.get("USUBJID"), row.get("target_variable")) for row in trace}
    for subject in (row["USUBJID"] for row in exp["rows"]):
        for target in TRACE_TARGETS:
            if (subject, target) not in seen:
                errors.append(f"missing trace for {subject}/{target}")
    for row in trace:
        # Empty derived values are valid for censored/absent dates; require the
        # column and provenance fields, rather than treating a blank result as
        # a missing trace row.
        if not row.get("rule_id") or not row.get("source_rows") or "derived_value" not in row:
            errors.append("trace rows require rule_id, source_rows, and derived_value")
        if row.get("source_domain") not in {"DM", "EX", "DM+EX"}:
            errors.append(f"invalid trace source_domain for {row.get('USUBJID')}")

    try:
        report = json.loads(report_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        errors.append(f"invalid audit_report.json: {exc}")
        report = {}
    if report.get("schema_version") != "1.0":
        errors.append("audit_report.schema_version must be 1.0")
    if report.get("summary") != exp["summary"]:
        errors.append("audit_report.summary mismatch")
    if report.get("rules_version") != exp["rules_version"]:
        errors.append("audit_report.rules_version mismatch")
    if report.get("input_sha256") != exp["hashes"]:
        errors.append("audit_report.input_sha256 mismatch")
    if report.get("handoff", {}).get("decision") != "hold_for_review":
        errors.append("audit_report.handoff.decision must be hold_for_review")
    if report.get("edge_cases") != truth["edge_cases"]:
        errors.append("audit_report.edge_cases mismatch")
    boundary = str(report.get("claim_boundary", "")).lower()
    for phrase in ("synthetic", "not clinical", "not sponsor"):
        if phrase not in boundary:
            errors.append(f"audit_report.claim_boundary must mention {phrase}")

    notes = notes_path.read_text(encoding="utf-8").lower()
    for phrase in ("screen failure", "no exposure", "rfendtc", "cutoff", "synthetic"):
        if phrase not in notes:
            errors.append(f"derivation_notes.md is missing phrase: {phrase}")

    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        errors.append(f"invalid run_manifest.json: {exc}")
        manifest = {}
    if manifest.get("input_sha256") != exp["hashes"]:
        errors.append("run_manifest.input_sha256 mismatch")
    if manifest.get("rules_version") != exp["rules_version"]:
        errors.append("run_manifest.rules_version mismatch")
    if not manifest.get("tool_version"):
        errors.append("run_manifest.tool_version is required")
    if manifest.get("deterministic") is not True:
        errors.append("run_manifest.deterministic must be true")
    return not errors, errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--submission", type=Path, required=True)
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--reference", type=Path, required=True)
    args = parser.parse_args()
    ok, errors = verify(args.submission, args.data, args.reference)
    print(json.dumps({"passed": ok, "errors": errors}, ensure_ascii=False, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
