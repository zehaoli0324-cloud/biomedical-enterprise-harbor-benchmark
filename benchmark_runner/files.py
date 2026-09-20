from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Iterable


class RunnerError(ValueError):
    """Raised when a task cannot be prepared or a trial cannot be archived."""


def repository_root(path: Path) -> Path | None:
    """Find a Git root without assuming that every task is stored in Git."""
    try:
        result = subprocess.run(
            ["git", "-C", str(path), "rev-parse", "--show-toplevel"],
            text=True,
            capture_output=True,
            check=False,
        )
    except OSError:
        return None
    if result.returncode != 0 or not result.stdout.strip():
        return None
    return Path(result.stdout.strip()).resolve()


def ensure_trial_root_is_external(task_dir: Path, output_root: Path) -> None:
    """Prevent process adapters from walking from workspace into the source repo."""
    root = repository_root(task_dir)
    if root is not None:
        try:
            output_root.relative_to(root)
        except ValueError:
            return
        raise RunnerError(
            "trial output must be outside the task Git repository for process isolation; "
            f"use a path such as /tmp/benchmark-runs, not {output_root}"
        )


def read_task_id(task_dir: Path) -> str:
    task_file = task_dir / "task.yaml"
    if not task_file.is_file():
        raise RunnerError(f"task is missing task.yaml: {task_dir}")
    for line in task_file.read_text(encoding="utf-8").splitlines():
        if line.startswith("id:"):
            task_id = line.split(":", 1)[1].strip().strip('"\'')
            if task_id:
                return task_id
    raise RunnerError(f"task.yaml does not declare an id: {task_file}")


def ensure_no_symlinks(path: Path) -> None:
    for item in path.rglob("*"):
        if item.is_symlink():
            raise RunnerError(f"symlinks are not allowed in agent-visible inputs: {item}")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def visible_file_hashes(workspace: Path) -> dict[str, str]:
    return {
        str(path.relative_to(workspace)): sha256_file(path)
        for path in sorted(workspace.rglob("*"))
        if path.is_file()
    }


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def copy_agent_visible_inputs(task_dir: Path, workspace: Path) -> None:
    instruction = task_dir / "instruction.md"
    data = task_dir / "data"
    if not instruction.is_file():
        raise RunnerError(f"task is missing agent instruction: {instruction}")
    if not data.is_dir():
        raise RunnerError(f"task is missing agent-visible data directory: {data}")
    ensure_no_symlinks(instruction.parent)
    shutil.copy2(instruction, workspace / "instruction.md")
    shutil.copytree(data, workspace / "data", symlinks=False)
    (workspace / "outputs").mkdir(parents=True, exist_ok=False)


def clean_environment(base: dict[str, str] | None = None) -> dict[str, str]:
    """Return a small inherited environment without task/repo-specific secrets."""
    source = dict(base or os.environ)
    allowed = {
        key: value
        for key, value in source.items()
        if key in {"PATH", "HOME", "LANG", "LC_ALL", "TMPDIR", "USER", "SHELL"}
    }
    allowed.setdefault("LANG", "C.UTF-8")
    allowed.setdefault("LC_ALL", "C.UTF-8")
    return allowed


def utc_trial_id() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).strftime("trial-%Y%m%dT%H%M%SZ")
