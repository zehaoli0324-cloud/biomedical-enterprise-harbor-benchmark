import csv
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("policy_regret_verifier", ROOT / "verifier.py")
verifier = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(verifier)


def write_reference(output):
    exp = verifier.expected(ROOT / "data")
    output.mkdir(exist_ok=True)
    (output / "policy.json").write_text(json.dumps({"selected_policy": exp["selected_policy"], "rules_version": exp["rules_version"], "claim_boundary": "planning_only_not_experimental_proof", "human_review_required": True, "policies": exp["policies"]}))
    fields = ["policy_id", "scenario_id", "observation", "action", "total_cost", "utility", "regret", "eligible", "blockers"]
    with (output / "branches.tsv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, delimiter="\t"); writer.writeheader()
        for pid, policy in exp["policies"].items():
            for sid, branch in policy["branches"].items(): writer.writerow({"policy_id": pid, "scenario_id": sid, **branch, "eligible": str(policy["eligible"]).lower(), "blockers": ";".join(policy["blockers"])})
    (output / "manifest.json").write_text(json.dumps({"input_sha256": exp["hashes"], "rules_version": exp["rules_version"], "deterministic": True}))
    (output / "audit.md").write_text("Minimax regret, budget, future outcome, branch completeness and human review are explicit. This is not experimental proof.")


def test_reference_oracle_matches_recomputation():
    exp = verifier.expected(ROOT / "data")
    ref = json.loads((ROOT / "verifier_only/reference.json").read_text())
    assert exp["selected_policy"] == ref["selected_policy"] == "P-ROBUST"


def test_reference_passes(tmp_path):
    write_reference(tmp_path)
    assert verifier.verify(tmp_path, ROOT / "data", ROOT / "verifier_only/reference.json") == (True, [])


def test_missing_submission_fails(tmp_path):
    passed, errors = verifier.verify(tmp_path, ROOT / "data", ROOT / "verifier_only/reference.json")
    assert not passed and errors


def test_greedy_and_overrun_do_not_win():
    exp = verifier.expected(ROOT / "data")
    assert exp["policies"]["P-GREEDY"]["mean_utility"] > exp["policies"]["P-STOP"]["mean_utility"]
    assert exp["policies"]["P-GREEDY"]["max_regret"] > exp["policies"]["P-ROBUST"]["max_regret"]
    assert exp["policies"]["P-OVERRUN"]["blockers"] == ["budget"]


def test_cross_artifact_branch_numeric_mutation_fails(tmp_path):
    write_reference(tmp_path)
    lines = (tmp_path / "branches.tsv").read_text().splitlines()
    header = lines[0].split("\t")
    values = lines[1].split("\t")
    values[header.index("utility")] = "999.0"
    lines[1] = "\t".join(values)
    (tmp_path / "branches.tsv").write_text("\n".join(lines) + "\n")
    passed, errors = verifier.verify(tmp_path, ROOT / "data", ROOT / "verifier_only/reference.json")
    assert not passed
    assert any("branch evidence utility mismatch" in error for error in errors)
