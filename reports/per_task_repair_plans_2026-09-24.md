# Per-task repair plans (2026-09-24)

依据《改题方案与检查标准 v1.0》§12.4、§12.11、§12.12。此台账区分“证据面已映射”和“动态门禁已通过”；`NOT_RUN` 不等于通过。

| task | 当前状态 | 本次处理 | 仍需完成 |
|---|---|---|---|
| `eb010-closed-loop-ambiguity-004` | ready_for_calibration | 新增逐项证据映射；P-ALPHA/P-GAMMA 为正例，P-DELTA/P-ARCHIVE 为反例，P-BETA 为局部证据不足 | 四种弃权变体、mutation、Docker replay |
| `eb010-distributional-policy-stress-006` | ready_for_calibration | 映射 12 个 policy、6 个 scenario、5 个 profile 及 CVaR/budget 控制参数；禁止因少数 policy 无效而整体弃权 | 四种弃权变体、profile/branch 覆盖 trial |
| `eb010-stop-uncertainty-002` | ready_for_calibration | 映射全部 stage1/stage2 请求；仅 S-POST 标记 future-outcome 缺证据 | 四种弃权变体、路由 oracle replay |
| `eb011-reproduction-manifest-001` | ready_for_calibration | 映射 manifest drift 和 remediation 分支；仅 D-POST 标记 future-outcome 缺证据 | 四种弃权变体、路由 oracle replay |
| `eb013-evidence-budget-routing-001` | ready_for_calibration | 映射 3 个 uncertainty、支持请求和 R-POST/R-INCOMPLETE 局部阻断 | 四种弃权变体、预算/依赖 mutation |
| `eb013-evidence-budget-routing-002` | ready_for_calibration | 映射 stage1/stage2 全部请求；仅 R-POST 允许设计内弃权 | 四种弃权变体、路由 oracle replay |
| `crispr-resistance-e2e-001` | contract_only | 新增阻断修复卡和 evidence-surface 卡；明确 data、verifier、reference 均未物化，保持 HOLD | 物化许可数据和 source freeze；或缩窄为契约审查题后再试跑 |
| `literature-screening-m1-001` | calibration_only | 新增 placeholder DOI 修复卡；明确不得当作真实文献闭环 | 替换可解析来源、source manifest、科学审阅、claim map |
| `research-workflow-stress-test-001` | calibration_only | 新增来源分类和 placeholder DOI 修复卡 | 声明 fixture 或替换来源、source manifest、科学审阅、claim map |

## 统一动态门禁

六道可运行规划题的 `quality/claim_evidence_map.tsv` 和 `quality/abstention_variant_plan.json` 已落盘，但其 evidence-surface card 仍为 `variant_status: BLOCKED_VARIANTS_NOT_RECORDED`。正式发布前必须记录：全部弃权、全部确定回答、一个正例回答+一个证据不足弃权、把正例改成错误弃权，并按独立判断单元计算弃权比例、得分权重和 blanket-abstain 分数。

来源闭环仍未完成：仓库尚未为全部题目建立逐文件 `source_manifest.json`、冻结 hash 和具名 `scientific_review.json`。因此本台账不把 synthetic fixture 或本次静态映射误报为“已有恰当原始数据和参考文献”。
