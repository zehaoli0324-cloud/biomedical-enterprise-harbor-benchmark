import importlib.util
import shutil
from pathlib import Path

import pytest

TASK = Path(__file__).resolve().parents[1]
ROOT = TASK.parents[1]
spec = importlib.util.spec_from_file_location("cross_context_calibration", ROOT / "scripts/calibrate_cross_context_portfolio.py")
cal = importlib.util.module_from_spec(spec); spec.loader.exec_module(cal)
v = cal.verifier()


def test_independent_oracle_and_portfolio_count():
    exp = v.expected(TASK / "data")
    independent, _ = cal.independent(TASK / "data")
    assert exp["portfolio_count"] == 32
    assert tuple(exp["winner"]["selected_followups"]) == independent[1] == ("F1", "F4")
    assert exp["winner"]["supported_count"] == 3


@pytest.mark.parametrize("name", ["pooled-shortcut", "related-repeat", "independent-gain", "budget-contraction", "conflict-resolution", "order-invariance", "insufficient"])
def test_metamorphic_variants(tmp_path, name):
    data = tmp_path / "data"; shutil.copytree(TASK / "data", data); cal.mutate(data, name)
    cal.independent(data)
    exp = v.expected(data)
    out = tmp_path / "out"; cal.reference(out, data, v)
    assert v.verify(out, data) == (True, [])
    assert exp["winner"] is None or exp["winner"]["eligible"]


@pytest.mark.parametrize("mutation", ["missing_context", "wrong_hash", "wrong_count", "portfolio_kind", "pooled_claim", "duplicate_row"])
def test_contract_mutations_rejected(tmp_path, mutation):
    cal.reference(tmp_path, TASK / "data", v)
    if mutation == "missing_context":
        p = tmp_path / "context.tsv"; p.write_text(p.read_text().splitlines()[0] + "\n")
    elif mutation == "wrong_count":
        p = tmp_path / "context.tsv"; p.write_text(p.read_text().replace("\t2\t", "\t1\t", 1))
    elif mutation == "duplicate_row":
        p = tmp_path / "portfolio.tsv"; lines = p.read_text().splitlines(); p.write_text("\n".join(lines + [lines[1]]) + "\n")
    elif mutation == "wrong_hash":
        p = tmp_path / "provenance.json"; payload = cal.read(p); payload["input_sha256"]["rules.json"] = "0" * 64; cal.write(p, payload)
    elif mutation == "portfolio_kind":
        p = tmp_path / "portfolio.tsv"; p.write_text(p.read_text().replace("\tadd\t", "\trelated\t", 1))
    else:
        p = tmp_path / "decision.json"; payload = cal.read(p); payload["claim_boundary"] = "pooled biological proof"; cal.write(p, payload)
    assert not v.verify(tmp_path, TASK / "data")[0]


def test_declared_equivalences_pass(tmp_path):
    cal.reference(tmp_path, TASK / "data", v)
    for name in ("plan.json", "decision.json"):
        payload = cal.read(tmp_path / name); payload["selected_followups"].reverse(); payload["total_cost"] = "2.400000"; cal.write(tmp_path / name, payload)
    p = tmp_path / "portfolio.tsv"; lines = p.read_text().splitlines(); p.write_text("\n".join([lines[0]] + list(reversed(lines[1:]))) + "\n")
    assert v.verify(tmp_path, TASK / "data") == (True, [])


def test_materializer_never_overwrites(tmp_path):
    spec = importlib.util.spec_from_file_location("portfolio_materializer", ROOT / "scripts/materialize_cross_context_portfolio.py")
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); m.TASK = tmp_path
    (tmp_path / "data").mkdir(); sentinel = tmp_path / "data/rules.json"; sentinel.write_text("{}")
    with pytest.raises(FileExistsError): m.main()
    assert sentinel.read_text() == "{}"
