# Enterprise Benchmark Difficulty Escalation v1

## 目标

把难度从“多字段校验”提升为可审计的多层科学决策。每次升级只引入一个主难度轴，最多叠加两个辅助轴，保证失败可以归因到具体能力，而不是把数据、规则和输出格式同时变复杂。

所有版本继续遵守四条约束：

- 结论必须由 agent-visible 的规则、数据和 provenance 推导，不能依赖隐藏答案标签。
- 最终选择与每个 blocker 都要能回溯到输入记录、规则和中间计算。
- 计算完成不等于生物学、化学或实验事实成立；claim boundary 必须进入输出。
- 每一级必须有 positive、negative、invariance、insufficient-evidence 和 adversarial control。

## 难度轴

| 轴 | L1 | L2 | L3 | L4 | L5 |
|---|---|---|---|---|---|
| 数据结构 | 平面表 | 多表 join | 证据图/事件图 | 多时间点状态 | 多主体、多实验单元 |
| 规则交互 | 单 blocker | 多 blocker | blocker 优先级/冲突 | 条件规则和状态转移 | 约束策略或政策树 |
| 不确定性 | 缺失值 | 情景 | 区间/敏感性 | 分布漂移 | 观测后更新 |
| 时间维度 | 静态快照 | 版本/截止日 | 顺序事件 | 多阶段决策 | 自适应闭环 |
| provenance | 输入 hash | 来源状态 | 独立性/quorum | 复现链 | 版本回溯与撤回 |
| 科学判断 | 可行/不可行 | 保留表型 | 证据冲突 | 停止/升级 | 资源与 claim 联合优化 |
| 审计输出 | 最终结果 | blocker 列表 | 每分支理由 | 事件日志 | 决策树/策略证明 |

## 版本阶梯

### L0：合同完整性

适用于当前 v0.3 的基线。验证 schema、join、hash、确定性、所有候选覆盖和最小 claim boundary。目标是消除“漏交付”和“抄答案”，不主张高科学难度。

### L1：独立证据门槛

加入一个明确的证据完整性 blocker，例如最小重复数、来源 quorum、必需 provenance。缺证据只能 `hold`，不能通过高分或默认值补齐。

### L2：交互门槛

至少两个局部指标同时满足才可 eligible，并要求报告 blocker 优先级。例如总体效果保留但一个批次方向反转，或者库存足够但证据来源不独立。Verifier 必须逐条件重算，不能只比最终选择。

### L3：冲突与敏感性

引入相互冲突的证据或多个合理 profile，并要求 leave-one-out、leave-one-batch-out、来源撤回或参数扰动后的稳定性报告。结论分为 `stable`、`sensitive`、`hold`，不能把最优单点当作稳健结论。

### L4：多阶段状态机

把任务变成两到三步决策：第一阶段的结果决定第二阶段允许的动作、预算或 claim 权限。必须校验事件顺序、状态转移、幂等性、重放结果和阶段间 provenance 传递。

### L5：鲁棒策略与自适应闭环

决策对象从单个候选升级为策略或决策树。要求在多个情景、预算、失败概率和信息价值下优化；观察结果只能在声明的时间点更新，禁止未来 outcome 泄漏。最终输出应包含策略、停止规则、最坏情景和人工升级条件。

## 四题升级路线

### EB003：failure recovery

**v0.4：claim-permission lattice**

- 将 claim 拆为 operational、descriptive、associational、causal 四级权限。
- 每个 fallback 除 invariants/provenance 外，带有可继承的 claim 权限；参数漂移、参考版本变化、输入 digest 缺失分别降低不同权限。
- 增加 provenance conflict 分支：两个来源都存在但互相矛盾，状态为 `provenance_conflict`，不得降级成普通 drift。
- 输出增加 `claim_permissions_before/after`、`downgrade_reason` 和逐分支审计。

**v0.5：retry budget and ordered events**

- 增加 retry budget、timeout budget 和不可逆副作用标记。
- 事件日志必须是可重放的状态机：`failed -> eligible -> retried -> selected/held`。
- 同一 branch 重放不得产生第二次资源消耗或改变选择；乱序、重复、跳状态都失败。

**v0.6：multi-endpoint recovery**

- 同时维护主要 estimand、次要 estimand 和安全性输出；不同 fallback 可能只保留部分 endpoint。
- 选择依据变为“最大 claim 保留度”，但任何 causal claim 都需要独立验证门槛。
- 加入 endpoint-specific abstention，避免一个成功 endpoint 解锁全部结论。

### EB005：batch normalization

**v0.4：experimental-unit hierarchy**

- 数据层级扩展为 donor、plate、well、site；明确独立实验单元，禁止把 well 当作独立 donor。
- metadata 加入 donor/site/batch 交叉结构与缺失机制 `MCAR/MAR/unknown`。
- verifier 计算 donor-level contrast、plate-level dispersion 和 design rank；rank 不足时整体 hold。

**v0.5：sensitivity-qualified normalization**

- 每个 profile 必须通过 leave-one-batch-out 和 control-subset sensitivity。
- 输出 `stable_batches`、`sensitivity_range`、`phenotype_sign_consistency`；任一关键批次移除后改变推荐则只能 `sensitive`。
- 增加“均值变好但方差/尾部恶化”的 normalization，阻止单一 control-range 指标获胜。

**v0.6：uncertainty-aware correction**

- 为控制均值、效应保留率和方向一致性加入 bootstrap 或声明的区间规则。
- eligibility 由点估计改为区间门槛，例如 retention 下界和 batch-range 上界。
- 区分 `eligible`、`eligible_but_uncertain`、`hold_for_replication`，并要求报告最小追加实验。

### EB008：stock and route

**v0.4：shared inventory allocation**

- 一个 lot 可被多个 route 竞争；库存判定从 route-local sufficiency 升级为全局分配问题。
- 每个 route 输出消耗、剩余量、保留量和 allocation witness；不能同时把同一物料分配给冲突路线。
- 增加 lot reservation race 和决策截止时间，验证过期与并发状态。

**v0.5：evidence graph with retraction time**

- source 不再只有 current/retracted，而是带 effective interval、supersedes、independence group 和 conflict edge。
- quorum 按 step、来源独立性和目标 scope 计算；同一证据链的派生记录不能重复计数。
- 对“当前有效但已被后续来源否定”的记录输出 `temporally_conflicted`，不能静默排除。

**v0.6：route portfolio and approval policy**

- 选择一个 route portfolio，而不是单一路线；共享库存、危险组合、人工 review capacity 都成为约束。
- route score 只作排序，不能越过 safety gate；任何 unresolved chemistry 触发 human approval。
- 输出 route-level 和 portfolio-level blocker，禁止用一条可行路线掩盖另一条高风险路线。

### EB010：next batch

**v0.4：two-stage acquisition**

- 第一批候选结果不提供未来 outcome，只提供声明格式的 observation state。
- 第二阶段候选可用集合由第一阶段的 observed state 和预算剩余量决定。
- verifier 检查阶段顺序、预算消耗、不可提前使用的字段和 stop/continue 决策。

**v0.5：distributionally robust selection**

- 情景权重不再固定为可信真值；使用权重区间或 ambiguity set。
- 目标加入 worst-case、CVaR 或 regret，并要求同时输出 nominal、worst-case 和 sensitivity ranking。
- 任何只优化 mean 的 batch、忽略 correlation 或超预算的 batch 必须能被 negative control 捕获。

**v0.6：adaptive policy tree**

- 输出不再是一个 batch，而是 `if observation in region -> next action` 的策略树。
- 每个叶节点带剩余预算、停止条件、claim boundary 和人工升级条件。
- 控制样例应包含相同首批但不同第二阶段策略、过早停止、未来 outcome 泄漏和策略树不闭合。

## 跨题组合难度

当单题达到 L3 后，再引入跨题组合；不要在单题未稳定前直接组合。

1. **Recovery -> normalization**：EB003 的 fallback 版本决定 EB005 可使用的 reference/profile；验证 provenance 传递和 claim 权限同步。
2. **Normalization -> next batch**：EB005 的不确定性区间进入 EB010 acquisition；不能把校正后的点估计伪装成已验证 outcome。
3. **Route -> next batch**：EB008 的 inventory allocation 约束 EB010 的 material budget；验证跨任务单位、截止时间和 hash 一致。
4. **全链路**：失败恢复、数据校正、路线可行性和批次设计各自产生一个带权限的 artifact，最终策略必须引用四者的版本和 blocker，而非只引用最终推荐。

## 控制与发布门槛

每个新版本至少需要：

- `positive`：标准解完整通过；
- `negative`：只改变一个关键科学条件就失败；
- `invariance`：行序、来源顺序、候选排序改变不改变语义结果；
- `insufficient_evidence`：缺证据时 hold，不生成默认 winner；
- `adversarial`：高分、漂亮总体指标、旧来源或 future outcome 诱导均被拒绝；
- `metamorphic`：重复、重放、撤回、时间平移和等价字段映射的结果符合声明性质。

建议发布条件：

1. 关键路径至少有两组独立 positive fixture；
2. 每个 blocker 都有单因素 negative control；
3. baseline matrix 能区分 scientific judgment、delivery failure 和 shortcut；
4. verifier 不读取 `verifier_only` 以外的隐藏真值，也不依赖候选名称；
5. 目标模型试验与合同版本一致；合同变更后旧试验只能标记为历史证据，不能充当当前版本校准；
6. 审计记录能回答“哪个输入、哪条规则、哪个中间值导致了该结论”。

## 推荐实施顺序

下一轮先做 EB003 v0.4、EB005 v0.4、EB008 v0.4、EB010 v0.4，分别只引入 claim lattice、实验单元层级、共享库存分配、两阶段 acquisition 这四个主轴。四题 v0.4 全部通过控制校准后，再并行推进 v0.5 的敏感性/鲁棒性层；跨题组合放到四题至少达到 v0.5 后。

## L5 首个物化任务

`eb010-closed-loop-replay-003` 是首个 L5 package。它把静态 next-batch 选择升级为 policy replay：每个 policy 必须经过 `observe -> act -> stop_or_continue`，并同时通过预算、未来 outcome 防泄漏、至少两个 seed 和最大 utility spread 门槛。verifier 逐 policy 校验 eligibility、逐 replay 校验覆盖，并在无 eligible policy 时返回 `request_information`。

该题的 controls 位于 `scripts/run_l5_controls.py`，author-side 状态为 `CALIBRATED`；`gpt-5.6-sol` 已完成一次本地 process trial，初始 verifier schema 缺陷经未改动 artifact contract replay 后通过。固定容器 replay 和 practitioner review 仍是 release blockers。

## L5.1 低披露与语义含糊

`eb010-closed-loop-ambiguity-004` 不再在 instruction 中逐字段解释输入。agent 必须递归发现嵌套 JSON、读取 discovery manifest、重建 semantic lexicon 与 policy record 的连接，并记录所有输入 hash。策略文本同时包含明确 proceed、显式 review、未来 outcome、archived scope 和 proceed/review 冲突等记录；冲突必须输出 `human_review`，高 utility 不能越过语义 blocker。

该题把难度增加在环境、语意和 agent-planned workflow 层，而不是隐藏答案：规则仍在 agent-visible 输入中，但 agent 必须发现 mission 的 required capabilities，自行从包含诱导捷径的 operation catalog 中选择能力完备子图，再执行 lexicon、scope、leakage、stability 和 selection 判断。v0.7.1 的 `trial-gpt56-sol-005` 首轮通过，避开 label-only、top-only、联网和 blanket-defer 捷径，计划覆盖 `inventory -> interpret -> screen -> replay -> decide`，总规划成本 6.5，离线执行并在选出 eligible record 后停止。fixed-container replay、held-out variants 和 practitioner review 尚未完成。

## L5.2-L5.3 鲁棒策略优化

`eb010-adaptive-policy-regret-005` 把完整策略树放入四个 latent scenarios，先执行 scope、branch、future-outcome 和 budget 硬门，再按逐情景 minimax regret 选择。`gpt-5.6-sol` 的正式本地 trial 通过，因此该题证明了工作量和能力覆盖，但没有形成目标模型区分度。

`eb010-distributional-policy-stress-006` 进一步把情景权重从单一可信分布升级为五个 ambiguity-set profiles。agent 必须为 72 个 policy/scenario 分支重放状态，计算 profile-specific expected utility、允许 fractional boundary 的 weighted lower-tail CVaR、profile regret，并重复 leave-one-profile-out 稳定性选择。nominal winner 与 robust winner 被刻意分离；所有公式、tie-break 和输出 schema 仍对 agent 可见，因此难度来自鲁棒推理与交叉产物一致性，不来自隐藏规则。

## L5.4 跨阶段 claim/provenance handoff

`eb012-cross-stage-chain-002` 将 recovery、normalization、route 和 policy 四个阶段连接为一个可重放的 handoff graph。agent 必须沿每个 `upstream_hash` 传递版本、接口状态、资源 reservation 和 claim permission，并在 provenance、safety 和 robust-CVaR 门全部通过后授权一条 chain。高 CVaR 但 hash 错误、库存冲突或 claim 越界的 decoy chain 不能获胜；输出同时包含 chain decision、逐阶段 handoff ledger、审计说明和 artifact manifest。该升级增加的是跨题状态、弱链权限和多产物一致性，不是隐藏 oracle。

## L5.5 撤回感知的组合重放

`eb012-revocation-portfolio-003` 把单次 handoff 扩展到 T0/T1/T2 三个 checkpoint。source retraction、restoration 和 sensitivity 事件按顺序持久化；一条 chain 即使随后恢复，只要任一 checkpoint 无效，就不能进入最终 portfolio。两个 checkpoint-robust chain 还必须使用不同的 exclusive lot，最终按三阶段合计 utility 的最小值做 maximin 排序。最高单点分数、最终时点恢复和两个局部最优链都不能绕过历史撤回、claim 权限或共享资源门。

## L6：可复用 minimax evidence-route 模块

`math_minimax_evidence_route_selection` 是一个跨领域可复用模块，而不是 EB013 的题面别名。它要求 agent 枚举所有 blocker-valid routes，按 correlation group 做最大减免，计算每个关键不确定性的 residual，并先最小化最大关键 residual，再应用 cost 与 lexical tie-break。只“刚好跨过阈值”的 route 不能提前停止。

模块的可迁移接口固定为：`critical uncertainties + thresholds + candidate reductions + blockers + budget + objective order -> route set + residual map + objective tuple + selected route/hold`。必须包含一个 threshold-crossing 但被更低 worst-case residual 支配的 negative control；任何输出合同修复都要对原始 artifact 做 unchanged replay。正式注册和跨题适用范围见 `config/reusable_difficulty_modules.json`。

## L6：低披露 evidence routing 与 minimax residual

`eb013-evidence-budget-routing-001` 是 L6 的首个物化题。agent 必须从嵌套 catalog 和 uncertainty map 重建依赖图，在总预算内选择证据 route，并以最大 critical residual 为首要目标、总成本为次要目标、request id lexical order 为最终 tie-break。相关证据组只允许声明的最大边际 reduction 计入，未来 outcome、过期来源和缺失前置能力都不能作为当前决策依据。

该题的 primary module 是 `judgment_evidence_route_selection`；secondary modules 是 `data_dependency_graph_routing` 和 `math_minimax_evidence_route_selection`；`math_correlation_adjusted_reduction` 与 `retrieval_provenance_temporal_boundary` 为 supporting contract/safety modules。这个组合把难度放在“不要满足于任何可行 route，而要证明最坏关键残差最小”，同时保留 L5 的 provenance 与 temporal boundary。held-out 变体至少覆盖依赖修复、阈值移动、相关组重分配和预算收缩；必须通过单因素 mutation 验证每个变体会改变 route 或 decision。

EB013 的 trial 也说明了 L6 的归因规则：首轮 gpt-5.6-sol 选择了 threshold-crossing 的 `R-ASSAY`，没有选择能将最大关键残差降到 `0.15` 的 `R-CORR`，属于 scientific minimax failure；第二轮的正确 route 在 raw delivery/enum 上出现合同缺陷，经过 unchanged-artifact replay 后通过，归类为 `RAW_FAIL_CONTRACT_REPLAY_PASS`。合同 replay 不计入能力通过，且不能覆盖首轮 scientific failure。固定容器、held-out trial 和独立 practitioner review 完成前，题包只能处于 `REVIEW_REQUIRED`/`BLOCKED`。

## L6.2：跨域 evidence-policy transfer

### L6.3：三状态 adaptive-policy replay

`eb013-evidence-budget-routing-002` 的 v0.3.0 在合同稳定后只新增一个 primary module：`horizon_adaptive_policy_replay`。`R-ADAPTIVE` 现在产生 `signal_high`、`signal_low` 和 `signal_mid` 三种可观察状态；`signal_mid` 只能使用依赖有效的 `R-BALANCE`。模型必须覆盖所有状态、逐状态重算 residual/cost，并保留最坏状态作为 policy objective。缺失 `signal_mid`、复用 `R-CORR` 或提前按高 nominal value 停止都会触发 decision-flip negative control。该变体保留相同 claim boundary 和 provenance 规则，且在新的 clean target trial 前不计入能力通过。

TRANCHE-014 将相同 minimax 模块迁移到 EB010 stop/uncertainty 与 EB011 reproduction manifest。迁移任务保持公开的 objective order 和两阶段 observation gate，但使用独立的 uncertainty axes、依赖图、decoy 与 decision flips；跨域通过不能由复用候选名称或固定 stage-2 模板获得。该批次用于区分“模型记住 EB013 route”与“模型真正掌握 observation-conditioned minimax evidence routing”。

## EB013-004：信息边界与组合压力

`eb013-observation-boundary-004` 是独立题包，保留旧 EB013-002 的输入和 trial 记录。新增可复用模块 `horizon_observation_equivalence` 和 `math_distributional_minimax`，与已有共享准备成本组合。六个支持维度分别是信息分组、跨分支资源承诺、压力情景、来源时间/作用域、相关证据去重和不对称阈值。规则和输出合同公开，算法与工作顺序由模型自主规划。

原题含 3 个 stage-1、11 个 stage-2、4 个 world，来源过滤后有 2,457 个完整观测策略。独立 world-first Fraction 与 label-first Decimal 实现核对了最优解和每个替代方案的可行计数。18 个产物控制及朴素基线、8 个输入变体在 trial 前完成；7 个单因素变体改变决策，顺序变体保持不变。模块有可迁移接口，但跨领域目标模型迁移尚未验证。

冻结与校准：`scripts/calibrate_observation_boundary.py`；目标模型结果与局限记录在新题的 `quality/target_trial_evidence.json` 和 `quality/trial_analysis.md`。不得在模型失败后修改冻结输入来制造能力失败。

两次本地完整回合 `gpt56sol-v1-001` 与 `observation-boundary-gpt56sol-001` 均为 `RAW_PASS`，正常退出且冻结重放通过。两次模型都选出 Q1 的 `amber -> A6, green -> A4`，risk=0.5，worst_cost=4.5；除 prose audit 外，decision、plan 和 provenance 哈希一致。新增维度能区分朴素基线，但仍没有难住目标模型。下一版必须增加一个新的 primary difficulty axis，不能再靠输出字段、候选数量或同类约束堆叠；固定容器、跨域 held-out 和领域审查完成前仍保持 BLOCKED。

## EB014-002：序贯反馈与可退回研究交卷

`horizon_sequential_evidence_feedback` 将静态策略树升级为真实的多轮状态机。每轮模型只能提交一个动作；host 在隐藏但冻结的 scenario 中返回声明过的 measurement 与 cost，下一动作必须满足已观察依赖和剩余预算。模型最终要区分质量通过、目标 context shift、注册队列独立复现与 transport claim 权限，不能把“复现成功”错误提升为目标环境可迁移。

难度不来自隐藏格式。v1.0.0-v1.0.1 trial 暴露的 `final_claims` 容器、状态含义、布尔 checks、stop reason 和 provenance shape 均已在 v1.0.2 公开；旧失败保留为合同/基础设施诊断，不进入难度分母。公共 completion gate 只返回交付缺项，隐藏 scientific verifier 不参与逐轮提示。

冻结 trial `sequential-gpt56sol-007` 为 `RAW_PASS`：模型使用 5 个实验动作、10 个可观察 turn 和 47 次工具调用完成闭环，completion gate 一次接受，未发生预算、依赖、future-outcome 或 claim-boundary 错误。当前模块能排除固定路径、一次性交卷和 blanket abstention 基线，但没有难住目标模型。下一版若继续加难，只能新增一个科学 primary axis，例如让第一轮结果改变可用实验集合、预算与最优停止时点；不得靠增加输出字段、延长轮数或隐藏枚举升级难度。
