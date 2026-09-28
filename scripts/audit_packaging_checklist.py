#!/usr/bin/env python3
"""Audit package artifacts and checklist gaps for every scoped benchmark task."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import re
import tarfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PIPELINE = ROOT / "scripts/check_task_pipeline.py"
CONTRACT_FILES = [
    "candidate_design.json",
    "scenario-card.yaml",
    "data/output_contract.json",
    "quality/sop_card.json",
]
EVIDENCE_FILES = [
    "data/source_manifest.json",
    "data/source_freeze_manifest.json",
    "data/numeric_provenance.tsv",
    "data/release_input_manifest.json",
    "quality/claim_evidence_map.tsv",
    "quality/scientific_review.json",
]


def load_evaluator():
    spec = importlib.util.spec_from_file_location("task_pipeline_checker", PIPELINE)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module.evaluate


def scoped_ids() -> tuple[list[str], list[str]]:
    scope = json.loads((ROOT / "config/task_scope.v1.json").read_text(encoding="utf-8"))
    return scope["formal_release_scope"], scope["candidate_only_scope"]


def archive_index(task_ids: list[str]) -> dict[str, list[dict[str, Any]]]:
    index = {task_id: [] for task_id in task_ids}
    for archive in sorted((ROOT / "dist").rglob("*.tar.gz")):
        try:
            names = tarfile.open(archive).getnames()
        except (OSError, tarfile.TarError):
            continue
        for task_id in task_ids:
            if not any(re.search(rf"(^|/){re.escape(task_id)}(/|$)", name) for name in names):
                continue
            sidecar = Path(str(archive) + ".sha256")
            digest = hashlib.sha256(archive.read_bytes()).hexdigest()
            declared = sidecar.read_text(encoding="utf-8", errors="replace").split()[0] if sidecar.is_file() else None
            index[task_id].append(
                {
                    "path": archive.relative_to(ROOT).as_posix(),
                    "sha256_sidecar": sidecar.is_file(),
                    "sha256_matches": bool(declared and declared == digest),
                }
            )
    return index


def read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def has_fixed_replay(package: Path) -> bool:
    candidates = [
        package / "quality/container_replays",
        package / "quality/fixed_container_replay.json",
        package / "quality/fixed-container-replay.json",
        package / "quality/replay_manifest.json",
    ]
    return any(path.is_dir() and any(path.iterdir()) or path.is_file() for path in candidates)


def has_practitioner_review(package: Path) -> bool:
    names = {"practitioner_review.json", "scientific_review.json", "review_record.json"}
    return any(path.name in names for path in package.rglob("*") if path.is_file())


def checklist_actions(row: dict[str, Any]) -> list[str]:
    actions: list[str] = []
    if "task_identity" in row["blockers"]:
        actions.append("FIX_TASK_IDENTITY")
    if row["missing_contract"]:
        actions.append("COMPLETE_CONTRACT_FILES")
    if row["source_status"] in {"UNKNOWN", "REVIEW_REQUIRED", "PLACEHOLDER_OR_MISSING", "UNREGISTERED", None}:
        actions.append("CLASSIFY_SOURCE_AND_CLAIM_BOUNDARY")
    if row["missing_evidence"]:
        actions.append("ADD_SOURCE_FREEZE_NUMERIC_PROVENANCE_CLAIM_MAP_REVIEW")
    if row["controls_status"] not in {"CALIBRATED", "PASS"}:
        actions.append("RUN_FOUR_CONTROL_CALIBRATION")
    if row["target_model_status"] in {None, "", "NOT_RUN", "RECALIBRATION_REQUIRED"}:
        actions.append("RUN_CURRENT_TARGET_TRIAL_AND_ANALYSIS")
    if not row["fixed_container_replay"]:
        actions.append("RUN_FIXED_CONTAINER_REPLAY_AND_HASH_CAPTURE")
    if row["review_status"] != "APPROVED" or not row["practitioner_review"]:
        actions.append("COMPLETE_SCIENTIFIC_AND_PRACTITIONER_REVIEW")
    if not row["archives"]:
        actions.append("BUILD_PACKAGE_AND_SHA256")
    elif not row["sha256_valid_archive"]:
        actions.append("REPACKAGE_WITH_VALID_SHA256")
    actions.append("UNPACK_DIFF_AND_ARCHIVE_RELEASE_MANIFEST")
    return actions


def audit() -> dict[str, Any]:
    formal, candidate = scoped_ids()
    task_ids = formal + candidate
    evaluate = load_evaluator()
    archives = archive_index(task_ids)
    rows: list[dict[str, Any]] = []
    for task_id in task_ids:
        package = ROOT / "benchmarks" / task_id
        report = evaluate(package)
        quality = read_json(package / "quality/sop_card.json")
        trial = read_json(package / "quality/model_trial_results.json")
        task_archives = archives[task_id]
        row: dict[str, Any] = {
            "task_id": task_id,
            "scope": "formal" if task_id in formal else "candidate",
            "identity_task_id": report["task_id"],
            "pipeline_status": report["pipeline_status"],
            "evidence_status": report["evidence_status"],
            "review_status": report["review_status"],
            "release_status": report["release_status"],
            "blockers": report["blockers"],
            "release_blockers": report["release_blockers"],
            "source_status": quality.get("source_status") or read_json(package / "evidence_quality.json").get("source_status"),
            "controls_status": read_json(package / "controls/calibration_results.json").get("status", ""),
            "target_model_status": trial.get("target_model_status", ""),
            "missing_contract": [path for path in CONTRACT_FILES if not (package / path).is_file()],
            "missing_evidence": [path for path in EVIDENCE_FILES if not (package / path).is_file()],
            "claim_map": (package / "quality/claim_evidence_map.tsv").is_file(),
            "abstention_plan": (package / "quality/abstention_variant_plan.json").is_file(),
            "fixed_container_replay": has_fixed_replay(package),
            "practitioner_review": has_practitioner_review(package),
            "archives": task_archives,
            "archive_count": len(task_archives),
            "sha256_archive_count": sum(item["sha256_sidecar"] for item in task_archives),
            "sha256_valid_archive": any(item["sha256_matches"] for item in task_archives),
        }
        row["actions"] = checklist_actions(row)
        rows.append(row)

    def count(predicate):
        return sum(1 for row in rows if predicate(row))

    summary = {
        "task_count": len(rows),
        "formal_count": len(formal),
        "candidate_count": len(candidate),
        "formal_without_any_archive": count(lambda r: r["scope"] == "formal" and not r["archives"]),
        "candidate_without_any_archive": count(lambda r: r["scope"] == "candidate" and not r["archives"]),
        "all_without_any_archive": count(lambda r: not r["archives"]),
        "formal_with_valid_sha256_archive": count(lambda r: r["scope"] == "formal" and r["sha256_valid_archive"]),
        "candidate_with_valid_sha256_archive": count(lambda r: r["scope"] == "candidate" and r["sha256_valid_archive"]),
        "all_with_valid_sha256_archive": count(lambda r: r["sha256_valid_archive"]),
        "release_ready": count(lambda r: r["release_status"] == "READY_FOR_HARBOR"),
        "identity_blocked": count(lambda r: "task_identity" in r["blockers"]),
        "missing_contract": count(lambda r: bool(r["missing_contract"])),
        "missing_release_evidence": count(lambda r: bool(r["missing_evidence"])),
        "missing_fixed_replay": count(lambda r: not r["fixed_container_replay"]),
        "missing_review": count(lambda r: not r["practitioner_review"] or r["review_status"] != "APPROVED"),
    }
    return {
        "schema_version": "packaging_checklist_audit.v1",
        "generated_on": "2026-09-28",
        "checklist_source": "docs/改题方案与检查标准-v1.0.md",
        "pipeline_schema": "config/task_pipeline_schema.v1.json",
        "summary": summary,
        "tasks": rows,
    }


def markdown(report: dict[str, Any]) -> str:
    summary = report["summary"]
    rows = report["tasks"]
    lines = [
        "# Packaging and Checklist Audit (2026-09-28)",
        "",
        "依据：`docs/改题方案与检查标准-v1.0.md`、`config/task_pipeline_schema.v1.json`。本报告区分历史归档、带有效 SHA-256 的归档和满足发布门禁；有归档不等于可发布。",
        "",
        "## Counts",
        "",
        f"- 总题目：{summary['task_count']}（正式 {summary['formal_count']}，候选 {summary['candidate_count']}）。",
        f"- 没有任何可识别归档：{summary['all_without_any_archive']}（正式 {summary['formal_without_any_archive']}，候选 {summary['candidate_without_any_archive']}）。",
        f"- 有有效 `.sha256` 归档：{summary['all_with_valid_sha256_archive']}（正式 {summary['formal_with_valid_sha256_archive']}，候选 {summary['candidate_with_valid_sha256_archive']}）。",
        f"- `READY_FOR_HARBOR`：{summary['release_ready']}；缺合同文件：{summary['missing_contract']}；缺来源/证据文件：{summary['missing_release_evidence']}；缺固定容器复跑：{summary['missing_fixed_replay']}；缺科学/实践复核：{summary['missing_review']}。",
        "",
        "## Per-task checklist",
        "",
        "`A`=合同文件，`B`=来源/证据冻结，`C`=控制与当前 trial，`D`=固定容器重放，`E`=科学/实践复核，`F`=打包 SHA/解包复核，`I`=任务身份。",
        "",
        "| task | scope | archive | pipeline | release | missing | next actions |",
        "|---|---|---:|---|---|---|---|",
    ]
    for row in rows:
        missing = "".join(
            [
                "A" if row["missing_contract"] else "",
                "B" if row["missing_evidence"] else "",
                "C" if row["controls_status"] not in {"CALIBRATED", "PASS"} or row["target_model_status"] in {"", "NOT_RUN", "RECALIBRATION_REQUIRED"} else "",
                "D" if not row["fixed_container_replay"] else "",
                "E" if row["review_status"] != "APPROVED" or not row["practitioner_review"] else "",
                "F" if not row["sha256_valid_archive"] else "",
                "I" if "task_identity" in row["blockers"] else "",
            ]
        ) or "-"
        actions = ", ".join(row["actions"])
        lines.append(
            f"| `{row['task_id']}` | {row['scope']} | {row['archive_count']} / {row['sha256_archive_count']} | "
            f"{row['pipeline_status']} | {row['release_status']} | `{missing}` | {actions} |"
        )
    lines += [
        "",
        "## Interpretation",
        "",
        "1. 没有归档的题必须先完成合同、证据和动态门禁，再生成 `.tar.gz + .sha256`；不能只把目录复制到 `dist/` 算作完成。",
        "2. 有历史归档但没有有效 SHA-256 的题必须重新打包；有 SHA-256 也必须对当前题面、数据、verifier 做解包 `diff`，否则只能算历史包。",
        "3. 所有题当前都不是发布候选：缺 source freeze、具名 scientific review、practitioner review 或 fixed-container replay 时保持 `BLOCKED`。",
        "4. `I` 是管线本身的阻断项：`task.toml` 中带 `terminal-bench-science/` 前缀的身份必须和目录 ID 统一，不能依赖目录扫描猜测。",
        "",
        "机器可读明细：`reports/packaging_checklist_audit_20260928.json`。",
    ]
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", type=Path, default=ROOT / "reports/packaging_checklist_audit_20260928.json")
    parser.add_argument("--markdown", type=Path, default=ROOT / "reports/packaging_checklist_audit_20260928.md")
    args = parser.parse_args()
    report = audit()
    args.json.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    args.markdown.write_text(markdown(report), encoding="utf-8")
    print(json.dumps(report["summary"], ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
