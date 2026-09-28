import importlib.util
import json


ROOT = __import__("pathlib").Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/check_task_pipeline.py"
spec = importlib.util.spec_from_file_location("task_pipeline", SCRIPT)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")


def make_package(root):
    for directory in ("data", "tests", "verifier_only", "quality", "environment/data"):
        (root / directory).mkdir(parents=True, exist_ok=True)
    (root / "task.yaml").write_text("id: pipeline-task-001\nversion: '1.0.0'\n", encoding="utf-8")
    (root / "instruction.md").write_text("Write outputs/result.json.\n", encoding="utf-8")
    (root / "environment/instruction.md").write_text("Write outputs/result.json.\n", encoding="utf-8")
    (root / "data/input.json").write_text("{}\n", encoding="utf-8")
    (root / "environment/data/input.json").write_text("{}\n", encoding="utf-8")
    (root / "verifier.py").write_text("def verify(): return True\n", encoding="utf-8")
    (root / "tests/verifier.py").write_text("def verify(): return True\n", encoding="utf-8")
    write_json(root / "verifier_only/reference.json", {})
    write_json(root / "data/output_contract.json", {"outputs": []})
    write_json(root / "environment/data/output_contract.json", {"outputs": []})
    write_json(root / "quality/sop_card.json", {"source_status": "SYNTHETIC_DISCLOSED", "replay": {"oracle": "PASS", "nop": "PASS_NEGATIVE"}})


def test_static_build_is_separate_from_release(tmp_path):
    package = tmp_path / "pipeline-task-001"
    make_package(package)
    result = module.evaluate(package)
    assert result["pipeline_status"] == "DEVELOPMENT_BUILT"
    assert result["evidence_status"] == "STATIC_REVIEW_PASS"
    assert result["release_status"] == "BLOCKED"
    assert result["release_permitted"] is False
    assert "scientific_review" in result["release_blockers"]
    assert result["build_manifest"]["data_fingerprint"]


def test_identity_and_copy_drift_fail_closed(tmp_path):
    package = tmp_path / "pipeline-task-001"
    make_package(package)
    (package / "task.yaml").write_text("id: another-task\nversion: '1.0.0'\n", encoding="utf-8")
    (package / "environment/instruction.md").write_text("drift\n", encoding="utf-8")
    result = module.evaluate(package)
    assert result["pipeline_status"] == "CONTRACT_ONLY"
    assert "task_identity" in result["blockers"]
    assert "instruction_copy_sync" in result["blockers"]


def test_missing_source_and_dynamic_records_remain_blocked(tmp_path):
    package = tmp_path / "pipeline-task-001"
    make_package(package)
    result = module.evaluate(package)
    assert result["release_status"] == "BLOCKED"
    assert "missing:data/source_manifest.json" in result["release_blockers"]
    assert "dynamic_oracle_nop" not in result["release_blockers"]
