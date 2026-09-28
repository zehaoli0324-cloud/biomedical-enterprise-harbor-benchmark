# EB010 题目优化审计（2026-09-28）

## 本轮范围

本轮只处理 `eb010-closed-loop-ambiguity-004` v0.8.0，不改变 verifier 的任务契约或放行条件。扩充数据集 `data-expanded-20260924-v2` 已重新执行控制校准和作者基线：控制校准 `CALIBRATED`，参考基线通过，目标模型仍未运行。

## 独立单元与权重

- 来源：`quality/claim_evidence_map.tsv`
- 独立判断单元：21 个；控制参数单元：5 个（不计入行为得分）
- 每个独立单元等权：`1/21 = 0.047619`
- 预期动作：`POSITIVE_OBSERVABLE` 和 `NEGATIVE_OBSERVABLE` 为 `definite`；`INSUFFICIENT_BY_DESIGN` 为 `abstain`
- 评分只衡量独立单元动作是否正确，不替代任务 verifier 的全量产物校验

## 四种拒答变体

| 变体 | 得分 | 弃权比例 | 弃权权重 | 结果 |
|---|---:|---:|---:|---|
| `all_abstain` | 0.190476 | 1.000000 | 1.000000 | 仅作 blanket-abstain 对照，不满足弃权比例上限 |
| `all_definite` | 0.809524 | 0.000000 | 0.000000 | 通过对照 |
| `positive_plus_insufficient_abstain` | 1.000000 | 0.190476 | 0.190476 | 参考策略通过 |
| `positive_as_wrong_abstain` | 0.952381 | 0.238095 | 0.238095 | 正例覆盖损失可观测，仍在上限内 |

门槛检查全部通过：非 blanket 变体的弃权比例不超过 0.30，弃权权重不超过 0.25；blanket-abstain 得分为参考策略的 19.05%，低于 70%。机器可读结果见 `benchmarks/eb010-closed-loop-ambiguity-004/quality/abstention_variant_results.json`。

## 当前结论

题目已完成数据扩充、控制校准、作者基线和独立单元拒答评分。仍不可发布：固定容器复跑、目标模型新版本校准、专业人员复核尚未完成；不得把本轮质量审计结果写成目标模型已通过。

## 下一步

1. 在固定容器中运行 v0.8.0 目标模型试验并保存完整输出与版本指纹。
2. 用同一 21 单元权重重算目标模型的动作得分和弃权比例。
3. 目标模型与专业人员复核均通过后，再更新 release gate；否则保留 `BLOCKED`。
