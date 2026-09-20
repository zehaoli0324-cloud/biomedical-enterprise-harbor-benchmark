from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class PreparedTrial:
    task_dir: Path
    trial_dir: Path
    workspace: Path
    outputs: Path
    task_id: str
    trial_id: str
    prompt_path: Path
    manifest_path: Path


@dataclass(frozen=True)
class TrialResult:
    task_id: str
    trial_id: str
    trial_dir: Path
    status: str
    agent_exit_code: int | None
    verifier_status: str | None
    verifier_score: float | None
    timed_out: bool
    manifest_path: Path

    def to_dict(self) -> dict[str, object]:
        return {
            "task_id": self.task_id,
            "trial_id": self.trial_id,
            "trial_dir": str(self.trial_dir),
            "status": self.status,
            "agent_exit_code": self.agent_exit_code,
            "verifier_status": self.verifier_status,
            "verifier_score": self.verifier_score,
            "timed_out": self.timed_out,
            "manifest_path": str(self.manifest_path),
        }
