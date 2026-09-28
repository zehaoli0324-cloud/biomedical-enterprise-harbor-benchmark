# gpt-5.6-sol Trial Status (2026-09-28)

## Scope and execution boundary

本轮严格使用现有题包，不修改题面、数据或 verifier 来迎合模型输出。执行模型为 `gpt-5.6-sol`，输出保存在现有本地根目录 `/private/tmp/benchmark-runs-gpt56sol/` 下。当前 Docker/Harbor 不可用，因此所有结果均为本地 `process_cwd_only` calibration evidence，不替代 fixed-container、held-out 或 practitioner release gates。

## Conditions-insufficient queue

以下题目本轮不重复跑模型，原因是缺少的不是 target model 输出，而是发布或复核条件：

| task | 当前状态 | 暂缓原因 |
|---|---|---|
| `eb015-real-source-replacement-gate-001` | `PASS_AFTER_CONTRACT_REPLAY` | source rights、file-level SHA-256 freeze、verifier rebind、fixed-container replay、practitioner review |
| `eb006-research-completion-011` | `TIMEOUT_OUTPUT_COMPLETE_SCIENCE_PASS` | 需要 clean rerun、target infrastructure、fixed-container、real-data replacement、practitioner review；先处理身份/入口一致性 |
| `eb013-cross-context-evidence-portfolio-005` | `RAW_PASS` | fixed-container、held-out target、practitioner review |
| `eb014-sequential-evidence-feedback-002` | `RAW_PASS` | trajectory analysis、fixed-container、practitioner review |
| `eb010-adaptive-policy-regret-005` | `PASS` | fixed-container、practitioner review |
| `eb010-closed-loop-replay-003` | `PASS_AFTER_CONTRACT_REPLAY` | fixed-container、practitioner review |
| `eb013-partial-observation-risk-004` | `PASS` | fixed-container、held-out target、practitioner review |
| `eb013-shared-setup-routing-003` | `PASS` | fixed-container、held-out target、practitioner review |
| `eb006-donor-stratified-signal-005` | `RAW_PASS` | fixed-container、held-out difficulty、independent practitioner、license/privacy/claim review |
| `eb006-research-completion-008` | `RAW_PASS` | fixed-container、practitioner review、real-data replacement |

这些题不做本轮重复 trial；补齐上述条件后再执行对应 gate。

## Trial results

| task | runner result | model observation | classification |
|---|---|---|---|
| `eb013-evidence-budget-routing-001` | repaired trial `pass` | 选出 `R-ASSAY + R-ORTHO`，cost `5.0`；修复后结构化产物、派生 reductions、provenance 和 audit 关键词均通过 | `RAW_PASS`，仅待 fixed-container/practitioner |
| `eb013-evidence-budget-routing-002` | `verifier_fail`, 4 errors | 选出 `R-ADAPTIVE` 及三路 stage-2 policy，worst residual `0.25`、cost `5.0`；policy/TSV/provenance 序列化不匹配 | `scientific_or_delivery_fail_pending_triage` |
| `eb010-closed-loop-ambiguity-004` | `verifier_fail`, 1 error | 生成五份产物，选出 `P-OMICRON`，cost `6.5`；仅 `P-TAU blocker reasons` 不匹配 | `scientific_or_delivery_fail_pending_triage` |
| `eb010-distributional-policy-stress-006` | `verifier_fail`, 458 errors | 生成五份产物并选出 `P-LOWCOST`；政策、branch、profile 指标与 oracle 大范围不匹配 | `scientific_or_delivery_fail_pending_triage` |

每道题的原始 verifier 结果、运行 manifest、产物 SHA-256、文字分析和质量卡均已写入对应 `benchmarks/<task>/quality/`。完整原始产物仍保留在上表所用的外部 trial 目录。

## Next actions

1. 对四道失败题先做 unchanged-artifact replay，区分表示/合同问题与科学计算错误；不直接改 verifier。
2. EB013 两题优先核对 output contract、派生 reduction、route TSV 和 provenance hash；已有修复合同与回归测试保持在题包中。
3. EB010 ambiguity 先核对 `P-TAU` blocker oracle；distributional 先核对 scenario/profile join 和 branch utility，再判断是否需要模型重跑。
4. Docker/Harbor 恢复后，对所有要进入发布候选的题执行 fixed-container replay、hash capture、解包 diff 和 practitioner review。

本轮高质量 trial bundle 已生成：`dist/high-quality-gpt56sol-trials-20260928.tar.gz`，SHA-256 记录在同名 `.sha256` 文件；bundle 详情见 `reports/high_quality_trial_bundle_20260928.md`。
