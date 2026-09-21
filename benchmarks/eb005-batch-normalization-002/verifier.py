from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _as_bool(value):
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        if value.strip().lower() in {"true", "yes", "1"}:
            return True
        if value.strip().lower() in {"false", "no", "0"}:
            return False
    return None


def expected(data: Path) -> dict:
    plates = list(csv.DictReader((data / "plates.csv").open()))
    metadata_rows = list(csv.DictReader((data / "plate_metadata.csv").open()))
    rules = json.loads((data / "rules.json").read_text())
    if len({row["plate"] for row in plates}) != len(plates):
        raise ValueError("plates.csv contains duplicate plate identifiers")
    if len({row["plate"] for row in metadata_rows}) != len(metadata_rows):
        raise ValueError("plate_metadata.csv contains duplicate plate identifiers")
    metadata = {row["plate"]: row for row in metadata_rows}
    if set(metadata) != {row["plate"] for row in plates}:
        raise ValueError("plate metadata must cover exactly the observed plates")

    joined = [
        {
            **row,
            "analysis_scope": metadata[row["plate"]]["analysis_scope"],
            "qc_pass": metadata[row["plate"]]["qc_pass"].lower() == "true",
        }
        for row in plates
    ]
    selected = [
        row
        for row in joined
        if row["analysis_scope"] == rules["analysis_scope"] and row["qc_pass"]
    ]
    excluded = sorted(row["plate"] for row in joined if row not in selected)
    batches = sorted({row["batch"] for row in selected})
    conditions = sorted({row["condition"] for row in selected})
    cell_counts = {
        f"{batch}|{condition}": len(
            {row["replicate"] for row in selected if row["batch"] == batch and row["condition"] == condition}
        )
        for batch in batches
        for condition in conditions
    }
    required_cells = {
        f"{batch}|{condition}" for batch in batches for condition in ("control", "treatment")
    }
    evidence_complete = bool(batches) and all(
        cell_counts.get(cell, 0) >= rules["min_replicates_per_batch_condition"]
        for cell in required_cells
    )

    profiles = {}
    raw_effect = None
    for profile in rules["candidate_profiles"]:
        controls = {}
        effects = {}
        for batch in batches:
            control = [float(row[profile]) for row in selected if row["batch"] == batch and row["condition"] == "control"]
            treatment = [float(row[profile]) for row in selected if row["batch"] == batch and row["condition"] == "treatment"]
            if not control or not treatment:
                raise ValueError(f"missing control or treatment evidence for {batch}")
            controls[batch] = sum(control) / len(control)
            effects[batch] = sum(treatment) / len(treatment) - controls[batch]
        all_treatment = [float(row[profile]) for row in selected if row["condition"] == "treatment"]
        all_control = [float(row[profile]) for row in selected if row["condition"] == "control"]
        if not all_treatment or not all_control:
            raise ValueError("analysis scope lacks treatment or control rows")
        effect = sum(all_treatment) / len(all_treatment) - sum(all_control) / len(all_control)
        if profile == "raw_signal":
            raw_effect = effect
        profiles[profile] = {
            "control_batch_means": {key: round(value, 6) for key, value in controls.items()},
            "control_batch_range": round(max(controls.values()) - min(controls.values()), 6),
            "within_batch_effects": {key: round(value, 6) for key, value in effects.items()},
            "treatment_control_effect": round(effect, 6),
        }
    if raw_effect is None or raw_effect == 0:
        raise ValueError("raw phenotype effect is not identifiable")

    for values in profiles.values():
        retention = abs(values["treatment_control_effect"] / raw_effect)
        direction_preserved = all(effect * raw_effect > 0 for effect in values["within_batch_effects"].values())
        blockers = []
        if not evidence_complete:
            blockers.append("evidence_incomplete")
        if values["control_batch_range"] > rules["max_control_batch_range"]:
            blockers.append("control_batch_range")
        if retention < rules["min_effect_retention_fraction"]:
            blockers.append("effect_retention")
        if rules.get("require_within_batch_direction", True) and not direction_preserved:
            blockers.append("direction_reversal")
        values["effect_retention_fraction"] = round(retention, 6)
        values["direction_preserved"] = direction_preserved
        values["blocker_reasons"] = blockers
        values["eligible"] = not blockers
    eligible = [name for name, values in profiles.items() if values["eligible"]]
    recommended = min(
        eligible,
        key=lambda name: (
            profiles[name]["control_batch_range"],
            -profiles[name]["effect_retention_fraction"],
            name,
        ),
    ) if eligible else None
    return {
        "profiles": profiles,
        "recommended": recommended,
        "evidence_complete": evidence_complete,
        "cell_counts": cell_counts,
        "included_plates": sorted(row["plate"] for row in selected),
        "excluded_plates": excluded,
        "joined_rows": joined,
        "hashes": {
            name: sha(data / name)
            for name in ("plates.csv", "plate_metadata.csv", "rules.json")
        },
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
    if report.get("evidence_complete") != exp["evidence_complete"]:
        errors.append("evidence completeness mismatch")
    if report.get("cell_counts") != exp["cell_counts"]:
        errors.append("batch-condition evidence counts mismatch")
    if sorted(report.get("excluded_plates", [])) != exp["excluded_plates"]:
        errors.append("scope exclusions mismatch")
    submitted_profiles = report.get("profiles", report.get("profile_metrics", {}))
    for name, expected_values in exp["profiles"].items():
        values = submitted_profiles.get(name, {}) if isinstance(submitted_profiles, dict) else {}
        for field in (
            "control_batch_range",
            "effect_retention_fraction",
            "direction_preserved",
            "blocker_reasons",
            "eligible",
        ):
            actual = values.get(field)
            expected_value = expected_values[field]
            if isinstance(expected_value, float):
                if not isinstance(actual, (int, float)) or abs(actual - expected_value) > 1e-5:
                    errors.append(f"{name} {field} mismatch")
            elif field == "blocker_reasons":
                if sorted(actual or []) != sorted(expected_value):
                    errors.append(f"{name} {field} mismatch")
            elif actual != expected_value:
                errors.append(f"{name} {field} mismatch")

    table_rows = list(csv.DictReader((submission / "normalization_comparison.tsv").open(), delimiter="\t"))
    table_by_plate = {row.get("plate"): row for row in table_rows}
    if len(table_by_plate) != len(table_rows) or set(table_by_plate) != {row["plate"] for row in exp["joined_rows"]}:
        errors.append("comparison must cover every plate exactly once")
    for source in exp["joined_rows"]:
        row = table_by_plate.get(source["plate"], {})
        if row.get("analysis_scope") != source["analysis_scope"] or _as_bool(row.get("qc_pass")) != source["qc_pass"]:
            errors.append(f"{source['plate']} scope or QC join mismatch")
    table_header = list(table_rows[0]) if table_rows else []
    for field in ("plate", "analysis_scope", "qc_pass", "batch", "condition", "replicate", *exp["profiles"]):
        if field not in table_header:
            errors.append("comparison missing column: " + field)

    text = (submission / "sensitivity_summary.md").read_text().lower()
    for concept, terms in {
        "scope exclusions": ("pilot", "archived", "scope"),
        "batch identifiability": ("batch", "identifi"),
        "control evidence": ("control",),
        "phenotype retention": ("phenotype", "effect retention"),
        "direction reversal": ("direction", "reversal"),
        "over-correction": ("over-correction", "overcorrection", "erasing"),
        "limitation": ("limitation", "descriptive"),
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
