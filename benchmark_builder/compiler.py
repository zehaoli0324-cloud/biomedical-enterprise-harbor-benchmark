from __future__ import annotations

import hashlib
import json
from pathlib import Path

from .models import BenchmarkSpec, DifficultyReport


def spec_digest(spec: BenchmarkSpec) -> str:
    payload = {
        "task_id": spec.task_id,
        "title": spec.title,
        "domain": spec.domain,
        "source_scenarios": spec.source_scenarios,
        "dimensions": {key: value.to_dict() for key, value in spec.dimensions.items()},
        "modules": {
            key: [item.to_dict() for item in values] for key, values in spec.modules.items()
        },
        "data_types": spec.data_types,
        "constraints": spec.constraints,
        "evaluation": spec.evaluation.to_dict(),
        "scenario_card": spec.scenario_card.to_dict() if spec.scenario_card else None,
    }
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def compile_spec(spec: BenchmarkSpec, report: DifficultyReport, output: str | Path) -> Path:
    output_path = Path(output)
    output_path.mkdir(parents=True, exist_ok=True)
    manifest = {
        "schema_version": "benchmark_builder.v1",
        "task": {
            "id": spec.task_id,
            "title": spec.title,
            "domain": spec.domain,
            "source_scenarios": list(spec.source_scenarios),
            "data_types": list(spec.data_types),
        },
        "difficulty": report.to_dict(),
        "constraints": spec.constraints,
        "spec_digest": spec_digest(spec),
        "evaluation": spec.evaluation.to_dict(),
        "scenario_card": spec.scenario_card.to_dict() if spec.scenario_card else None,
        "status": "compiled_contract",
    }
    manifest_path = output_path / "task_manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        f"# Difficulty report: {spec.task_id}",
        "",
        f"- Title: {spec.title}",
        f"- Domain: {spec.domain}",
        f"- Raw score: {report.raw_score}/5",
        f"- Adjusted score: {report.adjusted_score}/5",
        f"- Band: {report.band}",
        f"- Spec digest: `{manifest['spec_digest']}`",
        "",
        "## Dimensions",
        "",
        "| Dimension | Level | Weight | Rationale |",
        "| --- | ---: | ---: | --- |",
    ]
    for name, dimension in report.dimensions.items():
        rationale = dimension.rationale.replace("|", "\\|").replace("\n", " ")
        lines.append(f"| `{name}` | {dimension.level} | {dimension.weight:g} | {rationale} |")
    lines.extend(["", "## Interactions", ""])
    if report.interactions:
        lines.extend(f"- `{item}`" for item in report.interactions)
    else:
        lines.append("- None")
    lines.extend(["", "## Selected modules", ""])
    for category, selections in report.selected_modules.items():
        lines.append(f"### {category}")
        lines.extend(f"- `{item.module_id}`: `{item.params}`" for item in selections)
    (output_path / "difficulty_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (output_path / "evaluation_protocol.json").write_text(
        json.dumps(
            {
                "schema_version": "benchmark_builder.evaluation.v1",
                "task_id": spec.task_id,
                "spec_digest": manifest["spec_digest"],
                "evaluation": spec.evaluation.to_dict(),
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return manifest_path
