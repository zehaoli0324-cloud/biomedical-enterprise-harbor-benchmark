import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
spec = importlib.util.spec_from_file_location("calibration", ROOT / "scripts/calibrate_evidence_gap_followup.py")
calibration = importlib.util.module_from_spec(spec)
spec.loader.exec_module(calibration)


def test_pretrial_controls_and_reference():
    expected, results = calibration.calibrate()
    assert expected["claim_ledger.json"]["claim_ceiling"] == "descriptive"
    policy = expected["research_plan.json"]["policy"]
    assert policy["action"] == "A-REPLICATE"
    assert policy["branches"]["inconsistent"]["action"] == "hold"
    assert len(results["controls"]) >= 24
    assert len(results["variants"]) == 8
    assert all(row["passed"] == row["expected"] for row in results["controls"])


def test_refuted_is_not_opposite_claim_permission():
    expected = calibration.verifier().expected(calibration.TASK / "data")
    leaves = expected["adaptive_update.json"]["leaves"]
    negative = next(r for r in leaves if r["path"] == ["A-REPLICATE:inconsistent"])
    assert negative["claims"]["C-CAUSAL"] == "refuted"
    assert negative["claim_ceiling"] == "descriptive"
    assert negative["resolved_weight"] == 5
    positive = next(r for r in leaves if r["path"][-1] == "A-BRIDGE:bridge_supported")
    assert positive["claims"]["C-CAUSAL"] == "unknown"
    assert positive["claim_ceiling"] == "transportable_association"


def test_no_initial_support_means_no_claim_ceiling(tmp_path):
    import shutil
    shutil.copytree(calibration.TASK / "data", tmp_path / "data")
    path = tmp_path / "data/sources.json"
    sources = calibration.read(path)
    next(row for row in sources if row["id"] == "E-DIRECT")["status"] = "archived"
    calibration.write(path, sources)
    expected = calibration.verifier().expected(tmp_path / "data")
    assert expected["claim_ledger.json"]["claim_ceiling"] is None


def test_missing_artifacts_fail_without_exception(tmp_path):
    passed, errors = calibration.verifier().verify(tmp_path, calibration.TASK / "data")
    assert not passed and len(errors) == 5


def test_contract_builds():
    from benchmark_builder.config import load_spec
    spec = load_spec(ROOT / "candidate_pools/enterprise-v1/contracts/eb014-evidence-gap-followup-001.toml")
    assert spec.task_id == "eb014-evidence-gap-followup-001"


def test_registered_modules_exist():
    catalog = calibration.read(ROOT / "config/module_catalog.json")
    library = calibration.read(ROOT / "config/reusable_difficulty_modules.json")
    catalog_ids = {row["id"] for row in catalog["modules"]}
    library_ids = {row["id"] for row in library["modules"]}
    for module_id in ("judgment_claim_transportability_boundary", "research_minimum_additional_evidence", "horizon_adaptive_research_priority", "retrieval_independence_quorum"):
        assert module_id in catalog_ids and module_id in library_ids
