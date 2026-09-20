from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]


def read(name: str) -> str:
    return (ROOT / name).read_text(encoding="utf-8")


def test_package_shape():
    for path in [
        "task.yaml",
        "instruction.md",
        "expected_artifacts.md",
        "environment/README.md",
    ]:
        assert (ROOT / path).is_file(), path


def test_task_declares_required_chain_and_outputs():
    task = read("task.yaml")
    for token in [
        "id: crispr-resistance-e2e-001",
        "nf-core/crisprseq",
        "nf-core/rnaseq",
        "FlashFry",
        "CRISPResso2",
        "nature-statistics",
        "path: outputs/claim_ledger.tsv",
        "path: outputs/workflow_bundle/",
        "status: contract_only",
    ]:
        assert token in task, token


def test_score_weights_sum_to_one_hundred():
    task = read("task.yaml")
    block = task.split("  weighted_scores:\n", 1)[1].split("  metrics:\n", 1)[0]
    values = [int(value) for value in re.findall(r"^    (?!total:)[a-z_]+: (\d+)$", block, re.MULTILINE)]
    assert values
    assert sum(values) == 100


def test_instruction_matches_artifact_contract():
    instruction = read("instruction.md")
    expected = read("expected_artifacts.md")
    for artifact in [
        "study_plan.yaml",
        "evidence_table.tsv",
        "screen_results.tsv",
        "rna_mechanism.tsv",
        "target_ranking.tsv",
        "guide_candidates.tsv",
        "editing_validation.tsv",
        "claim_ledger.tsv",
        "workflow_bundle/",
        "final_report.md",
    ]:
        assert artifact in instruction
        assert artifact in expected


def test_failure_injections_are_linked_to_taxonomy():
    task = read("task.yaml")
    taxonomy = read("../../docs/failure-taxonomy.md")
    ids = set(re.findall(r"^##\s+(F\d+)\.", taxonomy, re.MULTILINE))
    referenced = set(re.findall(r"taxonomy: \[([^\]]+)\]", task))
    flattened = {item.strip() for group in referenced for item in group.split(",")}
    assert flattened
    assert flattened.issubset(ids)
