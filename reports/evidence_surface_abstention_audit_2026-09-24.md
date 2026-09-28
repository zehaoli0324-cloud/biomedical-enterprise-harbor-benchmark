# Evidence Surface and Abstention Audit (2026-09-24)

对照《改题方案与检查标准 v1.0》§12.4、§12.7、§12.11。此报告是静态审计和已有 trial 记录汇总，不把合成 fixture 当作原始真实数据，也不把未执行的动态门禁算作通过。

## 结论

- 题目范围：Git 正式题包 **32** 道；当前工作树共 **46** 道，其中 **14** 道尚未纳入 Git，属于候选/实验题。以下静态表默认覆盖工作树全部题包，但正式发布统计应以 Git 正式题包为准。
- 原始数据/参考文献闭环：**未解决**。当前逐题证据映射为 10/46（正式题包为 6/32），但 `source_manifest.json`、`source_freeze_manifest.json` 和 `scientific_review.json` 仍未建立（计数：`{'claim_evidence_map.tsv': 10, 'source_manifest.json': 3, 'source_freeze_manifest.json': 0, 'scientific_review.json': 0}`）。
- 数据不足导致弃权的风险：**存在，且尚未被门禁排除**。发现 1 道题属于“输出项较多但可见数据规模很小”的高风险候选；这不是仅凭文件数判定题目错误，而是必须补做证据面映射和四种弃权变体。
- 已有 `always_abstain` 记录：`{'UNRECORDED': 8, 'verifier_fail': 26, 'fail': 11, 'NOT_RUN': 1}`。记录只有 pass/fail 状态，没有按科学判断单元的得分权重，因此不能证明 blanket-abstain 低于正确分析的 70%。
- 四种弃权变体门禁：6 道高风险题已有逐题计划，但当前执行数为 0；详见 `reports/abstention_variant_gate_2026-09-24.md`。

## 来源与参考文献门禁

| source_status | 题数 | 含义 |
|---|---:|---|
| `NO_AUTOMATED_DEFECT` | 2 | 仍需 source freeze / scientific review 才能发布 |
| `PLACEHOLDER_OR_MISSING` | 2 | 仍需 source freeze / scientific review 才能发布 |
| `PUBLIC_SOURCE_METADATA_ONLY_STAGING` | 1 | 仍需 source freeze / scientific review 才能发布 |
| `REVIEW_REQUIRED` | 25 | 仍需 source freeze / scientific review 才能发布 |
| `SYNTHETIC_CALIBRATION_REVIEW_REQUIRED` | 1 | 仍需 source freeze / scientific review 才能发布 |
| `SYNTHETIC_DISCLOSED` | 12 | 仍需 source freeze / scientific review 才能发布 |
| `UNREGISTERED` | 3 | 仍需 source freeze / scientific review 才能发布 |

明确的高风险来源题：`literature-screening-m1-001` 和 `research-workflow-stress-test-001` 的 `evidence_quality.json` 标记为 `PLACEHOLDER_OR_MISSING`，并报告 `PLACEHOLDER_DOI`；`crispr-resistance-e2e-001` 缺少 verifier 和 reference 文件。

## 弃权风险候选

以下仅按“可见 data 文件近似记录数 <= 7 且 required outputs >= 5”筛出待复核项；嵌套 JSON 的实际科学单元必须由题作者逐题确认：

`crispr-resistance-e2e-001`

其中已补映射：``；仍未能映射且已转为阻断修复卡：`crispr-resistance-e2e-001`。已映射题仍必须运行标准要求的四个变体：全部弃权、全部确定回答、一个正例回答+一个缺证据弃权、把正例改成错误弃权。当前仓库没有这些变体的逐题分数和权重记录。

## 逐题静态摘要

| task | source_status | fixture | data files | approx records | outputs | always_abstain | evidence_map | risk |
|---|---|---|---:|---:|---:|---|---|---|
| admiral-adsl-derivation-001 | NO_AUTOMATED_DEFECT | SYNTHETIC_FIXTURE | 3 | 13 | 5 | UNRECORDED | no | - |
| biogen-adme-audit-001 | NO_AUTOMATED_DEFECT | SYNTHETIC_FIXTURE | 1 | 8 | 3 | UNRECORDED | no | - |
| crispr-resistance-e2e-001 | UNREGISTERED | UNREGISTERED | 0 | 0 | 10 | UNRECORDED | no | many_outputs_small_visible_data,verifier_missing,reference_missing |
| eb001-split-leakage-001 | REVIEW_REQUIRED | SYNTHETIC_FIXTURE | 2 | 9 | 4 | verifier_fail | no | - |
| eb003-failure-recovery-003 | REVIEW_REQUIRED | SYNTHETIC_FIXTURE | 3 | 12 | 4 | verifier_fail | no | - |
| eb003-recovery-chain-005 | REVIEW_REQUIRED | SYNTHETIC_FIXTURE | 2 | 4 | 4 | verifier_fail | no | - |
| eb003-replay-provenance-004 | REVIEW_REQUIRED | SYNTHETIC_FIXTURE | 2 | 2 | 3 | verifier_fail | no | - |
| eb004-adtte-censoring-002 | REVIEW_REQUIRED | SYNTHETIC_FIXTURE | 4 | 14 | 4 | verifier_fail | no | - |
| eb005-batch-normalization-002 | REVIEW_REQUIRED | SYNTHETIC_FIXTURE | 3 | 36 | 4 | verifier_fail | no | - |
| eb005-normalization-hierarchy-003 | REVIEW_REQUIRED | SYNTHETIC_FIXTURE | 2 | 5 | 4 | verifier_fail | no | - |
| eb006-donor-stratified-signal-005 | SYNTHETIC_DISCLOSED | SYNTHETIC_DISCLOSED | 2 | 94 | 4 | fail | no | - |
| eb006-research-completion-006 | SYNTHETIC_DISCLOSED | SYNTHETIC_DISCLOSED | 3 | 101 | 4 | fail | no | - |
| eb006-research-completion-007 | UNREGISTERED | UNREGISTERED | 3 | 101 | 4 | UNRECORDED | no | - |
| eb006-research-completion-008 | SYNTHETIC_DISCLOSED | SYNTHETIC_DISCLOSED | 3 | 101 | 4 | fail | no | - |
| eb006-research-completion-009 | SYNTHETIC_DISCLOSED | SYNTHETIC_DISCLOSED | 4 | 283 | 4 | fail | no | - |
| eb006-research-completion-010 | SYNTHETIC_DISCLOSED | SYNTHETIC_DISCLOSED | 4 | 283 | 4 | fail | no | - |
| eb006-research-completion-011 | SYNTHETIC_DISCLOSED | SYNTHETIC_DISCLOSED | 4 | 283 | 4 | fail | yes | - |
| eb006-signal-noise-004 | REVIEW_REQUIRED | SYNTHETIC_FIXTURE | 2 | 5 | 3 | verifier_fail | no | - |
| eb008-route-portfolio-002 | REVIEW_REQUIRED | SYNTHETIC_FIXTURE | 2 | 4 | 4 | verifier_fail | no | - |
| eb008-stock-route-001 | REVIEW_REQUIRED | SYNTHETIC_FIXTURE | 5 | 51 | 4 | verifier_fail | no | - |
| eb009-diversity-coverage-004 | REVIEW_REQUIRED | SYNTHETIC_FIXTURE | 2 | 6 | 4 | verifier_fail | no | - |
| eb010-adaptive-policy-regret-005 | REVIEW_REQUIRED | SYNTHETIC_FIXTURE | 5 | 26 | 4 | verifier_fail | no | - |
| eb010-closed-loop-ambiguity-004 | REVIEW_REQUIRED | REVIEW_REQUIRED | 6 | 36 | 5 | verifier_fail | yes | - |
| eb010-closed-loop-replay-003 | REVIEW_REQUIRED | REVIEW_REQUIRED | 2 | 7 | 4 | verifier_fail | no | - |
| eb010-distributional-policy-stress-006 | REVIEW_REQUIRED | SYNTHETIC_FIXTURE | 5 | 40 | 5 | verifier_fail | yes | - |
| eb010-measurement-value-004 | REVIEW_REQUIRED | SYNTHETIC_FIXTURE | 2 | 7 | 3 | verifier_fail | no | - |
| eb010-next-batch-001 | REVIEW_REQUIRED | SYNTHETIC_FIXTURE | 4 | 19 | 4 | verifier_fail | no | - |
| eb010-next-batch-002 | REVIEW_REQUIRED | SYNTHETIC_FIXTURE | 2 | 9 | 4 | verifier_fail | no | - |
| eb010-stop-uncertainty-002 | REVIEW_REQUIRED | SYNTHETIC_FIXTURE | 4 | 14 | 5 | verifier_fail | yes | - |
| eb011-measurement-request-005 | REVIEW_REQUIRED | SYNTHETIC_FIXTURE | 2 | 5 | 4 | verifier_fail | no | - |
| eb011-reproduction-manifest-001 | REVIEW_REQUIRED | SYNTHETIC_FIXTURE | 4 | 14 | 5 | verifier_fail | yes | - |
| eb012-cross-handoff-audit-001 | REVIEW_REQUIRED | SYNTHETIC_FIXTURE | 2 | 3 | 4 | verifier_fail | no | - |
| eb012-cross-stage-chain-002 | REVIEW_REQUIRED | SYNTHETIC_FIXTURE | 2 | 20 | 4 | verifier_fail | no | - |
| eb012-revocation-portfolio-003 | REVIEW_REQUIRED | REVIEW_REQUIRED | 3 | 13 | 4 | verifier_fail | no | - |
| eb013-cross-context-evidence-portfolio-005 | SYNTHETIC_DISCLOSED | SYNTHETIC_FIXTURE | 4 | 30 | 6 | fail | yes | - |
| eb013-evidence-budget-routing-001 | SYNTHETIC_CALIBRATION_REVIEW_REQUIRED | SYNTHETIC_FIXTURE | 4 | 16 | 5 | verifier_fail | yes | - |
| eb013-evidence-budget-routing-002 | REVIEW_REQUIRED | SYNTHETIC_FIXTURE | 4 | 14 | 5 | verifier_fail | yes | - |
| eb013-observation-boundary-004 | SYNTHETIC_DISCLOSED | SYNTHETIC_FIXTURE | 5 | 26 | 4 | UNRECORDED | no | - |
| eb013-partial-observation-risk-004 | SYNTHETIC_DISCLOSED | SYNTHETIC_FIXTURE | 4 | 28 | 5 | fail | no | - |
| eb013-shared-setup-routing-003 | SYNTHETIC_DISCLOSED | SYNTHETIC_FIXTURE | 3 | 24 | 5 | fail | no | - |
| eb014-adaptive-evidence-ladder-003 | UNREGISTERED | UNREGISTERED | 7 | 62 | 7 | UNRECORDED | no | - |
| eb014-evidence-gap-followup-001 | SYNTHETIC_DISCLOSED | SYNTHETIC_DISCLOSED | 6 | 27 | 5 | fail | no | - |
| eb014-sequential-evidence-feedback-002 | SYNTHETIC_DISCLOSED | SYNTHETIC_HIDDEN_FEEDBACK_FIXTURE | 5 | 26 | 5 | fail | yes | - |
| eb015-real-source-replacement-gate-001 | PUBLIC_SOURCE_METADATA_ONLY_STAGING | PUBLIC_SOURCE_METADATA_ONLY_STAGING | 7 | 42 | 6 | NOT_RUN | yes | - |
| literature-screening-m1-001 | PLACEHOLDER_OR_MISSING | SYNTHETIC_FIXTURE | 2 | 9 | 5 | UNRECORDED | no | - |
| research-workflow-stress-test-001 | PLACEHOLDER_OR_MISSING | NOT_DECLARED | 6 | 23 | 9 | UNRECORDED | no | - |

## 判定

1. 问题 1 的答案是：**没有解决**。正式 Git 范围是 32 道，其中多数题明确是 synthetic/calibration fixture；这可以用于工程校准，但不等于有已核验的原始数据和参考文献。正式发布还缺来源冻结、逐文件 hash、许可/隐私审查和具名科学审阅。
2. 问题 2 的答案是：**风险存在，不能判定已解决**。已有基线中的 `always_abstain` 没有记录为通过，但这只说明提交未通过当前 verifier，不能替代按科学考察单元计算的弃权比例和 blanket-abstain 分数；尤其不能排除数据只支持少数判断、其余判断靠弃权的情况。

下一步必须是把剩余 36 道题补齐证据面矩阵，并对已映射题重新运行 verifier mutation、Docker 动态 oracle/nop 及四种弃权变体。
