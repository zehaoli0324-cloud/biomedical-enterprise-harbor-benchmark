#!/usr/bin/env python3
"""Keep raw output and unchanged frozen replay for the partial-observation trial."""
import argparse
from pathlib import Path

from record_shared_setup_trial import ROOT, archive, read, write

TASK = ROOT / "benchmarks/eb013-partial-observation-risk-004"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--trial", type=Path, required=True)
    args = parser.parse_args()
    record = archive(args.trial, task=TASK)
    status = "PASS" if record["passed"] else "FAIL"
    record["raw_verdict_class"] = "RAW_PASS" if record["passed"] else "FAIL_REQUIRES_ATTRIBUTION"
    for filename, key in (("model_trial_results.json", "records"), ("model_trial_card.json", "run_records")):
        path = TASK / "quality" / filename
        payload = read(path)
        payload.update(status="COMPLETED", target_model_status=status)
        payload[key] = [r for r in payload[key] if r.get("trial_id") != record["trial_id"]] + [record]
        write(path, payload)
    for path in (TASK / "quality/sop_card.json", ROOT / "candidate_pools/enterprise-v1/partial_observation_escalation.json"):
        payload = read(path)
        key = "model_trial_status" if path.name == "sop_card.json" else "target_model_status"
        payload[key] = status
        if path.name != "sop_card.json":
            payload["status"] = "TARGET_TRIAL_COMPLETE"
        payload["release_blockers"] = [b for b in payload["release_blockers"] if b != "target-model trial"]
        write(path, payload)
    write(TASK / "quality/target_trial_evidence.json", record)
    print(status, record["trial_id"], record["replay_errors"])


if __name__ == "__main__":
    main()
