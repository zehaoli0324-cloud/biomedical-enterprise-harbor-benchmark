import importlib.util
import json


ROOT = __import__("pathlib").Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/run_task_pipeline.py"
spec = importlib.util.spec_from_file_location("task_pipeline_batch", SCRIPT)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_compact_report_preserves_independent_status_axes():
    report = {
        "task_id": "x",
        "pipeline_status": "DEVELOPMENT_BUILT",
        "evidence_status": "STATIC_REVIEW_PASS",
        "review_status": "NOT_RUN",
        "release_status": "BLOCKED",
        "release_permitted": False,
        "blockers": [],
        "release_blockers": ["scientific_review"],
        "build_manifest": {"task_version": "1.0.0", "data_fingerprint": "d", "contract_fingerprint": "c", "files": {"x": "y"}},
    }
    row = module.compact(report, formal=True)
    assert row["scope"] == "formal"
    assert row["pipeline_status"] != row["release_status"]
    assert row["release_permitted"] is False


def test_formal_task_ids_are_scope_registry_scoped():
    ids = module.scope_registry()["formal"]
    assert "eb013-cross-context-evidence-portfolio-005" in ids
    assert isinstance(ids, set)
    assert "eb014-adaptive-evidence-ladder-003" not in ids


def test_candidate_scope_is_not_promotion_scope():
    scopes = module.scope_registry()
    assert "eb014-adaptive-evidence-ladder-003" in scopes["candidate"]
    assert scopes["formal"].isdisjoint(scopes["candidate"])
