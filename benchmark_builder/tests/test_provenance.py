from pathlib import Path

from benchmark_builder.provenance import validate_registry


def test_public_data_literature_registry_is_valid() -> None:
    root = Path(__file__).resolve().parents[2]
    result = validate_registry(root / "data/public_data_literature_registry.json")
    assert result["status"] == "PASS"
    assert result["source_count"] >= 9
    assert result["claim_count"] >= 6
    assert result["formula_count"] >= 7
