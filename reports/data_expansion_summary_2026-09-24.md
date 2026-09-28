# Data expansion summary (2026-09-24)

本轮目标是增加模型可直接回答的正例、反例和边界例；新增记录均进入现有 verifier 的 `expected()` 计算，不是旁路注释数据。六道题的旧 trial 结果因此全部需要重新校准。

| task | 扩充前主要单元 | 扩充后主要单元 | 新增覆盖 |
|---|---:|---:|---|
| `eb010-closed-loop-ambiguity-004` | 5 records | 13 records / 3 eligible | clear proceed、low signal、budget、future outcome、archived、ambiguous/replay instability |
| `eb010-distributional-policy-stress-006` | 12 policies | 20 policies / 10 eligible | 10 valid policies + future/incomplete/archived/unknown/unlisted/budget negatives |
| `eb010-stop-uncertainty-002` | 5 derived policies | 6 derived policies / 4 eligible | 新增 context clear/conflict 观测及条件 follow-up |
| `eb011-reproduction-manifest-001` | 5 derived policies | 6 derived policies / 2 eligible | 新增 environment match/conflict 观测及 remediation |
| `eb013-evidence-budget-routing-001` | 7 requests | 9 requests / 2 included | 新增 reproducibility cross-check 和 orthogonal confirmation |
| `eb013-evidence-budget-routing-002` | 3 derived policies | 4 derived policies / 1 eligible | 新增 context clear/conflict 观测及条件 follow-up |

## 结果

- 六道题的 verifier 单测：`28 passed`。
- 作者侧 controls 已按新数据重跑：闭环歧义、分布策略、证据预算路由均为 `CALIBRATED`；stop/reproduction 两题的新分支保持原最优路由，相关 verifier 测试通过。
- 递归数据审计后，“输出多但可见数据少”的候选从 7 道降为 1 道；剩余的是没有物化数据和 verifier 的 `crispr-resistance-e2e-001`。
- 六道题的 `task.yaml` 已升版本并标记 `DATA_EXPANDED_RECALIBRATION_REQUIRED`；旧模型 trial 结果已加 `SUPERSEDES_PREVIOUS_TRIAL` 标记，不能直接沿用。

## 尚未完成

这不是 source closure，也不是 target trial 通过。新增数据仍是本地 synthetic fixture；仍需重新生成 reference、运行模型校准和四种弃权变体，并为正式发布补齐 source manifest、冻结 hash 和科学审阅。
