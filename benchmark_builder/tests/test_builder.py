from pathlib import Path

from benchmark_builder.compiler import compile_spec
from benchmark_builder.config import load_spec
from benchmark_builder.scoring import score_spec


ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "config/examples/crispr-resistance-e2e-001.toml"


def test_example_spec_loads_and_scores() -> None:
    spec = load_spec(CONFIG)
    report = score_spec(spec)
    assert spec.task_id == "crispr-resistance-e2e-001"
    assert report.band in {"advanced", "research-grade", "frontier"}
    assert report.adjusted_score >= report.raw_score
    assert "long_horizon_x_tool_orchestration" in report.interactions
    assert spec.scenario_card is not None
    assert spec.scenario_card.scenario_id == "C20-resistance-mechanism"


def test_compile_is_deterministic(tmp_path: Path) -> None:
    spec = load_spec(CONFIG)
    report = score_spec(spec)
    output = compile_spec(spec, report, tmp_path / "compiled")
    assert output.is_file()
    assert (output.parent / "difficulty_report.md").is_file()
    first = output.read_text(encoding="utf-8")
    compile_spec(spec, report, tmp_path / "compiled")
    assert output.read_text(encoding="utf-8") == first
