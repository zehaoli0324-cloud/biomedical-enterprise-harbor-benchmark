"""Deterministic public completion/continuation state machine.

The controller only sees a submission snapshot and a public completion gate.
Scientific scoring and hidden reference data remain outside this protocol.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import hashlib
import json
import shutil
from pathlib import Path
from typing import Callable, Mapping


class SubmissionState(str, Enum):
    WORKING = "WORKING"
    NEEDS_REVISION = "NEEDS_REVISION"
    ACCEPTED = "ACCEPTED"
    STOPPED_BUDGET = "STOPPED_BUDGET"
    STOPPED_INFRASTRUCTURE = "STOPPED_INFRASTRUCTURE"
    STOPPED_NO_PROGRESS = "STOPPED_NO_PROGRESS"


@dataclass(frozen=True)
class GateReceipt:
    accepted: bool
    issues: tuple[str, ...] = ()


@dataclass(frozen=True)
class ContinuationEvent:
    attempt: int
    state: SubmissionState
    receipt: GateReceipt | None = None
    reason: str | None = None
    submission_fingerprint: str | None = None


@dataclass
class ContinuationController:
    """Apply public completion feedback without resetting task state or budget."""

    max_attempts: int = 3
    max_no_progress: int = 3
    ledger_path: str | Path | None = None
    events: list[ContinuationEvent] = field(default_factory=list)
    _last_fingerprint: str | None = None
    _duplicate_count: int = 0

    @staticmethod
    def fingerprint(payload: object) -> str:
        """Return a stable, non-secret identity for one visible submission."""
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()

    @classmethod
    def load(cls, path: str | Path, *, max_attempts: int = 3, max_no_progress: int = 3) -> "ContinuationController":
        path = Path(path)
        if not path.is_file():
            return cls(max_attempts=max_attempts, ledger_path=path)
        payload = json.loads(path.read_text(encoding="utf-8"))
        controller = cls(
            max_attempts=int(payload.get("max_attempts", max_attempts)),
            max_no_progress=int(payload.get("max_no_progress", max_no_progress)),
            ledger_path=path,
        )
        for item in payload.get("events", []):
            receipt_payload = item.get("receipt")
            receipt = None
            if isinstance(receipt_payload, dict):
                receipt = GateReceipt(bool(receipt_payload.get("accepted")), tuple(receipt_payload.get("issues", [])))
            controller.events.append(
                ContinuationEvent(
                    int(item["attempt"]),
                    SubmissionState(item["state"]),
                    receipt=receipt,
                    reason=item.get("reason"),
                    submission_fingerprint=item.get("submission_fingerprint"),
                )
            )
        if controller.events:
            controller._last_fingerprint = controller.events[-1].submission_fingerprint
        controller._duplicate_count = int(payload.get("duplicate_count", 0))
        return controller

    def save(self, path: str | Path | None = None) -> Path:
        target = Path(path or self.ledger_path) if (path or self.ledger_path) else None
        if target is None:
            raise ValueError("a ledger path is required")
        target.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "schema_version": "benchmark_runner.continuation_ledger.v1",
            "max_attempts": self.max_attempts,
            "max_no_progress": self.max_no_progress,
            "duplicate_count": self._duplicate_count,
            "events": [
                {
                    "attempt": event.attempt,
                    "state": event.state.value,
                    "receipt": (
                        {"accepted": event.receipt.accepted, "issues": list(event.receipt.issues)}
                        if event.receipt
                        else None
                    ),
                    "reason": event.reason,
                    "submission_fingerprint": event.submission_fingerprint,
                }
                for event in self.events
            ],
        }
        target.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        return target

    def _record(self, event: ContinuationEvent) -> ContinuationEvent:
        self.events.append(event)
        if self.ledger_path:
            self.save()
        return event

    def submit(
        self,
        submission_fingerprint: str,
        gate: Callable[[], GateReceipt],
    ) -> ContinuationEvent:
        if self.events and self.events[-1].state in {
            SubmissionState.ACCEPTED,
            SubmissionState.STOPPED_BUDGET,
            SubmissionState.STOPPED_INFRASTRUCTURE,
            SubmissionState.STOPPED_NO_PROGRESS,
        }:
            return self.events[-1]
        if self.attempts >= self.max_attempts:
            return self._record(ContinuationEvent(self.attempts, SubmissionState.STOPPED_BUDGET, reason="attempt_budget_exhausted"))
        # Repeated submit requests are idempotent and must not consume an attempt.
        if submission_fingerprint == self._last_fingerprint and self.events:
            self._duplicate_count += 1
            if self._duplicate_count >= self.max_no_progress:
                return self._record(
                    ContinuationEvent(
                        self.attempts,
                        SubmissionState.STOPPED_NO_PROGRESS,
                        reason="no_progress",
                        submission_fingerprint=submission_fingerprint,
                    )
                )
            if self.ledger_path:
                self.save()
            return self.events[-1]
        self._last_fingerprint = submission_fingerprint
        self._duplicate_count = 0
        attempt = self.attempts + 1
        receipt = gate()
        state = SubmissionState.ACCEPTED if receipt.accepted else SubmissionState.NEEDS_REVISION
        return self._record(ContinuationEvent(attempt, state, receipt=receipt, submission_fingerprint=submission_fingerprint))

    def stop(self, reason: str) -> ContinuationEvent:
        if self.events and self.events[-1].state in {
            SubmissionState.ACCEPTED,
            SubmissionState.STOPPED_BUDGET,
            SubmissionState.STOPPED_INFRASTRUCTURE,
            SubmissionState.STOPPED_NO_PROGRESS,
        }:
            return self.events[-1]
        if reason == "infrastructure":
            state = SubmissionState.STOPPED_INFRASTRUCTURE
        elif reason == "no_progress":
            state = SubmissionState.STOPPED_NO_PROGRESS
        else:
            state = SubmissionState.STOPPED_BUDGET
        return self._record(ContinuationEvent(self.attempts, state, reason=reason))

    @property
    def attempts(self) -> int:
        return sum(event.state in {SubmissionState.NEEDS_REVISION, SubmissionState.ACCEPTED} for event in self.events)

    def summary(self) -> Mapping[str, object]:
        return {
            "state": self.events[-1].state.value if self.events else SubmissionState.WORKING.value,
            "attempts": self.attempts,
            "max_attempts": self.max_attempts,
            "max_no_progress": self.max_no_progress,
            "duplicate_count": self._duplicate_count,
            "events": [
                {
                    "attempt": event.attempt,
                    "state": event.state.value,
                    "issues": list(event.receipt.issues) if event.receipt else [],
                    "reason": event.reason,
                    "submission_fingerprint": event.submission_fingerprint,
                }
                for event in self.events
            ],
        }


def snapshot_submission(source: str | Path, destination: str | Path) -> dict[str, str]:
    """Freeze an accepted submission with a file-level SHA-256 manifest."""
    source_path = Path(source)
    destination_path = Path(destination)
    if not source_path.is_dir():
        raise ValueError("submission source must be a directory")
    if destination_path.exists():
        raise FileExistsError(destination_path)
    shutil.copytree(source_path, destination_path)
    manifest: dict[str, str] = {}
    for path in sorted(destination_path.rglob("*")):
        if path.is_file():
            manifest[str(path.relative_to(destination_path))] = hashlib.sha256(path.read_bytes()).hexdigest()
    (destination_path / "snapshot_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return manifest
