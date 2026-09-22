#!/usr/bin/env python3
"""Archive and replay the cross-context target trial against its frozen contract."""
from __future__ import annotations

import argparse
import importlib.util
import json
import shutil
from pathlib import Path

from record_shared_setup_trial import ROOT, archive, read, write

TASK = ROOT / "benchmarks/eb013-cross-context-evidence-portfolio-005"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--trial", required=True, type=Path)
    args = parser.parse_args()
    record = archive(args.trial, task=TASK)
    status = "PASS" if record["passed"] else "FAIL"
    record["raw_verdict_class"] = "RAW_PASS" if record["passed"] else "FAIL_REQUIRES_ATTRIBUTION"
    record["trial_analysis"] = "The revised contract explicitly nests provenance hashes under input_sha256."
    for filename, key in (("model_trial_results.json", "records"), ("model_trial_card.json", "run_records")):
        path = TASK / "quality" / filename
        payload = read(path)
        payload.update(status="COMPLETED", target_model_status=status)
        payload[key] = [r for r in payload[key] if r.get("trial_id") != record["trial_id"]] + [record]
        write(path, payload)
    for path in (TASK / "quality/sop_card.json", ROOT / "candidate_pools/enterprise-v1/cross_context_portfolio_escalation.json"):
        payload = read(path)
        key = "model_trial_status" if path.name == "sop_card.json" else "target_model_status"
        payload[key] = status
        if path.name != "sop_card.json":
            payload["status"] = "TARGET_TRIAL_COMPLETE"
        payload["release_blockers"] = [b for b in payload["release_blockers"] if b != "target-model trial"]
        write(path, payload)
    write(TASK / "quality/target_trial_evidence.json", record)
    analysis = TASK / "quality/trial_analysis.md"
    with analysis.open("a", encoding="utf-8") as handle:
        handle.write(f"\n## {record['trial_id']}\n\nThe revised trial replay status is `{status}`.\n")
    print(status, record["trial_id"], record["replay_errors"])


if __name__ == "__main__":
    main()
