import importlib.util
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "scripts/score_l51_abstention_variants.py"
spec = importlib.util.spec_from_file_location("score_l51", SCRIPT)
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(module)


def test_variants_have_auditable_scores():
    task = ROOT / "benchmarks/eb010-closed-loop-ambiguity-004"
    units = module.load_units(task)
    reference = module.score(units, "positive_plus_insufficient_abstain")
    all_abstain = module.score(units, "all_abstain")
    wrong_positive = module.score(units, "positive_as_wrong_abstain")

    assert len(units) == 21
    assert reference["score"] == 1.0
    assert reference["abstention_fraction"] == pytest.approx(4 / 21, abs=1e-6)
    assert all_abstain["score"] == pytest.approx(4 / 21, abs=1e-6)
    assert wrong_positive["score"] == pytest.approx(20 / 21, abs=1e-6)
    assert wrong_positive["score"] < reference["score"]
    assert all_abstain["abstention_score_weight"] > 0.70
