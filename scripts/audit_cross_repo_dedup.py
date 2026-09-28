#!/usr/bin/env python3
"""Static cross-repository task overlap audit.

This is a triage report, not a scientific equivalence proof. It compares the
32 Git-tracked task packages in this repository with task packages found in
related local repositories.
"""

from __future__ import annotations

import hashlib
import json
import re
from difflib import SequenceMatcher
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "reports/cross_repo_dedup_audit_2026-09-24.md"
JSON_REPORT = ROOT / "reports/cross_repo_dedup_audit_2026-09-24.json"
EXTERNAL_ROOTS = [
    Path("/Users/zehaoli0324/harbor-science-bench-factory"),
    Path("/Users/zehaoli0324/research-benchmark"),
    Path("/Users/zehaoli0324/skill-scenario-to-benchmark"),
    Path("/Users/zehaoli0324/work/BioBenchFactory"),
]
TOKEN_RE = re.compile(r"[a-z0-9][a-z0-9_-]+|[\u4e00-\u9fff]+")
STOPWORDS = {
    "task", "task_id", "version", "status", "title", "domain", "data", "outputs",
    "required", "path", "format", "json", "yaml", "toml", "the", "and", "with",
    "from", "for", "that", "this", "only", "must", "true", "false", "not",
}


def tracked_task_paths() -> list[Path]:
    import subprocess

    result = subprocess.run(
        ["git", "ls-files", "benchmarks/*/task.yaml"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    return [ROOT / item for item in result.stdout.splitlines() if item]


def normalize_id(value: str) -> str:
    value = value.lower().strip()
    value = re.sub(r"[-_](?:v?\d+(?:\.\d+){1,3})(?:[-_].*)?$", "", value)
    value = re.sub(r"[-_]reviewed$", "", value)
    return value


def parse_field(text: str, field: str) -> str:
    patterns = [
        rf"^\s*{re.escape(field)}\s*:\s*[\"']?([^\"'\n]+)",
        rf"^\s*{re.escape(field)}\s*=\s*[\"']([^\"']+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.MULTILINE)
        if match:
            return match.group(1).strip()
    return ""


def package_text(task_file: Path) -> str:
    package = task_file.parent
    parts = [task_file]
    for name in ("instruction.md", "README.md", "scenario-card.yaml"):
        candidate = package / name
        if candidate.is_file():
            parts.append(candidate)
    chunks = []
    for path in parts:
        try:
            chunks.append(path.read_text(encoding="utf-8", errors="replace")[:40_000])
        except OSError:
            pass
    return "\n".join(chunks)


def tokens(text: str) -> set[str]:
    return {token for token in TOKEN_RE.findall(text.lower()) if token not in STOPWORDS and len(token) > 1}


def record(task_file: Path, repo: str, tracked: bool) -> dict:
    text = package_text(task_file)
    task_id = parse_field(text, "id") or task_file.parent.name
    title = parse_field(text, "title")
    token_set = tokens(text)
    normalized = " ".join(sorted(token_set))
    return {
        "repo": repo,
        "tracked": tracked,
        "path": str(task_file),
        "task_id": task_id,
        "normalized_id": normalize_id(task_id),
        "title": title,
        "normalized_title": " ".join(tokens(title)),
        "tokens": token_set,
        "fingerprint": hashlib.sha256(normalized.encode()).hexdigest(),
        "text": text,
    }


def external_tasks() -> list[dict]:
    rows = []
    for repo_root in EXTERNAL_ROOTS:
        if not repo_root.is_dir():
            continue
        seen = set()
        for path in sorted(repo_root.rglob("*")):
            if path.is_dir() or ".git" in path.parts or path.name not in {"task.yaml", "task.toml"}:
                continue
            package = path.parent.resolve()
            if package in seen:
                continue
            seen.add(package)
            rows.append(record(path, repo_root.name, False))
    return rows


def compare(left: dict, right: dict) -> dict:
    intersection = len(left["tokens"] & right["tokens"])
    union = len(left["tokens"] | right["tokens"]) or 1
    jaccard = intersection / union
    title_ratio = SequenceMatcher(None, left["normalized_title"], right["normalized_title"]).ratio()
    id_match = left["normalized_id"] == right["normalized_id"]
    title_match = bool(left["normalized_title"]) and left["normalized_title"] == right["normalized_title"]
    score = 0.55 * title_ratio + 0.45 * jaccard
    if id_match:
        classification = "SAME_LINEAGE_ID_MATCH"
    elif title_match or score >= 0.92:
        classification = "DIRECT_DUPLICATE_CANDIDATE"
    elif score >= 0.65:
        classification = "HIGH_OVERLAP_REVIEW"
    elif score >= 0.40:
        classification = "SHARED_PATTERN_ONLY"
    else:
        classification = "LOW_OVERLAP"
    return {
        "current_task": left["task_id"],
        "external_repo": right["repo"],
        "external_task": right["task_id"],
        "current_path": left["path"],
        "external_path": right["path"],
        "title_ratio": round(title_ratio, 4),
        "token_jaccard": round(jaccard, 4),
        "score": round(score, 4),
        "classification": classification,
    }


def main() -> int:
    current = [record(path, ROOT.name, True) for path in tracked_task_paths()]
    external = external_tasks()
    comparisons = [compare(left, right) for left in current for right in external]
    comparisons.sort(key=lambda row: (-row["score"], row["current_task"], row["external_repo"], row["external_task"]))
    top_by_task = {}
    for row in comparisons:
        top_by_task.setdefault(row["current_task"], []).append(row)
    selected = []
    for task_id, rows in top_by_task.items():
        # Keep the generic semantic leaderboard readable; same-lineage rows
        # are reported separately after version/repository grouping.
        non_lineage = [row for row in rows if row["classification"] != "SAME_LINEAGE_ID_MATCH"]
        selected.extend(non_lineage[:5])
    selected.sort(key=lambda row: (-row["score"], row["current_task"], row["external_repo"], row["external_task"]))
    counts = {}
    for row in comparisons:
        counts[row["classification"]] = counts.get(row["classification"], 0) + 1
    lineage_groups = {}
    for row in comparisons:
        if row["classification"] != "SAME_LINEAGE_ID_MATCH":
            continue
        key = (row["current_task"], row["external_repo"])
        group = lineage_groups.setdefault(key, {
            "current_task": row["current_task"],
            "external_repo": row["external_repo"],
            "external_task_variants": [],
            "external_paths": [],
            "max_score": 0.0,
            "best_external_task": row["external_task"],
            "best_external_path": row["external_path"],
            "title_ratio": row["title_ratio"],
            "token_jaccard": row["token_jaccard"],
        })
        if row["external_task"] not in group["external_task_variants"]:
            group["external_task_variants"].append(row["external_task"])
        if row["external_path"] not in group["external_paths"]:
            group["external_paths"].append(row["external_path"])
        if row["score"] > group["max_score"]:
            group.update({
                "max_score": row["score"],
                "best_external_task": row["external_task"],
                "best_external_path": row["external_path"],
                "title_ratio": row["title_ratio"],
                "token_jaccard": row["token_jaccard"],
            })
    lineage_groups = sorted(
        lineage_groups.values(),
        key=lambda row: (-row["max_score"], row["current_task"], row["external_repo"]),
    )
    for group in lineage_groups:
        group["external_package_count"] = len(group["external_paths"])
        group["classification"] = "SAME_LINEAGE_REVIEW"
    direct = [
        group for group in lineage_groups if group["max_score"] >= 0.65
    ]
    high = [row for row in comparisons if row["classification"] == "HIGH_OVERLAP_REVIEW"]
    payload = {
        "schema_version": "cross_repo_dedup_audit.v2",
        "generated_on": "2026-09-24",
        "current_repository": str(ROOT),
        "current_tracked_task_count": len(current),
        "external_repository_count": len({row["repo"] for row in external}),
        "external_task_package_count": len(external),
        "external_roots": [str(path) for path in EXTERNAL_ROOTS if path.is_dir()],
        "classification_counts": counts,
        "same_lineage_groups": lineage_groups,
        "direct_duplicate_groups": direct,
        "direct_duplicate_candidate_count": len(direct),
        "high_overlap_review_count": len(high),
        "high_overlap_review": high,
        "top_matches_per_current_task": selected,
        "limitations": [
            "static comparison of task metadata and visible task text only",
            "does not prove scientific equivalence or compare hidden reference truth",
            "versioned copies in the same lineage are reported as overlap candidates",
            "external repositories were read from local working trees; no network refresh was performed",
        ],
    }
    JSON_REPORT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lines = [
        "# Cross-repository deduplication audit (2026-09-24)",
        "",
        "这是静态题目重合审计，不是科学等价性证明。当前仓库只按 Git 跟踪的正式题包统计；工作树候选题不混入正式题数。",
        "",
        f"- 当前仓库正式题包：**{len(current)}**",
        f"- 扫描外部本地仓库：**{len({row['repo'] for row in external})}**",
        f"- 外部 task package：**{len(external)}**",
        f"- 同一规范化 ID 的题族仓库组合：**{len(lineage_groups)}**",
        f"- 直接重复/同一题族待复核组合：**{len(direct)}**",
        f"- 高重合待人工复核：**{len(high)}**",
        "",
        "## 扫描仓库",
        "",
    ]
    for path in EXTERNAL_ROOTS:
        if path.is_dir():
            lines.append(f"- `{path}`")
    lines += [
        "",
        "## 同一题族/直接重复候选（按仓库归并）",
        "",
        "| 当前题目 | 外部仓库 | 外部版本/路径数 | 最佳外部题目 | 最高 score | 判定 |",
        "|---|---|---:|---|---:|---|",
    ]
    for row in direct[:100]:
        lines.append(f"| `{row['current_task']}` | `{row['external_repo']}` | {row['external_package_count']} | `{row['best_external_task']}` | {row['max_score']:.4f} | `{row['classification']}` |")
    if not direct:
        lines.append("| - | - | - | none detected | - | - |")
    lines += [
        "",
        "同一规范化 ID 但文本相似度不足 0.65 的组合仍保留在 JSON 的 `same_lineage_groups`，需要确认是否只是旧版本或残留副本。",
    ]
    lines += [
        "",
        "## 每道正式题最高重合项",
        "",
        "| 当前题目 | 外部仓库 | 外部题目 | 判定 | score |",
        "|---|---|---|---|---:|",
    ]
    for row in selected:
        lines.append(f"| `{row['current_task']}` | `{row['external_repo']}` | `{row['external_task']}` | `{row['classification']}` | {row['score']:.4f} |")
    lines += [
        "",
        "## 判读规则与限制",
        "",
        "- `SAME_LINEAGE_ID_MATCH`：规范化 task id 相同，先视为同一题族；报告按外部仓库归并版本副本。",
        "- `DIRECT_DUPLICATE_CANDIDATE`：题目标题或综合文本高度一致，需要人工确认是否同一题的版本迁移。",
        "- `HIGH_OVERLAP_REVIEW`：语义和结构高度接近，但不能仅凭静态文本判定重复。",
        "- `SHARED_PATTERN_ONLY`：可能共享 workflow、失败模式或设计模块，不计作重复题。",
        "- 同名题若是同一题的不同仓库版本，应保留 lineage、版本、来源和 reference 差异记录；不能把它们当作独立题累计数量。",
        "- 本报告没有访问网络，也没有比较隐藏 verifier/reference truth；正式去重决定仍需人工科学审阅。",
        "",
        f"原始比较分类计数：`{counts}`",
    ]
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"current_tasks": len(current), "external_tasks": len(external), "lineage_groups": len(lineage_groups), "direct_groups": len(direct), "high_overlap": len(high), "report": str(REPORT)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
