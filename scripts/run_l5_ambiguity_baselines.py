#!/usr/bin/env python3
"""Run author-side baselines for the L5.1 ambiguity task."""

from __future__ import annotations

import importlib.util
import json
import shutil
import tempfile
from pathlib import Path

from run_l5_ambiguity_controls import reference


ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "eb010-closed-loop-ambiguity-004"


def load():
    task = ROOT / "benchmarks" / TASK_ID
    spec = importlib.util.spec_from_file_location("ambiguity_baseline_verifier", task / "verifier.py")
    verifier = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(verifier)
    return task, verifier


def main() -> int:
    task, verifier = load()
    records = []
    for strategy in ("reference_solution", "simple_legal_baseline", "always_abstain", "template_or_keyword"):
        with tempfile.TemporaryDirectory(prefix=f"{TASK_ID}-{strategy}-") as temp:
            output = Path(temp) / "outputs"
            reference(task, verifier, output)
            if strategy == "simple_legal_baseline":
                decision = json.loads((output / "decision.json").read_text())
                decision["selected_record"] = "P-ARCHIVE"
                (output / "decision.json").write_text(json.dumps(decision))
            elif strategy == "always_abstain":
                shutil.rmtree(output)
                output.mkdir()
            elif strategy == "template_or_keyword":
                decision = json.loads((output / "decision.json").read_text())
                decision["selected_record"] = "P-BETA"
                decision["records"] = {"P-BETA": decision["records"]["P-BETA"]}
                (output / "decision.json").write_text(json.dumps(decision))
            passed, errors = verifier.verify(output, task / "data", task / "verifier_only/reference.json")
            records.append({
                "strategy": strategy,
                "status": "pass" if passed else "verifier_fail",
                "passed": passed,
                "error_count": len(errors),
                "failure_attribution": None if passed else ("artifact_completeness" if strategy == "always_abstain" else "method_choice"),
                "errors": errors,
            })

    result = {
        "task_id": TASK_ID,
        "protocol_version": "enterprise-model-trial.v1",
        "status": "BASELINES_COMPLETE",
        "target_model_status": "NOT_RUN",
        "records": records,
    }
    results_path = task / "quality/model_trial_results.json"
    results_path.write_text(json.dumps(result, indent=2) + "\n")
    card_path = task / "quality/model_trial_card.json"
    card = json.loads(card_path.read_text())
    card.update({"status": "BASELINES_COMPLETE", "target_model_status": "NOT_RUN", "run_records": records})
    card_path.write_text(json.dumps(card, indent=2) + "\n")
    sop_path = task / "quality/sop_card.json"
    sop = json.loads(sop_path.read_text())
    sop["model_trial_status"] = "BASELINES_COMPLETE"
    sop_path.write_text(json.dumps(sop, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    return 0 if records[0]["passed"] and all(not row["passed"] for row in records[1:]) else 1


if __name__ == "__main__":
    raise SystemExit(main())
