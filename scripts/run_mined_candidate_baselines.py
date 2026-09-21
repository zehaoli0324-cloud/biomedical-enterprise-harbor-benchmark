#!/usr/bin/env python3
"""Run author-side baseline strategies for the mined second tranche."""

from __future__ import annotations

import csv
import importlib.util
import json
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STRATEGIES = ("reference_solution", "simple_legal_baseline", "always_abstain", "template_or_keyword")


def load_verifier(task_id: str):
    spec = importlib.util.spec_from_file_location(f"{task_id}_baseline", ROOT / "benchmarks" / task_id / "verifier.py")
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load verifier for {task_id}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_json(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def eb003_reference(verifier, data: Path, output: Path) -> None:
    exp = verifier.expected(data)
    write_json(output / "replay_manifest.json", {"artifact_id": exp["artifact_id"], "rules_version": exp["rules_version"], "input_hashes": exp["input_hashes"], "output_hashes": exp["output_hashes"], "environment": exp["environment"], "replay_status": "reproduced"})
    (output / "provenance_diff.tsv").write_text("field\tstatus\ninput_hashes\tmatch\noutput_hashes\tmatch\nenvironment\tmatch\n", encoding="utf-8")
    (output / "handoff_replay_report.md").write_text("# Replay handoff\n\nReplay checksums and environment match. Human review remains required; this is not biological validation.\n", encoding="utf-8")


def eb009_reference(verifier, data: Path, output: Path) -> None:
    exp = verifier.expected(data)
    rows = list(csv.DictReader((data / "candidates.csv").open(newline="", encoding="utf-8")))
    with (output / "candidate_set.tsv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["candidate_id", "scaffold", "cluster", "valid"], delimiter="\t")
        writer.writeheader(); writer.writerows(rows)
    report = {key: exp[key] for key in ("candidate_count", "valid_count", "unique_valid_count", "scaffolds", "clusters", "coverage", "rules_version")}
    report["input_sha256"] = exp["hashes"]
    write_json(output / "diversity_report.json", report)
    (output / "coverage_review_gate.md").write_text("# Coverage review gate\n\nScaffold and cluster coverage pass for valid candidates. Human review remains required; computed diversity is not biological activity.\n", encoding="utf-8")
    write_json(output / "run_manifest.json", {"input_sha256": exp["hashes"], "rules_version": exp["rules_version"], "deterministic": True, "tool_version": "baseline-reference-v1"})


def mutate(task_id: str, strategy: str, output: Path) -> None:
    if strategy == "simple_legal_baseline":
        if task_id.startswith("eb003"):
            (output / "provenance_diff.tsv").unlink()
        else:
            (output / "run_manifest.json").unlink()
    elif strategy == "always_abstain":
        for path in output.iterdir():
            path.unlink()
    elif strategy == "template_or_keyword":
        if task_id.startswith("eb003"):
            manifest = json.loads((output / "replay_manifest.json").read_text())
            manifest["replay_status"] = "reproduced"
            manifest["input_hashes"] = {"inputs.tsv": "copied-from-template"}
            write_json(output / "replay_manifest.json", manifest)
        else:
            report = json.loads((output / "diversity_report.json").read_text())
            report["coverage"] = False
            write_json(output / "diversity_report.json", report)


def run_task(task_id: str) -> dict:
    verifier = load_verifier(task_id)
    task = ROOT / "benchmarks" / task_id
    records = []
    with tempfile.TemporaryDirectory(prefix=f"{task_id}-baselines-") as temp:
        root = Path(temp)
        for strategy in STRATEGIES:
            output = root / strategy
            output.mkdir()
            if task_id.startswith("eb003"):
                eb003_reference(verifier, task / "data", output)
            else:
                eb009_reference(verifier, task / "data", output)
            mutate(task_id, strategy, output)
            passed, errors = verifier.verify(output, task / "data", task / "verifier_only/reference.json")
            attribution = None if passed else ("artifact_completeness" if strategy == "simple_legal_baseline" else "claim_boundary_or_abstention" if strategy == "always_abstain" else "calculation_or_tool")
            records.append({"strategy": strategy, "status": "pass" if passed else "verifier_fail", "passed": passed, "error_count": len(errors), "failure_attribution": attribution, "errors": errors})
    return {"task_id": task_id, "protocol_version": "enterprise-model-trial.v1", "status": "BASELINES_COMPLETE", "target_model_status": "NOT_RUN", "records": records}


def main() -> int:
    results = [run_task("eb003-replay-provenance-004"), run_task("eb009-diversity-coverage-004")]
    for result in results:
        path = ROOT / "benchmarks" / result["task_id"] / "quality" / "model_trial_results.json"
        path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        card_path = ROOT / "benchmarks" / result["task_id"] / "quality" / "model_trial_card.json"
        card = json.loads(card_path.read_text(encoding="utf-8")); card["target_model_status"] = "NOT_RUN"; card["status"] = "BASELINES_COMPLETE"; card["run_records"] = result["records"]; card_path.write_text(json.dumps(card, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    payload = {"status": "BASELINES_COMPLETE", "tasks": results}
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if all(result["records"][0]["passed"] for result in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
