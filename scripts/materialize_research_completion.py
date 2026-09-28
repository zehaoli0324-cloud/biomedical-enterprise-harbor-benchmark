"""Build a separate research-completion variant; never modify the parent task."""
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TASK = ROOT / "benchmarks/eb006-research-completion-006"


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n")


def main():
    if (TASK / "quality/pretrial_freeze.json").exists():
        raise RuntimeError("Frozen task exists; create a versioned variant instead of overwriting")
    source = ROOT / "benchmarks/eb006-donor-stratified-signal-005/data"
    with (source / "observations.csv").open(newline="") as handle:
        reader = csv.DictReader(handle)
        fields, rows = reader.fieldnames, list(reader)
    labels = {"method_alpha": "C17", "method_beta": "C28", "method_gamma": "C43", "method_shadow": "C90"}
    alpha = {"D1": "1.52", "D2": "1.40", "D3": "1.59", "D4": "1.48"}
    gamma = {"D1": "1.68", "D2": "1.35", "D3": "1.52"}
    for row in rows:
        if row["state"] == "late" and row["condition"] == "treatment":
            if row["candidate_id"] == "method_alpha":
                row["adjusted_signal"] = alpha[row["donor"]]
            if row["candidate_id"] == "method_gamma" and row["donor"] in gamma:
                row["adjusted_signal"] = gamma[row["donor"]]
        row["candidate_id"] = labels[row["candidate_id"]]
    data = TASK / "data"
    data.mkdir(parents=True, exist_ok=True)
    with (data / "observations.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    policy = json.loads((source / "policy.json").read_text())
    policy["active_candidates"] = [labels[c] for c in policy["active_candidates"]]
    policy["rules_version"] = "research-completion-v1"
    policy["minimum_state_mean_effect"]["late"] = 0.35
    policy["scenarios"] = ["base"] + ["omit:" + d for d in policy["registered_donors"]]
    policy["sensitivity_count_rule"] = "In omission scenarios use max(2, original state minimum - 1), even if the omitted donor was already unidentifiable. Keep effect and range thresholds unchanged."
    policy["selection_rule"] = ["nominal: SUPPORTED in all base states; largest worst state mean then lexical ID", "pooled diagnostic: largest minimum pooled state effect then lexical ID; ignores support gates", "robust: SUPPORTED in every state of base and every omission scenario; largest minimum paired state mean over all scenarios then lexical ID; null when none"]
    policy["precision"] = "Compute using exact decimal or rational arithmetic; round reported numbers half-up to six decimal places. Apply thresholds and rankings before rounding."
    write(data / "policy.json", policy)
    cs, ss, ds = policy["active_candidates"], policy["registered_states"], policy["registered_donors"]
    tables = {
        "unit_effects": {"ids": ["|".join([c,s,d]) for c in cs for s in ss for d in ds], "fields": ["id", "effect", "control_rows", "treatment_rows"]},
        "checks": {"ids": ["|".join([x,c,s]) for x in policy["scenarios"] for c in cs for s in ss], "fields": ["id", "count", "missing_donors", "nonpositive_donors", "mean_effect", "effect_range", "status"]},
        "pooled": {"ids": ["|".join([c,s]) for c in cs for s in ss], "fields": ["id", "effect", "control_rows", "treatment_rows"]},
        "summaries": {"ids": cs, "fields": ["id", "nominal_eligible", "robust_eligible", "nominal_worst_mean", "robust_worst_mean", "pooled_worst_mean", "failed_scenarios"]},
    }
    write(data / "research_contract.json", {
        "required_files": ["analysis.py", "results.json", "provenance.json", "research_audit.md"],
        "tables": tables,
        "decision_fields": ["nominal_selected", "pooled_selected", "selected", "reason_codes", "claim_boundary", "human_review_required"],
        "replay_timeout_seconds": 10,
        "max_submission_attempts": 3,
        "shared_model_seconds": 840,
        "program_interface": "Standalone Python standard-library analysis.py --data DATA_DIRECTORY --out OUTPUT_DIRECTORY must write results.json. Resolve all inputs from --data, not a fixed path. It must work with altered measurements, row order and equivalent schema. It may additionally write provenance and audit. Each clean replay has a 10-second limit; no network or subprocesses in submitted analysis code.",
        "completion_gate": "At a normal model turn end, the system checks required artifacts, exact public record coverage and required fields, then executes the submitted code in three clean directories (two identical inputs, one reversed row order). Replay results must agree semantically with submitted results. Real missing requirements are returned, at most three submissions within one shared budget. No hidden scientific scores or expected numbers are fed back. Complete first submissions are accepted immediately.",
        "scientific_verifier": "After the gate, independent scoring checks numerical correctness, decisions and the submitted program on measurement perturbations. Perturbation expected results are never feedback during repair. Completion acceptance is not scientific correctness.",
        "formats": "results.json is an object with exactly the four tables and decision. Each table is an array with one object for each declared id. Row/object key order does not matter. ID arrays are sorted and duplicate-free. Numeric fields are JSON numbers, missing effects are null, and flags are booleans. All listed fields required; no extra fields. Scientific numeric tolerance 1e-6. Duplicate keys/IDs and non-finite numbers forbidden.",
        "field_semantics": {
            "unit_effects": "Base condition counts and treatment mean minus control mean for each registered donor/state; effect null if either condition missing. Exclude inactive candidates, unregistered donors/states/conditions and non-PASS or empty values.",
            "checks": "Recompute equal-weight identifiable donor effects for each scenario. Omitted donor is not in missing_donors. Status follows policy.decision_precedence. Count below scenario minimum gives INSUFFICIENT, else any effect <=0 CONTRADICTORY, else mean below minimum or range above maximum WEAK, else SUPPORTED. Empty mean/range are null.",
            "pooled": "Base unpaired treatment row mean minus control row mean on eligible observations, including a one-sided row from an unpaired donor. No donor equal weighting. Report condition row counts; effect null if either group empty. This is an alternative explanation diagnostic, not a replacement estimand.",
            "summaries": "All numeric minima are reported even if ineligible; null if any needed mean missing. nominal_eligible means all base states SUPPORTED. robust_eligible means all scenarios/states SUPPORTED. failed_scenarios lists every scenario with any non-SUPPORTED state. Rank using unrounded means and policy.selection_rule.",
            "decision": "Use policy selection rules for three winner fields. reason_codes contains pooled_ranking_disagrees when pooled differs from nominal; nominal_selection_not_robust when nominal differs from robust; technical_replication_imbalance when base control or treatment row counts differ across registered donors within any candidate/state; missing_pair_evidence when any base donor effect is null. claim_boundary copies policy.claim_boundary; human_review_required is true.",
            "provenance": "input_sha256 contains all three data filenames (no directory prefix) and SHA-256; rules_version, network=off, deterministic=true. analysis_sha256 hashes submitted analysis.py. Do not fabricate runner execution receipts.",
            "research_audit": "Explain the competing estimands, coverage, observed disagreements, influential donors and conclusion boundary. Presence checked automatically; prose scientific review is separate."
        }
    })


if __name__ == "__main__":
    main()
