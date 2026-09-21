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
