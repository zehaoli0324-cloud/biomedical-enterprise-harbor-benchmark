"""Public completion checks, deliberately separate from scientific answer scoring.

Local replay executes submitted code. It is not a security sandbox; use container
isolation before running adversarial/untrusted submissions in production.
"""
from __future__ import annotations

import csv
import hashlib
import json
import os
import shutil
import signal
import subprocess
import sys
from pathlib import Path


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n")


def load(path):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("duplicate JSON key")
            result[key] = value
        return result
    def invalid(value):
        raise ValueError("non-finite JSON number")
    return json.loads(path.read_text(), object_pairs_hook=unique, parse_constant=invalid)


def canonical(value):
    if isinstance(value, dict):
        return {key: canonical(v) for key, v in value.items()}
    if isinstance(value, list):
        if value and all(isinstance(row, dict) and isinstance(row.get("id"), str) for row in value):
            return sorted((canonical(row) for row in value), key=lambda row: row["id"])
        return [canonical(v) for v in value]
    return value


def run_program(script, data, out, log, timeout=15):
    out.mkdir(parents=True, exist_ok=False)
    command = [sys.executable, str(script), "--data", str(data), "--out", str(out)]
    env = {key: value for key, value in os.environ.items() if key in {"PATH", "LANG", "LC_ALL", "TMPDIR"}}
    with log.open("w") as handle:
        process = subprocess.Popen(command, cwd=out, env=env, stdout=handle, stderr=subprocess.STDOUT, start_new_session=True)
        try:
            code = process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait()
            code = 124
    return {"command": command, "exit_code": code, "log_sha256": digest(log)}


def check(submission, data, archive):
    archive.mkdir(parents=True, exist_ok=False)
    contract = load(data / "research_contract.json")
    issues, runs = [], []
    for name in contract["required_files"]:
        path = submission / name
        if not path.is_file() or path.is_symlink() or not path.stat().st_size:
            issues.append("missing_or_invalid_artifact:" + name)
    result = None
    if not issues:
        try:
            result = load(submission / "results.json")
            for name, spec in contract["tables"].items():
                rows = result.get(name) if isinstance(result, dict) else None
                if not isinstance(rows, list) or not all(isinstance(row, dict) for row in rows):
                    issues.append("missing_table:" + name)
                    continue
                ids = [row.get("id") for row in rows]
                if any(not isinstance(key, str) for key in ids) or len(set(ids)) != len(ids) or set(ids) != set(spec["ids"]):
                    issues.append("record_coverage:" + name)
                if any(not set(spec["fields"]).issubset(row) for row in rows):
                    issues.append("missing_fields:" + name)
            decision = result.get("decision") if isinstance(result, dict) else None
            if not isinstance(decision, dict) or not set(contract["decision_fields"]).issubset(decision):
                issues.append("missing_fields:decision")
            load(submission / "provenance.json")
        except (ValueError, OSError, TypeError):
            issues.append("unreadable_structured_artifact")
    if not issues:
        source_hashes = {p.name: digest(p) for p in submission.iterdir() if p.is_file()}
        for mode in ("replay_a", "replay_b", "row_order"):
            copied = archive / (mode + "_data")
            shutil.copytree(data, copied)
            if mode == "row_order":
                path = copied / "observations.csv"
                with path.open(newline="") as handle:
                    reader = csv.DictReader(handle)
                    fields, rows = reader.fieldnames, list(reader)
                with path.open("w", newline="") as handle:
                    writer = csv.DictWriter(handle, fieldnames=fields)
                    writer.writeheader()
                    writer.writerows(reversed(rows))
            before = {p.name: digest(p) for p in copied.iterdir() if p.is_file()}
            script = archive / (mode + ".py")
            shutil.copy2(submission / "analysis.py", script)
            run = run_program(script.resolve(), copied.resolve(), (archive / mode).resolve(), archive / (mode + ".log"), contract["replay_timeout_seconds"])
            runs.append(dict(run, mode=mode, script_sha256=digest(script)))
            if run["exit_code"]:
                issues.append("replay_execution_failed:" + mode)
                continue
            if before != {p.name: digest(p) for p in copied.iterdir() if p.is_file()}:
                issues.append("replay_modified_inputs:" + mode)
            try:
                replay = load(archive / mode / "results.json")
                if canonical(replay) != canonical(result):
                    issues.append("replay_inconsistent:" + mode)
            except (OSError, ValueError):
                issues.append("replay_missing_results:" + mode)
        if source_hashes != {p.name: digest(p) for p in submission.iterdir() if p.is_file()}:
            issues.append("submission_changed_during_check")
    receipt = {
        "accepted": not issues, "issues": sorted(set(issues)), "runs": runs,
        "feedback_boundary": "Completion and reproducibility only; no hidden scientific answers returned.",
    }
    save(archive / "receipt.json", receipt)
    return receipt
