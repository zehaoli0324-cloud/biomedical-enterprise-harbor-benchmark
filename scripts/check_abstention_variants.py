#!/usr/bin/env python3
"""Register the four required abstention variants without treating pass/fail baselines as scores."""

from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TASKS = [
    "eb010-closed-loop-ambiguity-004",
    "eb010-distributional-policy-stress-006",
    "eb010-stop-uncertainty-002",
    "eb011-reproduction-manifest-001",
    "eb013-evidence-budget-routing-001",
    "eb013-evidence-budget-routing-002",
]
VARIANTS = [
    ("all_abstain", "所有独立判断单元均输出弃权"),
    ("all_definite", "所有有证据判断单元均输出确定回答"),
    ("positive_plus_insufficient_abstain", "正例确定回答，设计内证据不足分支弃权"),
    ("positive_as_wrong_abstain", "把一个正例错误改为弃权，验证正例覆盖确实计分"),
]


def load_json(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else {}
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return {}


def map_summary(path: Path) -> dict:
    rows = list(csv.DictReader(path.open(encoding="utf-8"), delimiter="\t"))
    examples = []
    by_type = {}
    for row in rows:
        ids = [item.strip() for item in row.get("example_ids", "").split(",") if item.strip()]
        key = row.get("evidence_type", "")
        if key != "CONTROL_PARAMETER":
            examples.extend(ids)
        by_type[key] = by_type.get(key, 0) + len(ids)
    return {
        "map_rows": len(rows),
        "independent_example_units": len(set(examples)),
        "example_units_by_type": by_type,
        "score_weights_declared": False,
    }


def main() -> int:
    output = {"schema_version": "abstention_variant_gate.v1", "generated_on": "2026-09-24", "tasks": []}
    for task_id in TASKS:
        task = ROOT / "benchmarks" / task_id
        mapping = map_summary(task / "quality/claim_evidence_map.tsv")
        results = load_json(task / "quality/model_trial_results.json")
        baseline = [
            row for row in results.get("records", [])
            if isinstance(row, dict) and row.get("strategy") == "always_abstain"
        ]
        latest = baseline[-1] if baseline else None
        item = {
            "task_id": task_id,
            "evidence_surface": mapping,
            "existing_always_abstain_baseline": {
                "status": latest.get("status") if latest else "UNRECORDED",
                "failure_attribution": latest.get("failure_attribution") if latest else None,
                "errors": latest.get("errors", []) if latest else [],
                "usable_as_score_evidence": False,
            },
            "variants": [
                {
                    "variant_id": variant_id,
                    "description": description,
                    "status": "NOT_RUN",
                    "score": None,
                    "score_weight": None,
                    "abstention_fraction": None,
                }
                for variant_id, description in VARIANTS
            ],
            "gate_status": "BLOCKED_VARIANTS_NOT_RECORDED",
            "blocking_reason": "verifier pass/fail records do not expose independent-unit scores or score weights",
        }
        output["tasks"].append(item)
        (task / "quality/abstention_variant_plan.json").write_text(
            json.dumps(item, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )

    report = ROOT / "reports/abstention_variant_gate_2026-09-24.md"
    lines = [
        "# Abstention variant gate (2026-09-24)",
        "",
        "本报告严格区分 verifier 的 pass/fail baseline 和按独立判断单元计算的弃权分数。当前六道高风险题均未完成四种变体，因此不得把已有 `always_abstain` 失败记录解释为 blanket-abstain 分数低于门槛。",
        "",
        "| task | 独立示例单元 | 已有 always_abstain | 是否可作为分数证据 | 四变体 |",
        "|---|---:|---|---|---|",
    ]
    for item in output["tasks"]:
        baseline = item["existing_always_abstain_baseline"]
        lines.append(
            f"| `{item['task_id']}` | {item['evidence_surface']['independent_example_units']} | "
            f"`{baseline['status']}` ({baseline['failure_attribution'] or 'none'}) | 否 | `NOT_RUN` |"
        )
    lines += [
        "",
        "## 通过条件",
        "",
        "每道题必须提供四个变体的 score、score_weight 和 abstention_fraction；并证明：弃权比例不超过 30%，弃权分数权重不超过 25%，blanket-abstain 得分低于正确分析得分的 70%。如果无法定义独立判断单元或分数权重，应先缩窄题目，不得直接发布。",
        "",
        "逐题执行计划保存在各题的 `quality/abstention_variant_plan.json`。",
    ]
    report.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"tasks": len(output["tasks"]), "status": "BLOCKED_VARIANTS_NOT_RECORDED"}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
