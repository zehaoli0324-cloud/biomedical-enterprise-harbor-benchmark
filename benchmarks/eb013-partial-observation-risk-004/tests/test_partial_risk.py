import importlib.util
import json
import shutil
from pathlib import Path

import pytest

TASK = Path(__file__).resolve().parents[1]
ROOT = TASK.parents[1]
spec = importlib.util.spec_from_file_location("partial_risk_calibration", ROOT / "scripts/calibrate_partial_observation_risk.py")
cal = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cal)
v = cal.load_verifier()


def test_independent_exact_oracles_agree():
    exp = cal.crosscheck(TASK / "data", v)
    assert len(v.enumerate_policies(TASK / "data")) == 346
    assert exp["winner"]["observation_policy"] == {"a": "B", "b": "A", "c": "B", "d": "C"}
    assert exp["winner"]["robust_cvar"] == .215


@pytest.mark.parametrize("name", ["reveal-world", "nominal-only", "tail-confidence", "commitment-budget", "remove-withdrawal", "no-feasible-policy", "order-invariance"])
def test_variants_have_independent_oracles_and_valid_artifacts(tmp_path, name):
    data = tmp_path / "data"
    shutil.copytree(TASK / "data", data)
    cal.variant(data, name)
    cal.crosscheck(data, v)
    cal.reference(tmp_path / "outputs", data, v)
    assert v.verify(tmp_path / "outputs", data) == (True, [])


def test_fractional_boundary_and_equal_loss_tail():
    losses = {"a": v.num(.6), "b": v.num(.2), "c": v.num(.2)}
    # Worst 40% mass = all 10% at .6, plus 30% at .2.
    assert v.tail_risk(losses, {"a": .1, "b": .7, "c": .2}, .6) == v.num(.3)
    assert v.tail_risk(losses, {"a": .1, "b": .7, "c": .2}, 0) == v.num(.24)


def test_asof_snapshot_is_not_latest_active_fallback():
    _, _, evidence, audit = v.resolve(TASK / "data")
    rows = {r["action_id"]: r for r in audit}
    assert "E" not in evidence and rows["E"]["revision"] == 2
    assert "F" not in evidence and rows["F"]["status"] == "unavailable"
    assert rows["B"]["revision"] == 2
    assert evidence["B"]["W3"]["signal"] == .62


@pytest.mark.parametrize("error", ["duplicate_json", "duplicate_hash", "hidden_state_action", "wrong_tail", "same_rows_wrong_action", "missing_hash", "claim", "missing_file"])
def test_mutations_fail_without_repair(tmp_path, error):
    cal.reference(tmp_path, TASK / "data", v)
    path = tmp_path / "decision.json"
    payload = cal.read(path)
    if error == "hidden_state_action": payload["observation_policy"]["W3"] = "C"
    if error == "wrong_tail": payload["robust_cvar"] = .0001
    if error == "claim": payload["claim_boundary"] = "experimentally_proven"
    cal.write(path, payload)
    if error == "duplicate_json": path.write_text(path.read_text().replace('"probe_id": "P2"', '"probe_id": "P2", "probe_id": "P2"'))
    if error == "same_rows_wrong_action":
        route = tmp_path / "route.tsv"
        route.write_text(route.read_text().replace("W3\tb\tA", "W3\tb\tC"))
    if error in {"duplicate_hash", "missing_hash"}:
        path = tmp_path / "provenance.json"; payload = cal.read(path)
        if error == "duplicate_hash": payload["input_sha256"]["data/rules.json"] = payload["input_sha256"]["rules.json"]
        else: payload["input_sha256"].pop("evidence.json")
        cal.write(path, payload)
    if error == "missing_file": (tmp_path / "audit.md").unlink()
    assert not v.verify(tmp_path, TASK / "data")[0]


def test_equivalent_representations_pass(tmp_path):
    cal.reference(tmp_path, TASK / "data", v)
    for name in ("plan.json", "decision.json"):
        payload = cal.read(tmp_path / name)
        payload["setup_families"].reverse()
        payload["robust_cvar"] = "0.215000"
        cal.write(tmp_path / name, payload)
    path = tmp_path / "route.tsv"; lines = path.read_text().splitlines()
    path.write_text("\n".join([lines[0]] + list(reversed(lines[1:]))) + "\n")
    assert v.verify(tmp_path, TASK / "data") == (True, [])


def test_freeze_still_matches():
    import hashlib
    for name, digest in cal.read(TASK / "quality/pretrial_freeze.json")["files"].items():
        assert hashlib.sha256((TASK / name).read_bytes()).hexdigest() == digest


def test_calibration_cannot_overwrite_freeze(tmp_path, monkeypatch):
    monkeypatch.setattr(cal, "TASK", tmp_path)
    (tmp_path / "quality").mkdir()
    (tmp_path / "quality/pretrial_freeze.json").write_text("{}")
    with pytest.raises(FileExistsError):
        cal.main()


def test_observation_renaming_preserves_semantics(tmp_path):
    data = tmp_path / "data"
    shutil.copytree(TASK / "data", data)
    catalog = cal.read(data / "catalog.json")
    for probe in catalog["probes"]:
        probe["observations"] = {s: "observed_" + label for s, label in probe["observations"].items()}
    cal.write(data / "catalog.json", catalog)
    original = v.expected(TASK / "data")["winner"]
    renamed = cal.crosscheck(data, v)["winner"]
    assert original["probe_id"] == renamed["probe_id"]
    assert original["robust_cvar"] == renamed["robust_cvar"]
    assert {"observed_" + k: value for k, value in original["observation_policy"].items()} == renamed["observation_policy"]


def test_capabilities_gate_before_search():
    policies = v.enumerate_policies(TASK / "data")
    assert all("D" not in p["observation_policy"].values() for p in policies if p["probe_id"] != "P2")
    assert any("D" in p["observation_policy"].values() for p in policies if p["probe_id"] == "P2")


def test_builder_reproduces_visible_data_and_preserves_existing_version(tmp_path):
    spec = importlib.util.spec_from_file_location("partial_risk_builder", ROOT / "scripts/materialize_partial_observation_risk.py")
    builder = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(builder)
    builder.TASK = tmp_path
    builder.main()
    for path in (TASK / "data").glob("*.json"):
        assert cal.read(path) == cal.read(tmp_path / "data" / path.name)
    with pytest.raises(FileExistsError):
        builder.main()
