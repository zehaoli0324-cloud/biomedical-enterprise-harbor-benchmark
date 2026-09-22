import importlib.util
import json
import shutil
from pathlib import Path

import pytest

TASK = Path(__file__).resolve().parents[1]
ROOT = TASK.parents[1]
spec = importlib.util.spec_from_file_location("setup_calibration", ROOT / "scripts/calibrate_shared_setup_routing.py")
calibration = importlib.util.module_from_spec(spec)
spec.loader.exec_module(calibration)
verifier = calibration.load_verifier()


def test_independent_oracle_and_nonlocal_winner():
    result = calibration.check_oracle(TASK / "data", verifier)
    assert result["winner"]["stage2_policy"] == {"high": "M01", "low": "M05", "mid": "M08"}
    assert result["winner"]["setup_cost"] == 4
    assert result["winner"]["worst_case_cost"] == 6.8
    assert result["winner"]["worst_case_max_critical_residual"] == .23
    assert len(verifier.enumerate_policies(TASK / "data")) == 108


def test_own_threshold_per_axis_and_hold(tmp_path):
    data = tmp_path / "data"
    shutil.copytree(TASK / "data", data)
    rules = calibration.read(data / "rules.json")
    rules["critical_thresholds"]["signal"] = .01
    calibration.write(data / "rules.json", rules)
    assert calibration.check_oracle(data, verifier)["winner"] is None
    calibration.reference(tmp_path / "out", data, verifier)
    assert verifier.verify(tmp_path / "out", data) == (True, [])


def test_all_prerequisites_and_temporal_gates():
    policies = verifier.enumerate_policies(TASK / "data")
    used = {action for p in policies for action in p["stage2_policy"].values()}
    assert not used & {"M10", "M11", "M12"}
    assert "M13" in used


@pytest.mark.parametrize("mutation", ["missing_field", "missing_state", "extra_state", "wrong_hash", "duplicate_path", "bad_number", "claim", "duplicate_json"])
def test_structured_errors_are_rejected(tmp_path, mutation):
    calibration.reference(tmp_path, TASK / "data", verifier)
    path = tmp_path / "decision.json"
    payload = calibration.read(path)
    if mutation == "missing_field": payload.pop("setup_cost")
    if mutation == "missing_state": payload["stage2_policy"].pop("mid")
    if mutation == "extra_state": payload["stage2_policy"]["extra"] = "M01"
    if mutation == "bad_number": payload["setup_cost"] = "NaN"
    if mutation == "claim": payload["human_review_required"] = False
    calibration.write(path, payload)
    if mutation in {"wrong_hash", "duplicate_path"}:
        path = tmp_path / "provenance.json"; payload = calibration.read(path)
        payload["input_sha256"]["data/rules.json" if mutation == "duplicate_path" else "rules.json"] = "0" * 64
        calibration.write(path, payload)
    if mutation == "duplicate_json":
        path.write_text(path.read_text().replace('"setup_cost": 4.0', '"setup_cost": 4.0, "setup_cost": 4.0'))
    assert not verifier.verify(tmp_path, TASK / "data")[0]


def test_route_content_not_just_row_count(tmp_path):
    calibration.reference(tmp_path, TASK / "data", verifier)
    path = tmp_path / "route.tsv"
    path.write_text(path.read_text().replace("M01", "M10"))
    assert not verifier.verify(tmp_path, TASK / "data")[0]


@pytest.mark.parametrize("accounting", ["observed_setup_only", "shared_setup_double_charge"])
def test_wrong_setup_accounting_is_rejected(tmp_path, accounting):
    import csv
    calibration.reference(tmp_path, TASK / "data", verifier)
    inputs = calibration.read(TASK / "data/requests.json")
    rules = calibration.read(TASK / "data/rules.json")
    actions = {a["request_id"]: a for a in inputs["stage2"]}
    path = tmp_path / "route.tsv"
    with path.open() as handle:
        rows = list(csv.DictReader(handle, delimiter="\t"))
    first = next(a for a in inputs["stage1"] if a["request_id"] == "P01")
    for row in rows:
        action = actions[row["stage2_request_id"]]
        setup = (rules["setup_costs"][action["setup_family"]] if accounting == "observed_setup_only"
                 else sum(rules["setup_costs"][actions[r["stage2_request_id"]]["setup_family"]] for r in rows))
        row["cost"] = first["cost"] + setup + action["cost"]
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)
    passed, errors = verifier.verify(tmp_path, TASK / "data")
    assert not passed
    assert any("cost: wrong number" in error for error in errors)


def test_equivalence_and_explicit_numbers(tmp_path):
    calibration.reference(tmp_path, TASK / "data", verifier)
    for name in ("plan.json", "decision.json"):
        path = tmp_path / name; payload = calibration.read(path)
        payload["setup_families"].reverse()
        payload["setup_cost"] = "4.0000000"
        calibration.write(path, payload)
    path = tmp_path / "provenance.json"; payload = calibration.read(path)
    payload["input_sha256"] = {"data/" + k: v for k, v in payload["input_sha256"].items()}
    calibration.write(path, payload)
    assert verifier.verify(tmp_path, TASK / "data") == (True, [])


def test_later_source_is_excluded(tmp_path):
    data = tmp_path / "data"; shutil.copytree(TASK / "data", data)
    requests = calibration.read(data / "requests.json")
    requests["stage2"][0]["available_at"] = "2026-09-23"
    calibration.write(data / "requests.json", requests)
    result = calibration.check_oracle(data, verifier)
    assert result["winner"]["stage2_policy"]["high"] != "M01"


def test_materializer_does_not_overwrite_verifier_or_trials(tmp_path):
    spec = importlib.util.spec_from_file_location("setup_materializer", ROOT / "scripts/materialize_shared_setup_routing.py")
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    module.TASK = tmp_path
    (tmp_path / "data").mkdir()
    sentinel = tmp_path / "data/rules.json"
    sentinel.write_text('{"prior_trial": true}')
    with pytest.raises(FileExistsError):
        module.main()
    assert sentinel.read_text() == '{"prior_trial": true}'


def test_calibration_cannot_replace_recorded_trial_freeze(tmp_path, monkeypatch):
    monkeypatch.setattr(calibration, "TASK", tmp_path)
    (tmp_path / "quality").mkdir()
    (tmp_path / "quality/target_trial_evidence.json").write_text("{}")
    with pytest.raises(FileExistsError, match="Target trial recorded"):
        calibration.main()
