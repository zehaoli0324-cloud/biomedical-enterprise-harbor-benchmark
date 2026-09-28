from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def _unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key: " + key)
        result[key] = value
    return result


def _invalid(value):
    raise ValueError("non-finite JSON number: " + value)


def load(path):
    return json.loads(
        path.read_text(encoding="utf-8"),
        object_pairs_hook=_unique,
        parse_constant=_invalid,
    )


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def state_token(seed, prior_token, round_no, action_id, outcome):
    payload = "|".join(
        str(value) for value in (seed, prior_token, round_no, action_id, outcome)
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def activated_checks(rules, states):
    required = set(rules["required_checks"])
    for outcome in states:
        required.update(rules.get("conditional_checks", {}).get(outcome, []))
    return required


def verify_policy(submission, data, protocol, truth):
    errors = []
    try:
        policy = load(submission / "contingent_policy.json")
        certificate = load(submission / "policy_certificate.json")
    except (OSError, UnicodeError, ValueError) as exc:
        return ["policy delivery: " + str(exc)]
    if not isinstance(policy, dict):
        return ["policy contract: contingent_policy.json must contain an object"]
    policy_rows = policy.get("rows", policy.get("policy"))
    if not isinstance(policy_rows, list):
        return ["policy contract: contingent_policy.json rows/policy must be an array"]
    states = {row["information_set_id"]: row for row in protocol["information_sets"]}
    terminals = protocol["terminal_utilities"]
    memo = {}

    def value(state_id):
        if state_id in terminals:
            return terminals[state_id]
        if state_id in memo:
            return memo[state_id]
        row = states[state_id]
        candidates = []
        for action in row["actions"]:
            branch_values = [action["utility_delta"] + value(branch["next_state"]) for branch in action["branches"]]
            candidates.append((min(branch_values), action["action"], len(branch_values)))
        memo[state_id] = sorted(candidates, key=lambda item: (-item[0], item[1]))[0]
        return memo[state_id][0]

    value(protocol["root_information_set_id"])
    expected_ids = sorted(states)
    actual_ids = [row.get("information_set_id") for row in policy_rows]
    if len(actual_ids) != len(set(actual_ids)) or set(actual_ids) != set(expected_ids):
        errors.append("policy contract: information-set IDs must exactly cover protocol IDs without duplicates")
    for row in policy_rows:
        state_id = row.get("information_set_id")
        if state_id not in states:
            continue
        expected = memo[state_id]
        expected_status = "DELAYED_REVEAL_WAIT" if "PENDING" in states[state_id]["observation"] else "ROBUST_ACTION"
        accepted_statuses = {
            "DELAYED_REVEAL_WAIT": {"DELAYED_REVEAL_WAIT", "PENDING_WAIT"},
            "ROBUST_ACTION": {"ROBUST_ACTION", "MINIMAX_OPTIMAL"},
        }
        checks = {
            "chosen_action": expected[1],
            "worst_case_value": expected[0],
            "adversarial_branch_count": expected[2],
            "decision_status": expected_status,
            "stage": states[state_id]["stage"],
            "observation": states[state_id]["observation"],
        }
        for key, expected_value in checks.items():
            if key == "decision_status" and row.get(key) in accepted_statuses[expected_value]:
                continue
            if row.get(key) != expected_value:
                errors.append(f"policy contract: {state_id} {key} mismatch")

    selected_branch_count = sum(memo[state_id][2] for state_id in states)
    root = memo[protocol["root_information_set_id"]]
    expected_certificate = {
        "schema_version": "adaptive_ladder_l12_policy_certificate.v1",
        "protocol_sha256": digest(data / "partial_observation_protocol.json"),
        "root_information_set_id": protocol["root_information_set_id"],
        "root_action": root[1],
        "root_worst_case_value": root[0],
        "evaluated_information_set_count": len(states),
        "delayed_reveal_state_count": sum("PENDING" in row["observation"] for row in states.values()),
        "adversarial_branch_count": selected_branch_count,
        "claim_scope": "static_contingent_policy_replay_only",
        "overall_decision": "MINIMAX_POLICY_COMPLETE",
    }
    if certificate != expected_certificate:
        normalized_scope = certificate.get("claim_scope", certificate.get("runtime_scope"))
        if normalized_scope == "STATIC_CONTINGENT_POLICY_REPLAY_ONLY":
            normalized_scope = "static_contingent_policy_replay_only"
        normalized_decision = certificate.get("overall_decision", certificate.get("certificate_status"))
        if normalized_decision == "VALID_STATIC_MINIMAX_REPLAY":
            normalized_decision = "MINIMAX_POLICY_COMPLETE"
        alt_root_action = certificate.get("root_action", certificate.get("recomputed_root_action"))
        alt_root_value = certificate.get("root_worst_case_value", certificate.get("recomputed_root_value"))
        alternate_certificate = {
            "schema_version": certificate.get("schema_version", "adaptive_ladder_l12_policy_certificate.v1"),
            "protocol_sha256": certificate.get("protocol_sha256", certificate.get("protocol_hash")),
            "root_information_set_id": certificate.get("root_information_set_id"),
            "root_action": alt_root_action,
            "root_worst_case_value": alt_root_value,
            "evaluated_information_set_count": certificate.get("evaluated_information_set_count", certificate.get("information_set_count")),
            "delayed_reveal_state_count": certificate.get("delayed_reveal_state_count", certificate.get("pending_information_set_count", len(certificate.get("pending_information_sets", [])))),
            "adversarial_branch_count": certificate.get("adversarial_branch_count", sum(item.get("adversarial_branch_count", 0) for item in policy_rows)),
            "claim_scope": normalized_scope,
            "overall_decision": normalized_decision,
        }
        if "root_action_values" in certificate and certificate["root_action_values"].get(expected_certificate["root_action"]) != expected_certificate["root_worst_case_value"]:
            alternate_certificate["root_action"] = "__invalid__"
        if "pending_information_sets" in certificate and len(certificate["pending_information_sets"]) != expected_certificate["delayed_reveal_state_count"]:
            alternate_certificate["delayed_reveal_state_count"] = -1
        if alternate_certificate != expected_certificate:
            errors.append("policy contract: policy_certificate.json mismatch")
    if root[1] != truth["root_action"] or root[0] != truth["root_worst_case_value"]:
        errors.append("policy truth: root minimax decision mismatch")
    for scenario in truth["hidden_scenarios"]:
        state_id = protocol["root_information_set_id"]
        signal_index = 0
        terminal = None
        while state_id not in terminals:
            row = states[state_id]
            submitted = next((item for item in policy_rows if item.get("information_set_id") == state_id), None)
            if submitted is None:
                errors.append(f"policy replay: missing row {state_id} for {scenario['id']}")
                break
            action = next((item for item in row["actions"] if item["action"] == submitted.get("chosen_action")), None)
            if action is None:
                errors.append(f"policy replay: invalid action {state_id} for {scenario['id']}")
                break
            if signal_index >= len(scenario["signals"]):
                errors.append(f"policy replay: short hidden trajectory {scenario['id']}")
                break
            signal = scenario["signals"][signal_index]
            branch = next((item for item in action["branches"] if item["signal"] == signal), None)
            if branch is None:
                errors.append(f"policy replay: branch mismatch {state_id} for {scenario['id']}")
                break
            state_id = branch["next_state"]
            signal_index += 1
            terminal = state_id
        if terminal != scenario["terminal"]:
            errors.append(f"policy replay: terminal mismatch for {scenario['id']}")
    return errors


def verify(submission, data, reference=None):
    errors = []
    try:
        log = load(submission / "research_log.json")
        completion = load(submission / "completion.json")
        provenance = load(submission / "provenance.json")
        audit = (submission / "audit.md").read_text(encoding="utf-8")
        rules = load(data / "rules.json")
        contract = load(data / "action_contract.json")
        output_contract = load(data / "output_contract.json")
        protocol = load(data / "partial_observation_protocol.json")
        policy_truth = load(Path(__file__).parent / "verifier_only/policy_truth.json")
        actions = {
            row["id"]: row
            for row in load(data / "action_catalog.json")["actions"]
        }
        scenario_payload = load(Path(__file__).parent / "verifier_only/scenario.json")
    except (OSError, UnicodeError, ValueError, KeyError) as exc:
        return False, ["delivery: " + str(exc)]

    if not isinstance(log, dict):
        return False, ["contract: research_log.json must contain an object"]
    if not isinstance(completion, dict):
        return False, ["contract: completion.json must contain an object"]
    if not isinstance(provenance, dict):
        return False, ["contract: provenance.json must contain an object"]

    scenario = scenario_payload["outcomes"]
    seed = scenario_payload["chain_seed"]
    token = contract["state_token"]["genesis"]
    events = log.get("events")
    if not isinstance(events, list) or not events:
        errors.append("contract: events must be a nonempty array")
        events = []

    used = set()
    states = set()
    resolved = set()
    spent = 0
    previous_round = 0
    for event in events:
        if not isinstance(event, dict):
            errors.append("contract: event must be an object")
            continue
        missing_fields = set(output_contract["event_fields"]) - set(event)
        if missing_fields:
            errors.append("contract: event missing fields " + ",".join(sorted(missing_fields)))
        round_no = event.get("round")
        action_id = event.get("action_id")
        if not isinstance(round_no, int) or round_no != previous_round + 1:
            errors.append("contract: rounds must be contiguous")
        valid_round = round_no if isinstance(round_no, int) else previous_round + 1
        previous_round = valid_round
        action = actions.get(action_id)
        if action is None:
            errors.append("scientific: unknown action " + str(action_id))
            continue
        if action_id in used:
            errors.append("scientific: repeated action " + action_id)
        if not set(action.get("requires", [])).issubset(states):
            errors.append("scientific: unmet dependency for " + action_id)
        requires_any = action.get("requires_any", [])
        if requires_any and not states.intersection(requires_any):
            errors.append("scientific: unmet dependency for " + action_id)
        if action_id == "stop":
            missing = activated_checks(rules, states) - resolved - {"stop_rule"}
            if missing:
                errors.append("scientific: early stop with incomplete checks")

        expected = {"outcome": "stopped", "cost": 0, "measurements": []}
        if action_id != "stop":
            expected = scenario.get(action_id, {})
        outcome = expected.get("outcome")
        cost = expected.get("cost")
        expected_token = state_token(seed, token, valid_round, action_id, outcome)
        if event.get("observed_outcome") != outcome:
            errors.append("scientific: outcome mismatch for " + action_id)
        if event.get("cost") != cost:
            errors.append("contract: cost mismatch for " + action_id)
        if event.get("state_token") != expected_token:
            errors.append("contract: state-token mismatch for " + action_id)

        history = submission / "feedback_history"
        request_path = history / f"round-{valid_round:03d}-request.json"
        response_path = history / f"round-{valid_round:03d}-response.json"
        try:
            request = load(request_path)
            response = load(response_path)
        except (OSError, UnicodeError, ValueError) as exc:
            errors.append(f"contract: missing or invalid history for round {round_no}: {exc}")
        else:
            if (
                request.get("round") != round_no
                or request.get("action_id") != action_id
                or request.get("prior_state_token") != token
            ):
                errors.append(f"contract: request history mismatch for round {round_no}")
            if (
                response.get("round") != round_no
                or response.get("action_id") != action_id
                or response.get("outcome") != outcome
                or response.get("cost_charged") != cost
                or response.get("observed_measurements") != expected.get("measurements", [])
                or response.get("remaining_budget") != rules["budget"] - spent - cost
                or response.get("state_token") != expected_token
                or response.get("accepted") is not True
            ):
                errors.append(f"contract: response history mismatch for round {round_no}")

        spent += cost
        if spent > rules["budget"]:
            errors.append("scientific: budget overspend")
        used.add(action_id)
        states.add(outcome)
        resolved.add(action["resolves"])
        token = expected_token

    if len(events) > rules["max_rounds"]:
        errors.append("contract: max rounds exceeded")
    if not events or not isinstance(events[-1], dict) or events[-1].get("action_id") != "stop":
        errors.append("contract: accepted stop must be the final event")
    required = activated_checks(rules, states)
    missing = required - resolved
    if missing:
        errors.append("scientific: missing activated checks " + ",".join(sorted(missing)))

    submitted_checks = completion.get("checks")
    if not isinstance(submitted_checks, dict) or set(submitted_checks) != required:
        errors.append("contract: completion check coverage mismatch")
    elif any(submitted_checks[key] is not True for key in required):
        errors.append("contract: completion checks must be boolean true")

    expected_claims = rules["final_claims"]
    if log.get("final_claims") != expected_claims:
        errors.append("scientific: final claims mismatch")
    if completion.get("stop_reason") not in {"bounded_handoff", "evidence_complete"}:
        errors.append("contract: stop_reason mismatch")
    if completion.get("human_review_required") is not True:
        errors.append("contract: human review must be true")
    if completion.get("claim_boundary") != rules["claim_boundary"]:
        errors.append("contract: claim boundary mismatch")

    expected_hashes = {
        path.name: digest(path) for path in sorted(data.glob("*.json"))
    }
    expected_provenance = {
        "input_sha256": expected_hashes,
        "rules_version": rules["rules_version"],
        "network": "off",
        "deterministic": True,
    }
    if provenance != expected_provenance:
        data_prefixed_hashes = {"data/" + key: value for key, value in expected_hashes.items()}
        alternate_provenance = dict(provenance)
        alternate_provenance["input_sha256"] = data_prefixed_hashes
        if alternate_provenance != {**expected_provenance, "input_sha256": data_prefixed_hashes}:
            errors.append("contract: provenance mismatch")
    if not audit.strip():
        errors.append("delivery: empty audit.md")
    for evidence_id in output_contract.get("audit_evidence_ids", []):
        if evidence_id not in audit:
            errors.append("delivery: audit.md missing measurement " + evidence_id)
    errors.extend(verify_policy(submission, data, protocol, policy_truth))
    return not errors, errors


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--submission", type=Path, required=True)
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--reference", type=Path, required=True)
    args = parser.parse_args()
    passed, errors = verify(args.submission, args.data, args.reference)
    print(json.dumps({"passed": passed, "errors": errors}))
    raise SystemExit(0 if passed else 1)
