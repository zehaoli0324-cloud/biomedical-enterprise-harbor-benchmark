import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_real_data_registry_matches_release_plan_contract():
    registry = json.loads((ROOT / "config/real_data_replacement_registry.json").read_text())
    plan = (ROOT.parent / "Downloads/ten-task-real-data-replacement-plan.md")
    assert plan.is_file()
    assert registry["standard"].startswith("No hand-authored scientific number")
    assert len(registry["tasks"]) == 10
    assert len({task["task_id"] for task in registry["tasks"]}) == 10
    required = set(registry["required_freeze_fields"])
    assert {"accession_or_doi", "sha256", "license_or_rights"} <= required
    links = registry["source_links"]
    assert "https://pmc.ncbi.nlm.nih.gov/articles/PMC7006212/" == links["crispr_paper"]
    assert "https://bbbc.broadinstitute.org/BBBC021" == links["bbbc021"]
    assert "https://zenodo.org/records/10362368" == links["zenodo_md"]


def test_real_source_tasks_are_fail_closed_until_rebound():
    registry = json.loads((ROOT / "config/real_data_replacement_registry.json").read_text())
    statuses = {task["status"] for task in registry["tasks"]}
    assert statuses <= {"STAGING_REBIND_REQUIRED", "RECIPE_ONLY", "RELEASED"}
    assert all(task["blockers"] for task in registry["tasks"])
    assert "Legacy calibration data" in registry["release_interpretation"]
