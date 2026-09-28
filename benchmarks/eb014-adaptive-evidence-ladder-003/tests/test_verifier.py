from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).parents[1]
SPEC = importlib.util.spec_from_file_location("adaptive_ladder_verifier", ROOT / "verifier.py")
verifier = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(verifier)


def oracle_output(tmp_path):
    out = tmp_path / "outputs"
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "solution/solve.py"),
            "--data",
            str(ROOT / "data"),
            "--out",
            str(out),
        ],
        check=True,
    )
    return out


def test_oracle_passes(tmp_path):
    out = oracle_output(tmp_path)
    passed, errors = verifier.verify(out, ROOT / "data", ROOT / "verifier_only/reference.json")
    assert passed, errors


def test_tampered_state_token_fails(tmp_path):
    out = oracle_output(tmp_path)
    payload = json.loads((out / "research_log.json").read_text())
    payload["events"][4]["state_token"] = "0" * 64
    (out / "research_log.json").write_text(json.dumps(payload))
    passed, errors = verifier.verify(out, ROOT / "data", ROOT / "verifier_only/reference.json")
    assert not passed
    assert "contract: state-token mismatch for independent_replicate" in errors


def test_early_stop_and_skipped_conditional_branch_fail(tmp_path):
    out = oracle_output(tmp_path)
    payload = json.loads((out / "research_log.json").read_text())
    payload["events"] = payload["events"][:6] + [payload["events"][-1]]
    payload["events"][-1]["round"] = 7
    (out / "research_log.json").write_text(json.dumps(payload))
    passed, errors = verifier.verify(out, ROOT / "data", ROOT / "verifier_only/reference.json")
    assert not passed
    assert "scientific: early stop with incomplete checks" in errors
    assert any("missing activated checks" in error for error in errors)


def test_malformed_round_is_a_stable_verifier_failure(tmp_path):
    out = oracle_output(tmp_path)
    payload = json.loads((out / "research_log.json").read_text())
    payload["events"][0]["round"] = "one"
    (out / "research_log.json").write_text(json.dumps(payload))
    passed, errors = verifier.verify(out, ROOT / "data", ROOT / "verifier_only/reference.json")
    assert not passed
    assert "contract: rounds must be contiguous" in errors


def test_tampered_minimax_root_policy_fails(tmp_path):
    out = oracle_output(tmp_path)
    payload = json.loads((out / "contingent_policy.json").read_text())
    payload["rows"][0]["chosen_action"] = "COMMIT_SAFE"
    (out / "contingent_policy.json").write_text(json.dumps(payload))
    passed, errors = verifier.verify(out, ROOT / "data", ROOT / "verifier_only/reference.json")
    assert not passed
    assert any("I00 chosen_action mismatch" in error for error in errors)


def test_pending_policy_cannot_skip_wait(tmp_path):
    out = oracle_output(tmp_path)
    payload = json.loads((out / "contingent_policy.json").read_text())
    for row in payload["rows"]:
        if row["information_set_id"] == "I10":
            row["chosen_action"] = "COMMIT_A_HIGH"
    (out / "contingent_policy.json").write_text(json.dumps(payload))
    passed, errors = verifier.verify(out, ROOT / "data", ROOT / "verifier_only/reference.json")
    assert not passed
    assert any("I10 chosen_action mismatch" in error for error in errors)


def test_equivalent_policy_serialization_is_accepted(tmp_path):
    out = oracle_output(tmp_path)
    policy = json.loads((out / "contingent_policy.json").read_text())
    rows = policy.pop("rows")
    for row in rows:
        row["decision_status"] = "PENDING_WAIT" if row["decision_status"] == "DELAYED_REVEAL_WAIT" else "MINIMAX_OPTIMAL"
    policy["policy"] = list(reversed(rows))
    (out / "contingent_policy.json").write_text(json.dumps(policy))
    certificate = {
        "schema_version": "adaptive_ladder_l12_policy_certificate.v1",
        "difficulty_level": "L12_STATIC_CONTINGENT_POLICY_REPLAY",
        "runtime_scope": "STATIC_CONTINGENT_POLICY_REPLAY_ONLY",
        "protocol": "data/partial_observation_protocol.json",
        "protocol_sha256": json.loads((out / "policy_certificate.json").read_text())["protocol_sha256"],
        "root_information_set_id": "I00",
        "recomputed_root_action": "REQUEST_CONTEXT_A",
        "recomputed_root_value": -6,
        "root_adversarial_branch_count": 1,
        "information_set_count": 17,
        "pending_information_set_count": 4,
        "policy_row_count": 17,
        "certificate_status": "VALID_STATIC_MINIMAX_REPLAY",
    }
    (out / "policy_certificate.json").write_text(json.dumps(certificate))
    passed, errors = verifier.verify(out, ROOT / "data", ROOT / "verifier_only/reference.json")
    assert passed, errors


def test_data_heavy_finalization_aliases_are_accepted(tmp_path):
    out = oracle_output(tmp_path)
    completion = json.loads((out / "completion.json").read_text())
    completion["stop_reason"] = "evidence_complete"
    (out / "completion.json").write_text(json.dumps(completion))

    provenance = json.loads((out / "provenance.json").read_text())
    provenance["input_sha256"] = {"data/" + key: value for key, value in provenance["input_sha256"].items()}
    (out / "provenance.json").write_text(json.dumps(provenance))

    certificate = json.loads((out / "policy_certificate.json").read_text())
    certificate = {
        "overall_decision": "MINIMAX_POLICY_COMPLETE",
        "claim_scope": "static_contingent_policy_replay_only",
        "protocol_hash": certificate["protocol_sha256"],
        "root_information_set_id": "I00",
        "root_action": "REQUEST_CONTEXT_A",
        "root_worst_case_value": -6,
        "root_action_values": {"COMMIT_SAFE": -7, "REQUEST_CONTEXT_A": -6, "REQUEST_CONTEXT_B": -7},
        "root_adversarial_branch_count": 1,
        "information_set_count": 17,
        "pending_information_sets": ["I10", "I12", "I20", "I22"],
    }
    (out / "policy_certificate.json").write_text(json.dumps(certificate))

    passed, errors = verifier.verify(out, ROOT / "data", ROOT / "verifier_only/reference.json")
    assert passed, errors
