import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/check_enterprise_harbor_sop.py"
spec = importlib.util.spec_from_file_location("enterprise_harbor_sop", SCRIPT)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")


def make_package(root, target_status="NOT_RUN"):
    (root / "data").mkdir(parents=True)
    (root / "tests").mkdir()
    (root / "verifier_only").mkdir()
    (root / "quality").mkdir()
    (root / "data/input.json").write_text("{}", encoding="utf-8")
    (root / "tests/test_verifier.py").write_text("def test_placeholder(): pass\n", encoding="utf-8")
    (root / "verifier.py").write_text("def verify(): return True\n", encoding="utf-8")
    write_json(root / "verifier_only/reference.json", {})
    (root / "task.yaml").write_text(
        f"id: {root.name}\nrequired_outputs:\n  - {{id: result, path: outputs/result.json}}\n",
        encoding="utf-8",
    )
    (root / "instruction.md").write_text("Write `outputs/result.json`.\n", encoding="utf-8")
    write_json(root / "quality/control_plan_card.json", {"calibration_status": "CALIBRATED", "controls": [{"kind": kind} for kind in module.REQUIRED_CONTROL_KINDS]})
    records = [{"strategy": strategy, "status": "pass"} for strategy in ("reference_solution", "simple_legal_baseline", "always_abstain", "template_or_keyword")]
    write_json(root / "quality/model_trial_card.json", {"strategies": sorted(module.REQUIRED_STRATEGIES), "target_model_status": target_status, "status": "BLOCKED" if target_status != "NOT_RUN" else "NOT_RUN", "run_records": records})
    write_json(root / "quality/sop_card.json", {"schema_version": "enterprise_harbor_sop_card.v1", "task_id": root.name, "source_status": "REVIEW_REQUIRED", "contract_status": "CONTRACT_ONLY", "control_status": "CALIBRATED", "model_trial_status": "NOT_RUN", "independent_verifier_status": "PASS", "release_status": "BLOCKED"})
    write_json(root / "quality/independent_verifier_audit.json", {"status": "PASS", "review_status": "pass"})


def test_pretrial_pass_does_not_require_target_model(tmp_path):
    package = tmp_path / "enterprise-task-001"
    make_package(package)
    result = module.evaluate(package)
    assert result["status"] == "PASS"
    assert result["blockers"] == []
    assert result["release_blockers"] == ["target_model_not_run"]


def test_multiline_required_outputs_are_detected(tmp_path):
    package = tmp_path / "enterprise-task-001"
    make_package(package)
    (package / "task.yaml").write_text(
        f"id: {package.name}\nrequired_outputs:\n  - id: result\n    path: outputs/result.json\n    required_fields: [status]\nhidden_truth:\n  status: verifier_only\n",
        encoding="utf-8",
    )
    result = module.evaluate(package)
    assert result["status"] == "PASS"
    assert result["blockers"] == []


def test_infrastructure_failure_is_not_difficulty_evidence(tmp_path):
    package = tmp_path / "enterprise-task-001"
    make_package(package, target_status="TIMEOUT_INFRASTRUCTURE")
    result = module.evaluate(package)
    assert result["status"] == "PASS"
    assert result["release_blockers"] == ["target_model_infrastructure"]
    assert result["target_model_infra_not_difficulty"] is True


def test_missing_package_is_fail_closed(tmp_path):
    result = module.evaluate(tmp_path)
    assert result["status"] == "BLOCKED"
    assert "file:task.yaml" in result["blockers"]
    assert result["release_permitted"] is False
