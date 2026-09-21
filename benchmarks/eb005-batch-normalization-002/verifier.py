from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def expected(data: Path) -> dict:
    rows = list(csv.DictReader((data / "plates.csv").open()))
    rules = json.loads((data / "rules.json").read_text())
    batches = sorted({row["batch"] for row in rows})
    profiles = {}
    raw_effect = None
    for profile in rules["candidate_profiles"]:
        controls = {
            batch: sum(float(row[profile]) for row in rows if row["batch"] == batch and row["condition"] == "control")
            / sum(1 for row in rows if row["batch"] == batch and row["condition"] == "control")
            for batch in batches
        }
        effects = {}
        for batch in batches:
            treatment = [float(row[profile]) for row in rows if row["batch"] == batch and row["condition"] == "treatment"]
            control = [float(row[profile]) for row in rows if row["batch"] == batch and row["condition"] == "control"]
            effects[batch] = sum(treatment) / len(treatment) - sum(control) / len(control)
        all_treatment = [float(row[profile]) for row in rows if row["condition"] == "treatment"]
        all_control = [float(row[profile]) for row in rows if row["condition"] == "control"]
        effect = sum(all_treatment) / len(all_treatment) - sum(all_control) / len(all_control)
        if profile == "raw_signal":
            raw_effect = effect
        profiles[profile] = {
            "control_batch_means": {key: round(value, 6) for key, value in controls.items()},
            "control_batch_range": round(max(controls.values()) - min(controls.values()), 6),
            "within_batch_effects": {key: round(value, 6) for key, value in effects.items()},
            "treatment_control_effect": round(effect, 6),
        }
    assert raw_effect is not None and raw_effect != 0
    for values in profiles.values():
        retention = abs(values["treatment_control_effect"] / raw_effect)
        direction_preserved = all(effect * raw_effect > 0 for effect in values["within_batch_effects"].values())
        values["effect_retention_fraction"] = round(retention, 6)
        values["direction_preserved"] = direction_preserved
        values["eligible"] = (
            values["control_batch_range"] <= rules["max_control_batch_range"]
            and retention >= rules["min_effect_retention_fraction"]
            and direction_preserved
        )
    eligible = [name for name, values in profiles.items() if values["eligible"]]
    recommended = min(eligible, key=lambda name: (profiles[name]["control_batch_range"], -profiles[name]["effect_retention_fraction"], name))
    return {
        "profiles": profiles,
        "recommended": recommended,
        "hashes": {"plates.csv": sha(data / "plates.csv"), "rules.json": sha(data / "rules.json")},
        "rules_version": rules["rules_version"],
    }


def _manifest_hashes(manifest: dict) -> dict | None:
    for key in ("input_sha256", "inputs"):
        value = manifest.get(key)
        if isinstance(value, dict):
            result = {str(name).removeprefix("data/"): digest for name, digest in value.items()}
            result.pop("instruction.md", None)
            return result
        if isinstance(value, list) and all(isinstance(item, dict) for item in value):
            result = {item.get("path", "").removeprefix("data/"): item.get("sha256") for item in value}
            result.pop("instruction.md", None)
            return result
    return None


def verify(submission: Path, data: Path, reference: Path) -> tuple[bool, list[str]]:
    exp, errors = expected(data), []
    for name in ("normalization_comparison.tsv", "batch_report.json", "sensitivity_summary.md", "run_manifest.json"):
        if not (submission / name).is_file():
            errors.append("missing artifact: " + name)
    if errors:
        return False, errors
    report = json.loads((submission / "batch_report.json").read_text())
    if report.get("recommended", report.get("recommended_profile")) != exp["recommended"]:
        errors.append("normalization recommendation mismatch")
    submitted_profiles = report.get("profiles", report.get("profile_metrics", {}))
    for name, expected_values in exp["profiles"].items():
        values = submitted_profiles.get(name, {}) if isinstance(submitted_profiles, dict) else {}
        for field in ("control_batch_range", "effect_retention_fraction", "eligible"):
            actual = values.get(field)
            expected_value = expected_values[field]
            if isinstance(expected_value, float):
                if not isinstance(actual, (int, float)) or abs(actual - expected_value) > 1e-5:
                    errors.append(f"{name} {field} mismatch")
            elif actual != expected_value:
                errors.append(f"{name} {field} mismatch")
    table_header = (submission / "normalization_comparison.tsv").read_text().splitlines()[0].split("\t")
    for field in ("batch", "condition", "replicate", *exp["profiles"]):
        if field not in table_header:
            errors.append("comparison missing column: " + field)
    text = (submission / "sensitivity_summary.md").read_text().lower()
    for concept, terms in {
        "batch identifiability": ("batch", "identifi"),
        "control evidence": ("control",),
        "phenotype retention": ("phenotype", "effect retention"),
        "over-correction": ("over-correction", "overcorrection", "erasing"),
    }.items():
        if not any(term in text for term in terms):
            errors.append("sensitivity summary omits " + concept)
    manifest = json.loads((submission / "run_manifest.json").read_text())
    if _manifest_hashes(manifest) != exp["hashes"] or manifest.get("rules_version", manifest.get("analysis_version")) != exp["rules_version"]:
        errors.append("manifest provenance mismatch")
    if not (manifest.get("deterministic") is True or manifest.get("reproducibility", {}).get("deterministic") is True):
        errors.append("manifest must declare deterministic execution")
    return not errors, errors


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--submission", type=Path, required=True)
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--reference", type=Path, required=True)
    args = parser.parse_args()
    ok, errors = verify(args.submission, args.data, args.reference)
    print(json.dumps({"passed": ok, "errors": errors}))
    raise SystemExit(0 if ok else 1)
