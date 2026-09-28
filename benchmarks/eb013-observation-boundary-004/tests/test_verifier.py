import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
spec = importlib.util.spec_from_file_location("calibration", ROOT / "scripts/calibrate_observation_boundary.py")
calibration = importlib.util.module_from_spec(spec)
spec.loader.exec_module(calibration)


def test_independent_oracle_and_contract_mutations():
    exp, controls, variants = calibration.run_controls()
    assert exp["winner"] is not None
    assert len(controls) >= 15
    assert len(variants) >= 8


def test_modules_registered():
    catalog = calibration.read(ROOT / "config/module_catalog.json")
    library = calibration.read(ROOT / "config/reusable_difficulty_modules.json")
    ids = {r["id"] for r in catalog["modules"]}
    modules = {r["id"]: r for r in library["modules"]}
    for key in ("horizon_observation_equivalence", "math_distributional_minimax"):
        assert key in ids and key in modules
        assert modules[key]["required_controls"] and modules[key]["decision_flip"]
