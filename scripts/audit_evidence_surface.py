#!/usr/bin/env python3
"""Audit source closure and evidence-surface/abstention risk for benchmark tasks."""

from __future__ import annotations

import json
import re
import subprocess
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BENCHMARKS = ROOT / "benchmarks"
OUTPUT = ROOT / "reports/evidence_surface_abstention_audit_2026-09-24.md"


def load(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def approximate_records(path: Path) -> int:
    try:
        if path.suffix in {".csv", ".tsv"}:
            return max(0, sum(1 for _ in path.open(encoding="utf-8", errors="replace")) - 1)
        if path.suffix == ".json":
            value = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(value, list):
                return len(value)
            if isinstance(value, dict):
                lengths = [len(item) for item in value.values() if isinstance(item, list)]
                return max(lengths or [1])
    except (OSError, UnicodeError, json.JSONDecodeError, TypeError):
        pass
    return 1


def output_count(task: Path) -> int:
    path = task / "task.yaml"
    text = path.read_text(encoding="utf-8", errors="replace") if path.is_file() else ""
    return len(re.findall(r"path:\s*outputs/", text))


def source_status(task: Path) -> str:
    sop = load(task / "quality/sop_card.json")
    if sop.get("source_status"):
        return str(sop["source_status"])
    evidence = load(task / "evidence_quality.json")
    return str(evidence.get("source_status", "UNREGISTERED"))


def fixture_status(task: Path) -> str:
    evidence = load(task / "evidence_quality.json")
    if evidence.get("fixture_classification"):
        return str(evidence["fixture_classification"])
    sop = load(task / "quality/sop_card.json")
    return str(sop.get("source_status", "UNREGISTERED"))


def abstain_status(task: Path) -> str:
    results = load(task / "quality/model_trial_results.json")
    records = [item for item in results.get("records", []) if isinstance(item, dict) and item.get("strategy") == "always_abstain"]
    return str(records[-1].get("status", "UNRECORDED")) if records else "UNRECORDED"


def main() -> int:
    tasks = [path for path in sorted(BENCHMARKS.iterdir()) if path.is_dir()]
    tracked_files = subprocess.run(
        ["git", "ls-files", "benchmarks/*/task.yaml"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    ).stdout.splitlines()
    tracked_ids = {Path(path).parent.name for path in tracked_files}
    tracked_tasks = [task for task in tasks if task.name in tracked_ids]
    candidate_tasks = [task for task in tasks if task.name not in tracked_ids]
    source_counts = Counter(source_status(task) for task in tasks)
    critical_files = {
        "claim_evidence_map.tsv": sum(1 for _ in ROOT.rglob("claim_evidence_map.tsv")),
        "source_manifest.json": sum(1 for _ in ROOT.rglob("source_manifest.json")),
        "source_freeze_manifest.json": sum(1 for _ in ROOT.rglob("source_freeze_manifest.json")),
        "scientific_review.json": sum(1 for _ in ROOT.rglob("scientific_review.json")),
    }
    mapped_tasks = [task.name for task in tasks if (task / "quality/claim_evidence_map.tsv").is_file()]
    abstain_counts = Counter(abstain_status(task) for task in tasks)
    rows = []
    high_risk = []
    for task in tasks:
        files = [
            path for path in (task / "data").rglob("*")
            if path.is_file() and path.name not in {"README.md"}
        ] if (task / "data").is_dir() else []
        records = sum(approximate_records(path) for path in files)
        outputs = output_count(task)
        missing_verifier = not (task / "verifier.py").is_file() and not (task / "tests/verifier.py").is_file()
        missing_reference = not any((task / "verifier_only" / name).is_file() for name in ("reference.json", "reference_labels.json"))
        risk = []
        if outputs >= 5 and records <= 7:
            risk.append("many_outputs_small_visible_data")
            high_risk.append(task.name)
        if missing_verifier:
            risk.append("verifier_missing")
        if missing_reference:
            risk.append("reference_missing")
        rows.append((task.name, source_status(task), fixture_status(task), len(files), records, outputs, abstain_status(task), "yes" if task.name in mapped_tasks else "no", ",".join(risk) or "-"))
    mapped_high_risk = [task for task in high_risk if task in mapped_tasks]
    unmapped_high_risk = [task for task in high_risk if task not in mapped_tasks]

    lines = [
        "# Evidence Surface and Abstention Audit (2026-09-24)",
        "",
        "对照《改题方案与检查标准 v1.0》§12.4、§12.7、§12.11。此报告是静态审计和已有 trial 记录汇总，不把合成 fixture 当作原始真实数据，也不把未执行的动态门禁算作通过。",
        "",
        "## 结论",
        "",
        f"- 题目范围：Git 正式题包 **{len(tracked_tasks)}** 道；当前工作树共 **{len(tasks)}** 道，其中 **{len(candidate_tasks)}** 道尚未纳入 Git，属于候选/实验题。以下静态表默认覆盖工作树全部题包，但正式发布统计应以 Git 正式题包为准。",
        f"- 原始数据/参考文献闭环：**未解决**。当前逐题证据映射为 {len(mapped_tasks)}/{len(tasks)}（正式题包为 {sum(1 for task in tracked_tasks if task.name in mapped_tasks)}/{len(tracked_tasks)}），但 `source_manifest.json`、`source_freeze_manifest.json` 和 `scientific_review.json` 仍未建立（计数：`{critical_files}`）。",
        f"- 数据不足导致弃权的风险：**存在，且尚未被门禁排除**。发现 {len(high_risk)} 道题属于“输出项较多但可见数据规模很小”的高风险候选；这不是仅凭文件数判定题目错误，而是必须补做证据面映射和四种弃权变体。",
        f"- 已有 `always_abstain` 记录：`{dict(abstain_counts)}`。记录只有 pass/fail 状态，没有按科学判断单元的得分权重，因此不能证明 blanket-abstain 低于正确分析的 70%。",
        "- 四种弃权变体门禁：6 道高风险题已有逐题计划，但当前执行数为 0；详见 `reports/abstention_variant_gate_2026-09-24.md`。",
        "",
        "## 来源与参考文献门禁",
        "",
        "| source_status | 题数 | 含义 |",
        "|---|---:|---|",
    ]
    for status, count in sorted(source_counts.items()):
        lines.append(f"| `{status}` | {count} | 仍需 source freeze / scientific review 才能发布 |")
    lines += [
        "",
        "明确的高风险来源题：`literature-screening-m1-001` 和 `research-workflow-stress-test-001` 的 `evidence_quality.json` 标记为 `PLACEHOLDER_OR_MISSING`，并报告 `PLACEHOLDER_DOI`；`crispr-resistance-e2e-001` 缺少 verifier 和 reference 文件。",
        "",
        "## 弃权风险候选",
        "",
        "以下仅按“可见 data 文件近似记录数 <= 7 且 required outputs >= 5”筛出待复核项；嵌套 JSON 的实际科学单元必须由题作者逐题确认：",
        "",
        "`" + "`, `".join(high_risk) + "`",
        "",
        f"其中已补映射：`{', '.join(mapped_high_risk)}`；仍未能映射且已转为阻断修复卡：`{', '.join(unmapped_high_risk)}`。已映射题仍必须运行标准要求的四个变体：全部弃权、全部确定回答、一个正例回答+一个缺证据弃权、把正例改成错误弃权。当前仓库没有这些变体的逐题分数和权重记录。",
        "",
        "## 逐题静态摘要",
        "",
        "| task | source_status | fixture | data files | approx records | outputs | always_abstain | evidence_map | risk |",
        "|---|---|---|---:|---:|---:|---|---|---|",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(item) for item in row) + " |")
    lines += [
        "",
        "## 判定",
        "",
        f"1. 问题 1 的答案是：**没有解决**。正式 Git 范围是 {len(tracked_tasks)} 道，其中多数题明确是 synthetic/calibration fixture；这可以用于工程校准，但不等于有已核验的原始数据和参考文献。正式发布还缺来源冻结、逐文件 hash、许可/隐私审查和具名科学审阅。",
        "2. 问题 2 的答案是：**风险存在，不能判定已解决**。已有基线中的 `always_abstain` 没有记录为通过，但这只说明提交未通过当前 verifier，不能替代按科学考察单元计算的弃权比例和 blanket-abstain 分数；尤其不能排除数据只支持少数判断、其余判断靠弃权的情况。",
        "",
        f"下一步必须是把剩余 {len(tasks) - len(mapped_tasks)} 道题补齐证据面矩阵，并对已映射题重新运行 verifier mutation、Docker 动态 oracle/nop 及四种弃权变体。",
        "",
    ]
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({"tasks": len(tasks), "tracked_tasks": len(tracked_tasks), "candidate_tasks": len(candidate_tasks), "mapped_tasks": mapped_tasks, "high_risk_small_surface": high_risk, "source_status": dict(source_counts), "abstain_status": dict(abstain_counts)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
