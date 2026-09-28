from benchmark_runner.continuation_controller import (
    ContinuationController,
    GateReceipt,
    SubmissionState,
    snapshot_submission,
)


def test_missing_requirements_return_then_accept_without_resetting_attempts():
    controller = ContinuationController(max_attempts=3)
    first = controller.submit("v1", lambda: GateReceipt(False, ("missing:audit",)))
    second = controller.submit("v2", lambda: GateReceipt(True))
    assert first.state is SubmissionState.NEEDS_REVISION
    assert second.state is SubmissionState.ACCEPTED
    assert controller.attempts == 2
    assert controller.summary()["events"][0]["issues"] == ["missing:audit"]


def test_duplicate_submission_is_idempotent():
    controller = ContinuationController(max_attempts=2)
    calls = []

    def gate():
        calls.append(1)
        return GateReceipt(False, ("missing:check",))

    first = controller.submit("same", gate)
    duplicate = controller.submit("same", gate)
    assert duplicate == first
    assert calls == [1]
    assert controller.attempts == 1


def test_budget_stop_is_terminal_and_does_not_fake_acceptance():
    controller = ContinuationController(max_attempts=1)
    controller.submit("v1", lambda: GateReceipt(False, ("missing:check",)))
    stopped = controller.submit("v2", lambda: GateReceipt(True))
    assert stopped.state is SubmissionState.STOPPED_BUDGET
    assert controller.summary()["state"] == "STOPPED_BUDGET"


def test_ledger_round_trip_preserves_attempts_and_duplicate_idempotence(tmp_path):
    ledger = tmp_path / "outputs/completion_attempts.json"
    controller = ContinuationController(max_attempts=3, ledger_path=ledger)
    first = controller.submit("v1", lambda: GateReceipt(False, ("missing:audit",)))
    assert first.attempt == 1
    restored = ContinuationController.load(ledger)
    duplicate = restored.submit("v1", lambda: GateReceipt(True))
    assert duplicate.state is SubmissionState.NEEDS_REVISION
    assert restored.attempts == 1
    accepted = restored.submit("v2", lambda: GateReceipt(True))
    assert accepted.state is SubmissionState.ACCEPTED
    saved = ledger.read_text()
    assert "submission_fingerprint" in saved


def test_fingerprint_is_stable_for_visible_json_payload():
    payload = {"completion": {"checks": {"a": True}}, "files": ["audit.md"]}
    assert ContinuationController.fingerprint(payload) == ContinuationController.fingerprint({"files": ["audit.md"], "completion": {"checks": {"a": True}}})


def test_repeated_bad_submission_stops_for_no_progress():
    controller = ContinuationController(max_attempts=3, max_no_progress=3)
    first = controller.submit("same", lambda: GateReceipt(False, ("missing:check",)))
    assert first.state is SubmissionState.NEEDS_REVISION
    assert controller.submit("same", lambda: GateReceipt(True)).state is SubmissionState.NEEDS_REVISION
    assert controller.submit("same", lambda: GateReceipt(True)).state is SubmissionState.NEEDS_REVISION
    stopped = controller.submit("same", lambda: GateReceipt(True))
    assert stopped.state is SubmissionState.STOPPED_NO_PROGRESS
    assert controller.attempts == 1


def test_accepted_snapshot_is_immutable_and_hashed(tmp_path):
    source = tmp_path / "outputs"
    source.mkdir()
    (source / "completion.json").write_text('{"accepted": true}\n')
    destination = tmp_path / "accepted_submission"
    manifest = snapshot_submission(source, destination)
    assert manifest["completion.json"]
    assert (destination / "snapshot_manifest.json").is_file()
    (source / "completion.json").write_text('{"accepted": false}\n')
    assert (destination / "completion.json").read_text() == '{"accepted": true}\n'
