from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]


def read(name: str) -> str:
    return (ROOT / name).read_text(encoding="utf-8")


def test_package_shape_and_task_book():
    for path in [
        "task.yaml",
        "instruction.md",
        "expected_artifacts.md",
        "scenario-card.yaml",
        "verifier.py",
        "data/project_brief.md",
        "data/constraints.yaml",
        "data/literature_records.tsv",
        "data/sample_metadata.tsv",
        "data/candidate_measurements.tsv",
        "data/tool_registry.json",
        "verifier_only/reference_labels.json",
    ]:
        assert (ROOT / path).is_file(), path


def test_all_difficulty_behaviors_are_declared():
    task = read("task.yaml")
    instruction = read("instruction.md")
    for token in [
        "swapped batch label",
        "normalized DOI",
        "correlation-only",
        "failed export",
        "alternate weight",
        "reproducibility_manifest.json",
        "wet-lab",
    ]:
        assert token.lower() in (task + instruction).lower(), token


def test_task_weights_and_reference_labels_are_complete():
    task = read("task.yaml")
    assert "hidden_reference: verifier_only/reference_labels.json" in task
    assert set(re.findall(r"CAND-[A-D]", read("verifier_only/reference_labels.json"))) == {"CAND-A", "CAND-B", "CAND-C", "CAND-D"}
