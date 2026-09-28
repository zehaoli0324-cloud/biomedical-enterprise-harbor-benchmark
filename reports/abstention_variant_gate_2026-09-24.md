# Abstention variant gate (2026-09-24)

本报告严格区分 verifier 的 pass/fail baseline 和按独立判断单元计算的弃权分数。当前六道高风险题均未完成四种变体，因此不得把已有 `always_abstain` 失败记录解释为 blanket-abstain 分数低于门槛。

| task | 独立示例单元 | 已有 always_abstain | 是否可作为分数证据 | 四变体 |
|---|---:|---|---|---|
| `eb010-closed-loop-ambiguity-004` | 21 | `verifier_fail` (artifact_completeness) | 否 | `NOT_RUN` |
| `eb010-distributional-policy-stress-006` | 32 | `verifier_fail` (artifact_completeness) | 否 | `NOT_RUN` |
| `eb010-stop-uncertainty-002` | 10 | `verifier_fail` (method_choice) | 否 | `NOT_RUN` |
| `eb011-reproduction-manifest-001` | 10 | `verifier_fail` (method_choice) | 否 | `NOT_RUN` |
| `eb013-evidence-budget-routing-001` | 11 | `verifier_fail` (method_choice) | 否 | `NOT_RUN` |
| `eb013-evidence-budget-routing-002` | 10 | `verifier_fail` (method_choice) | 否 | `NOT_RUN` |

## 通过条件

每道题必须提供四个变体的 score、score_weight 和 abstention_fraction；并证明：弃权比例不超过 30%，弃权分数权重不超过 25%，blanket-abstain 得分低于正确分析得分的 70%。如果无法定义独立判断单元或分数权重，应先缩窄题目，不得直接发布。

逐题执行计划保存在各题的 `quality/abstention_variant_plan.json`。
