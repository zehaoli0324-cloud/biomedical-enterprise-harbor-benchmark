from __future__ import annotations

import argparse
import csv
import hashlib
import json
from datetime import date
from pathlib import Path


FIELDS = ["USUBJID", "PARAMCD", "TRTSDT", "ADT", "CNSR", "EVNTDESC", "ADT_DTYPE", "DERIVATION_STATUS"]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_exact(value: str, precision: str) -> date | None:
    if precision != "DAY" or len(value) != 10:
        return None
    return date.fromisoformat(value)


def expected(data_dir: Path) -> dict:
    dm = read_csv(data_dir / "dm.csv")
    events = read_csv(data_dir / "events.csv")
    followup = read_csv(data_dir / "followup.csv")
    rules = json.loads((data_dir / "rules.json").read_text(encoding="utf-8"))
    cutoff = date.fromisoformat(rules["analysis_cutoff"])
    by_event: dict[str, list[dict[str, str]]] = {}
    by_followup: dict[str, list[dict[str, str]]] = {}
    for row in events:
        by_event.setdefault(row["USUBJID"], []).append(row)
    for row in followup:
        by_followup.setdefault(row["USUBJID"], []).append(row)

    rows: list[dict[str, str]] = []
    edge_cases: list[dict[str, str]] = []
    trace: list[dict[str, str]] = []
    for subject in sorted(dm, key=lambda row: row["USUBJID"]):
        sid = subject["USUBJID"]
        exact_events = []
        partial_events = []
        for event in by_event.get(sid, []):
            parsed = parse_exact(event["EVENTDTC"], event["DATE_PRECISION"])
            if parsed is None:
                partial_events.append(event)
                trace.append({"USUBJID": sid, "source_record": f"EVENT:{event['EVSEQ']}", "event_type": event["EVENTTYPE"], "raw_date": event["EVENTDTC"], "date_precision": event["DATE_PRECISION"], "rule_id": "partial_date_rule", "selected_value": "REVIEW"})
            elif parsed <= cutoff:
                exact_events.append((parsed, event))
                trace.append({"USUBJID": sid, "source_record": f"EVENT:{event['EVSEQ']}", "event_type": event["EVENTTYPE"], "raw_date": event["EVENTDTC"], "date_precision": event["DATE_PRECISION"], "rule_id": "event_rule", "selected_value": event["EVENTDTC"]})
            else:
                trace.append({"USUBJID": sid, "source_record": f"EVENT:{event['EVSEQ']}", "event_type": event["EVENTTYPE"], "raw_date": event["EVENTDTC"], "date_precision": event["DATE_PRECISION"], "rule_id": "post_cutoff_rule", "selected_value": "CUTOFF"})
        if partial_events:
            adt, cnsr, desc, dtype, status = "", "", "REVIEW_PARTIAL_DATE", "REVIEW", "REVIEW"
            edge_cases.append({"id": sid, "type": "partial_date"})
        elif exact_events:
            priority = {name: index for index, name in enumerate(rules["event_priority"])}
            parsed, event = min(exact_events, key=lambda item: (item[0], priority.get(item[1]["EVENTTYPE"], 99)))
            adt, cnsr, desc, dtype, status = event["EVENTDTC"], "0", event["EVENTTYPE"], "NONE", "DERIVED"
            if len(exact_events) > 1:
                edge_cases.append({"id": sid, "type": "competing_events"})
        else:
            post_cutoff_events = [
                event for event in by_event.get(sid, [])
                if parse_exact(event["EVENTDTC"], event["DATE_PRECISION"]) is not None
                and parse_exact(event["EVENTDTC"], event["DATE_PRECISION"]) > cutoff
            ]
            if post_cutoff_events:
                adt, cnsr, desc, dtype, status = rules["analysis_cutoff"], "1", "CENSORED_AT_CUTOFF", "CUTOFF", "DERIVED"
                edge_cases.append({"id": sid, "type": "post_cutoff_event"})
            else:
                exact_followups = []
                for record in by_followup.get(sid, []):
                    parsed = parse_exact(record["LASTASMTDTC"], record["DATE_PRECISION"])
                    if parsed is not None and parsed <= cutoff:
                        exact_followups.append(parsed)
                        trace.append({"USUBJID": sid, "source_record": f"FU:{record['FUSEQ']}", "event_type": "FOLLOWUP", "raw_date": record["LASTASMTDTC"], "date_precision": record["DATE_PRECISION"], "rule_id": "censor_rule", "selected_value": record["LASTASMTDTC"]})
                if exact_followups:
                    adt, cnsr, desc, dtype, status = max(exact_followups).isoformat(), "1", "CENSORED", "NONE", "DERIVED"
                else:
                    adt, cnsr, desc, dtype, status = "", "", "REVIEW_MISSING_FOLLOWUP", "REVIEW", "REVIEW"
                    edge_cases.append({"id": sid, "type": "missing_followup"})
        rows.append({"USUBJID": sid, "PARAMCD": rules["parameter"], "TRTSDT": subject["TRTSDT"], "ADT": adt, "CNSR": cnsr, "EVNTDESC": desc, "ADT_DTYPE": dtype, "DERIVATION_STATUS": status})
    hashes = {name: sha256(data_dir / name) for name in ("dm.csv", "events.csv", "followup.csv", "rules.json")}
    summary = {"subject_count": len(rows), "event_count": sum(row["CNSR"] == "0" for row in rows), "censor_count": sum(row["CNSR"] == "1" for row in rows), "review_count": sum(row["DERIVATION_STATUS"] == "REVIEW" for row in rows)}
    return {"rows": rows, "trace": trace, "summary": summary, "edge_cases": edge_cases, "hashes": hashes, "rules_version": rules["rules_version"]}


def verify(submission: Path, data_dir: Path, reference_path: Path) -> tuple[bool, list[str]]:
    truth = json.loads(reference_path.read_text(encoding="utf-8"))
    exp = expected(data_dir)
    errors: list[str] = []
    adtte_path = submission / "adtte.csv"
    trace_path = submission / "event_trace.csv"
    report_path = submission / "censoring_audit.json"
    manifest_path = submission / "run_manifest.json"
    for path in (adtte_path, trace_path, report_path, manifest_path):
        if not path.exists():
            errors.append(f"missing artifact: {path.name}")
    if errors:
        return False, errors
    rows = read_csv(adtte_path)
    if rows != exp["rows"]:
        errors.append("adtte.csv rows do not match independent endpoint derivation")
    if not rows or list(rows[0]) != FIELDS:
        errors.append("adtte.csv has the wrong header")
    trace = read_csv(trace_path)
    required_trace = {tuple(item.values()) for item in exp["trace"]}
    actual_trace = {tuple(row.get(key, "") for key in exp["trace"][0]) for row in trace} if exp["trace"] else set()
    if not required_trace.issubset(actual_trace):
        errors.append("event_trace.csv is missing evidence rows")
    try:
        report = json.loads(report_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        report = {}
        errors.append(f"invalid censoring_audit.json: {exc}")
    if report.get("schema_version") != "1.0":
        errors.append("censoring_audit.schema_version must be 1.0")
    if report.get("input_sha256") != exp["hashes"] or report.get("rules_version") != exp["rules_version"]:
        errors.append("censoring_audit provenance mismatch")
    if report.get("summary") != exp["summary"] or report.get("edge_cases") != truth["edge_cases"]:
        errors.append("censoring_audit summary or edge_cases mismatch")
    if report.get("handoff", {}).get("decision") != "hold_for_review":
        errors.append("handoff.decision must be hold_for_review")
    boundary = str(report.get("claim_boundary", "")).lower()
    for phrase in ("synthetic", "not sponsor", "not efficacy"):
        if phrase not in boundary:
            errors.append(f"claim_boundary must mention {phrase}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("input_sha256") != exp["hashes"] or manifest.get("rules_version") != exp["rules_version"]:
        errors.append("run_manifest provenance mismatch")
    if not manifest.get("tool_version") or manifest.get("deterministic") is not True:
        errors.append("run_manifest requires tool_version and deterministic=true")
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
