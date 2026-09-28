# 【Biomedical Enterprise Harbor Benchmark】生命科学 Sample 数据说明书

> 本 Sample 面向生命科学模型的能力评估、难例分析和持续迭代。本文严格区分模型可见数据、验证器隐藏真值、作者参考解和模型试跑证据。除特别注明外，数据是用于可复现决策评估的合成或结构化测试数据，不代表真实实验结论。

# 1 概要

|任务|领域|科学问题|主要数据|当前校准状态|可形成的能力反馈|
|---|---|---|---|---|---|
|eb013-cross-context-evidence-portfolio-005|跨情境证据组合|在相关、冲突和证据不足的多个情境中选择后续证据组合，并避免把相关重复当成独立证据|`evidence.json`、`followups.json`、`rules.json`、`output_contract.json`|当前版本模型通过；尚未形成稳定区分度|跨情境证据综合、独立重复识别、相关性与预算约束|
|eb014-sequential-evidence-feedback-002|序贯研究工作流|在反馈逐轮到达时选择下一步行动，维护依赖、预算、轨迹和声明边界|动作目录、动作契约、初始状态、规则、输出契约|当前版本模型通过；仍需固定容器重放|长轨迹规划、反馈利用、停止条件和声明边界|
|eb015-real-source-replacement-gate-001|来源与发布治理|判断来源权利、文件哈希、验证器绑定和发布状态是否满足替换门槛|来源清单、权利/哈希变体、发布清单、数值 provenance|修正验证器契约后通过；正式发布仍阻塞|来源追溯、哈希完整性、许可边界和验证器重新绑定|
|eb010-adaptive-policy-regret-005|闭环实验策略|在多个情景下选择最小最大后悔值策略，而不是只优化名义收益|策略、动作、情景、执行清单、规则|当前版本模型通过；待固定容器重放|稳健策略、分支预算、未来信息泄漏防护|
|eb010-closed-loop-replay-003|闭环重放|判断一个策略是否保持时间因果、预算合规和重放稳定|闭环 case、规则和隐藏参考|修正验证器契约后通过|时间因果、稳定性、可重放性|
|eb013-partial-observation-risk-004|部分观测风险|在隐藏状态不可见时选择非预见性观察策略，并控制稳健尾部风险|观测 catalog、evidence、规则、输出契约|当前版本模型通过|部分可识别性、CVaR、非预见性策略|
|eb013-shared-setup-routing-003|共享 setup 路由|在共享前置 setup 成本下规划后续请求，避免逐分支贪心超预算|请求表、规则、输出契约|当前版本模型通过|共享成本、阶段路由、预算收缩|
|eb006-donor-stratified-signal-005|供体分层信号|在供体和批次分层下判断扰动信号是否可识别，并选择受约束的后续策略|观察表、策略规则|当前版本模型通过；待固定容器重放|供体异质性、分层汇总、部分可识别性|
|eb006-research-completion-008|研究完成门控|在供体证据不完整时决定继续、补证据或 hold，并输出有边界的研究声明|观察表、研究契约、策略规则|当前版本模型通过；待固定容器重放|完成条件、证据缺口、研究声明边界|
|eb006-research-completion-011|跨 assay 研究完成|在主 assay 和独立 assay 证据存在冲突或缺失时进行 hold/review 判断|观察表、assay 观察、研究契约、策略规则|有一次可归因科学失败；需干净重跑|跨 assay 复核、注册供体缺失、失败归因|
|eb013-evidence-budget-routing-001|相关不确定性下的证据预算|在相关证据、依赖关系和时间边界下选择最小风险路线|请求 catalog、uncertainty map、运行 manifest、规则|控制校准通过；目标模型尚未重跑|相关证据折减、依赖修复、预算路由、反弃权|
|eb013-evidence-budget-routing-002|两阶段自适应证据预算|先选择第一阶段请求，再按观察结果选择第二阶段策略|第一/第二阶段请求、运行清单、规则|非法 JSON 已修复并通过 8 项回归测试；不改变既有试跑状态|自适应策略、观察分支、摘要策略兼容性|
|eb010-closed-loop-ambiguity-004|语义歧义与发现|发现输入、重建语义词典，区分可判定记录和语义歧义记录|policy records、semantic lexicon、workflow mission/catalog、规则|22 条记录已扩展；需重新校准目标模型|语义消歧、发现流程、局部弃权、来源稳定性|
|eb010-distributional-policy-stress-006|分布鲁棒策略|在多个分布情景和分支下选择 lower-tail CVaR 稳健策略|策略、动作、情景、profile 规则、执行清单|控制校准通过；目标模型尚未重跑|分布偏移、CVaR、profile regret、留一分布复核|

# 2 共同设计

这 14 道题都把科学判断、数据依赖、证据边界和可执行输出放在同一个任务契约中。题面只暴露模型需要使用的数据和输出契约；参考解、隐藏真值、变体数据和验证规则放在作者侧或验证侧路径。所有任务默认断网、要求确定性输出并记录输入哈希，避免把外部检索或不可复现运行当成科学证据。

每道题至少包含以下层次：

|层次|内容|可见性|
|---|---|---|
|任务题面|科学目标、输入、输出、预算、声明边界|模型|
|`data/`|结构化输入、规则、输出契约或公开元数据|模型|
|`environment/`|模型容器和可见数据副本|模型|
|`tests/`|验证器、变体、参考输入和回归测试|验证器/作者|
|`solution/`|只使用模型可见输入的参考解|作者/CI|
|`quality/`|证据面、契约审计、难度卡、SOP、trial 记录|作者/评审|

评估不允许用整体弃权规避主要考察项目。每道题应明确 `INSUFFICIENT_BY_DESIGN` 的局部范围，并通过正例、负例、不变性、相关证据、预算收缩或分布偏移变体检查：有足够数据的判断必须逐项回答，只有设计内证据不足的分支才可弃权。

# 3 逐题数据说明

## 3.1 eb013-cross-context-evidence-portfolio-005

### 科学问题

在多个独立 context 中，选择成本受限的 follow-up 组合，分别判断 supported、conflicted 和 insufficient evidence。不能把相关重复当作独立证据，也不能用 pooled effect 替代 context-level decision。

科学上对应的是“同一干预在不同情境下是否得到一致支持”的证据整合问题。模型必须识别哪些观测来自同一证据链、哪些 follow-up 真正增加独立信息，并在冲突 context 中保留冲突，而不能用总体平均值掩盖局部反向信号。最终结论只适用于已登记的 context 和证据条件，不延伸为普遍生物学结论。

### 数据

|文件|内容|
|---|---|
|`data/evidence.json`|证据单元、context、效应和状态|
|`data/followups.json`|候选后续请求、成本、依赖和相关性|
|`data/rules.json`|预算、阈值、相关证据折减规则|
|`data/output_contract.json`|planner、portfolio、context、provenance 和 audit 输出约束|

当前证据面包含 9 个 observable units，另有设计内 insufficient 分支；`quality/contract_audit.json` 的正例、缺 context、pooled-only、错误 independent count、错误 hash 和 metamorphic controls 已通过。

### 输出与评分

模型输出 planner、plan、decision、portfolio.tsv、context.tsv、provenance 和 audit。核心检查是逐 context 覆盖、独立样本数、相关重复折减、预算和声明边界。

### 难度证据

难点不在把效应值排序，而在同时维护 context 边界、证据独立性、替换关系和预算。公开 fixture 有 5 个 context、9 个可观察证据单元；质量卡保留 pooled-shortcut、related-repeat、independent-gain、budget-contraction、conflict-resolution、order-invariance 和 insufficient 等变体，合法 portfolio 共 512 个。独立 verifier 用 Decimal 重算并检查 5 个 context 全覆盖，控制校准和不变性检查通过。GPT-5.6-sol 当前版本通过，说明任务可完成，但尚未形成稳定模型区分度。

### Oracle 为什么正确

Oracle 穷举所有 512 个预算内 portfolio，再按每个 context 单独筛选 `quality=pass` 且 `independence=independent` 的证据。独立组不足时只能是 `INSUFFICIENT`；一正一负跨过阈值时优先判为 `CONFLICTED`；只有独立组数足够且均值达到阈值才判为 `SUPPORTED`。因此参考解选择 `F1、F4、F6、F7`，总成本 4.4，5 个 context 均为 `SUPPORTED`，不是按 pooled mean 取最大，而是按声明规则和字典序目标逐项验证。

## 3.2 eb014-sequential-evidence-feedback-002

### 科学问题

在多轮反馈逐步到达的研究工作流中，选择下一步行动，保持 round 连续、动作依赖满足、预算不超支，并在最终停止时给出 bounded claim。

研究过程从质量失败开始，后续动作只有在前置观察成功后才合法；因此模型要根据反馈更新研究状态，而不是预先写死一条路径。核心科学判断是何时证据已经支持某一层级的声明、何时只能对注册 cohort 保持 hold，以及何时必须把未解决问题交给人工复核。

### 数据

`action_catalog.json` 定义动作及成本，`action_contract.json` 定义请求/响应字段，`initial_state.json` 定义初始证据，`rules.json` 定义预算与反馈规则，`output_contract.json` 定义 research log、completion、provenance 和 audit。

### 输出与评分

输出 research log、completion、provenance、audit 和 feedback history。验证器检查错误 outcome、缺 handoff、重复 action、预算超支、round 不连续和 completion check 缺失。

### 难度证据

公开协议最多 10 轮，但合法轨迹必须先修复质量问题，再获取 context shift、独立 replication 和 orthogonal handoff，最终显式 stop；动作依赖和反馈会随轮次改变，合法路径消耗完整预算。held-out 变体专门注入错误 outcome、缺 handoff 和超预算。难度来自状态机和声明边界的联合约束，而不是人为拉长对话。v3 的 GPT-5.6-sol 试跑通过 10 轮、花费 12；早期失败被定位为 adapter/finalization，而非科学判断失败。

### Oracle 为什么正确

Oracle 从公开 `rules.json` 和动作目录读取依赖、预算与必需检查，从 verifier-only 的确定性 scenario 读取每个动作的 outcome/cost，再逐事件重算 round 连续性、依赖满足、累计花费和反馈 receipt。最终 claims 固定为 `quality=PASS`、`context=HOLD`、`replication=SUPPORTED`、`assay=SUPPORTED`、`transport=HOLD`，因为这些状态分别对应 scenario 实际解决的检查项和仍未解决的注册 cohort/transport 边界。任何猜测未来 outcome、跳过 repair、重复 action 或省略 handoff 都会被拒绝。

## 3.3 eb015-real-source-replacement-gate-001

### 科学问题

判断一个真实来源替换包是否具备来源权利、文件级 SHA-256、verifier rebind、科学 claim boundary 和发布所需的完整 provenance。

这道题考察的不是“哪篇论文结论更好”，而是来源能否被安全地带入一个可审计的数据产品。模型要把来源许可、文件身份、验证器版本和数值 provenance 连接起来，区分“可以进入审核”与“可以支持科学结论”；任何一个发布门未满足，都必须保留 blocked 状态。

### 数据

`sources.json` 和 `source_manifest.json` 保存来源及状态；`numeric_provenance.tsv` 保存文件级数值 provenance；`release_input_manifest.json` 和 `case_mutations.json` 定义发布门与变体；`rules.json`、`output_contract.json` 定义审计输出。

### 输出与评分

输出 source audit、release plan、provenance、case matrix、readiness summary 和 audit。错误 hash、撤回来源、MD5-only、缺 rights、verifier snapshot drift 和 rebind-only replay 必须被拒绝或保持 blocked。

### 难度证据

难点是四个门必须同时满足：权利状态、文件级 SHA-256、verifier rebind 和 claim boundary。质量卡设置了 rights cleared、SHA-256 frozen、verifier snapshot drift、rights withdrawal、ready-and-reordered 和 rebind-only 六类变体；9 个独立来源/控制单元均可观察，不能用整体弃权掩盖单项缺口。GPT-5.6-sol 在契约修正后能重放通过，但这只能证明规则可执行，不能证明来源治理判断已经难住模型。

### Oracle 为什么正确

Oracle 对每个 source 依次检查允许的 rights 状态、是否存在非 `PENDING`/非 `MD5_ONLY` 的 SHA-256，以及是否完成 verifier rebind，并按固定优先级生成 blocker：rights 优先于 hash，hash 优先于 rebind。当前三条基线来源的 rights 均未清，因此参考解的状态全部是 `BLOCKED_RIGHTS`，`selected_sources` 为空；claim boundary 固定为 `source_audit_only_not_scientific_claim`，因为这道题只判断发布前来源条件，不授权任何生物学结论。变体中只有 rights、hash 和 rebind 同时完成，才可进入 `READY_FOR_REVIEW`。

## 3.4 eb010-adaptive-policy-regret-005

### 科学问题

在多个隐藏情景下选择 minimax-regret 的 adaptive policy，不能选 nominal mean 最高但在某个情景中 regret 过大的策略。

科学问题是：当真实情景未知、每个情景的观测会改变后续动作时，哪种实验策略对最坏情景更稳健。模型要把情景分支、动作成本和观察条件组合成一棵完整策略树，并说明结果只是规划层面的稳健性，不是对某个实验机制或疗效的确认。

### 数据

`data/inputs/policies.json` 定义策略树，`actions.json` 定义动作和成本，`scenarios.json` 定义情景，`execution_manifest.json` 记录输入版本，`rules.json` 定义预算和 regret 计算。

### 输出与评分

输出 policy、branches.tsv、audit 和 manifest。verifier 逐分支检查 observation-conditioned action、预算、future outcome 禁止项、minimax regret 和 provenance。

### 难度证据

难点是先做结构门控，再在每条情景分支上计算 regret：必须排除缺分支、超预算和 future-outcome 泄漏，才能比较策略。质量卡明确设置了 mean-optimal 与 minimax-regret 分离、单一预算 blocker 和 future-outcome leakage 三个 decision flip。GPT-5.6-sol 试跑在 534.7 秒内完成并通过 verifier；这说明可解性已确认，仍不能把 target PASS 当成模型失败或正式 release 证据。

### Oracle 为什么正确

Oracle 对每个候选 policy 的所有 scenario branch 重放动作和成本，先判 scope、完整性、预算及 future-outcome gate，再计算每个情景相对该情景最优可行策略的 regret，最后最小化 worst-case regret。参考选择 `P-ROBUST`，而不是名义均值最高的策略；这一选择由全部分支数据、可行性门和 minimax 目标共同决定。verifier 还要求逐 policy、逐 branch、manifest 和 claim boundary 完整输出，避免只提交一个选项名称。

## 3.5 eb010-closed-loop-replay-003

### 科学问题

判断一个闭环策略在时间顺序、预算、随机性和稳定性变体下是否仍然可执行，避免从未来 outcome 泄漏信息。

这里的科学性体现在研究流程是否具有时间因果：决策只能使用当时已获得的观测，不能读取事后 outcome 反推前置选择。模型还必须判断多次 replay 的波动是否足以撤销策略，而不能因为某一次高收益运行就把不稳定策略发布为安全策略。

### 数据

`data/case.json` 保存闭环状态、动作、观测和策略候选，`data/rules.json` 保存时间因果、预算和稳定性规则。

### 输出与评分

输出 replay log、budget audit、policy decision、provenance 和 review audit。必须覆盖合法轨迹、失败轨迹和 seed/order replay。

### 难度证据

难点是同一 policy 必须同时满足 stage 顺序、预算、future-outcome 禁止项和多 seed 稳定性；高 utility 不能覆盖任一硬门。held-out 变体包括 future-outcome leakage、单一不稳定 seed 和超预算高 utility。GPT-5.6-sol 初始产物在模型正常退出后被旧 verifier 的 blocker alias 和 replay coverage 规则误判，artifact 未变且契约重放通过；因此这次结果证明 verifier 修复有效，不构成科学失败。

### Oracle 为什么正确

Oracle 逐 policy 计算 action cost、stage 是否等于规定顺序、是否读取 future outcome、seed 数和 utility spread；只有 active、预算内、顺序正确、无泄漏且达到稳定性阈值的 policy 才 eligible。随后在 eligible 集合中按 utility 最大、policy id 字典序选取；无 eligible 时返回 `request_information`。参考状态为 `policy_safe`，且 claim boundary 是 `planning_only_not_experimental_proof`，因为重放只能证明计划在给定 fixture 上安全，不能推出实验效果。

## 3.6 eb013-partial-observation-risk-004

### 科学问题

在只能看到 observation、不能访问 hidden world 的情况下，选择 ex-ante observation policy，并按 robust CVaR 和 worst mean loss 控制尾部风险。

该题模拟真实研究中只能先做可见的探针或 setup、之后才知道部分观测的情形。科学判断不是预测 hidden world，而是在信息尚不完整时承诺一套不会事后适应 hidden state 的路线，并用尾部风险回答“少数不利情景是否会让这条路线失效”。

### 数据

`catalog.json` 定义 probe 和 setup，`evidence.json` 定义 world/observation/evidence 状态，`rules.json` 定义 CVaR、预算和 human review 规则，`output_contract.json` 约束 plan、route、decision 和 provenance。

### 输出与评分

输出 observation policy、route.tsv、risk_by_model、decision、provenance 和 audit。hidden-state-conditioned action、nominal-only shortcut、wrong tail 和 withdrawal fallback 都应失败。

### 难度证据

题目把 hidden world 与 observable signal 分开，模型只能先提交 ex-ante observation policy，不能把 hidden state 当作 policy key。质量卡列出 346 个合法 policy，并保留 reveal-world、nominal-only、tail-confidence、commitment-budget 和 remove-withdrawal 变体。参考 policy 的 worst cost 为 3.5、robust CVaR 为 0.215、worst mean loss 为 0.1565；GPT-5.6-sol raw pass 且 replay pass，但 held-out 变体尚未跑完。

### Oracle 为什么正确

Oracle 枚举所有可行的 observation-conditioned policy，按 nominal、shift、rare 三个 risk model 计算 mean loss 和 fractional lower-tail CVaR，再按 hard budget 和 ex-ante non-anticipativity 过滤。参考解选择 `P2`：`a->B、b->A、c->B、d->C`，setup families 为 `basic/select`，并在每个 W1-W6 状态输出对应 route。因为动作只依赖 observation 而不依赖 hidden state，且风险指标由完整分布重新计算，该结果不是把最坏状态事后挑出来的人工答案。

## 3.7 eb013-shared-setup-routing-003

### 科学问题

在 setup 可共享但每个后续请求有独立成本的情况下，先决定 setup，再根据 observation 路由 stage-2 request，避免分支贪心导致超预算。

它对应实验平台上的共享前处理或共享测量条件：setup 一旦完成可以服务多个分支，但不能把尚未观察到的结果提前用于选择 setup。模型要同时考虑信息收益、共享成本和每个观察分支的剩余不确定性，给出可执行的条件路线，而不是分别为每个分支挑一个局部最优请求。

### 数据

`requests.json` 保存两阶段请求、setup family、观察和残余不确定性；`rules.json` 定义共享 setup 成本、预算、threshold 和 retraction；`output_contract.json` 约束 plan、decision、route、provenance 和 audit。

### 输出与评分

必须覆盖全部 observation，setup 只计一次，route.tsv 的成本和 eligible 状态必须与决策一致。缺 observation、重复 route、错误 hash 和 claim inflation 均应失败。

### 难度证据

题目要求在 observation 前承诺 setup family，再对 high/mid/low 三个观察分支分别路由 stage-2 请求；分支贪心会重复收费或超预算。质量卡包含 total budget contraction、setup price reduction、action retraction 三类 decision flip。参考最优策略的 setup cost 为 4.0，worst-case cost 为 6.8，最大 critical residual 为 0.23；GPT-5.6-sol 通过 raw/replay 检查，但当前仍处于 calibration required。

### Oracle 为什么正确

Oracle 先枚举每个 stage-1 请求的所有合法 stage-2 映射，按 setup family 的并集只收费一次，再对每个 observation 计算相关性折减后的 residual、分支成本和阈值 eligibility。按 `(worst_case_max_critical_residual, worst_case_cost, setup_cost, request_id, mapping)` 的确定性目标排序，得到 `P01`：high 走 `M01`、low 走 `M05`、mid 走 `M08`。因此它同时解释了共享 setup 为什么只计一次，以及为什么不能用某一个观察分支的局部最优替代全局 policy。

## 3.8 eb006-donor-stratified-signal-005

### 科学问题

在 donor-stratified observations 下判断扰动信号是否可识别，区分 donor heterogeneity、batch noise、missingness 和可继续验证的路径。

科学问题是一个信号是否跨供体稳定，而不是技术重复数量最多的条件是否有最高均值。模型必须把 donor 作为实验单位，识别单个供体方向反转、晚期状态缺失和技术重复造成的假精确，并把“支持”“矛盾”“证据不足”分别映射到后续研究动作。

### 数据

`observations.csv` 保存 donor/condition/measurement 观测，`policy.json` 保存候选策略、阈值和预算。数据是公开结构启发下的合成可复现 fixture，不代表真实疗效。

### 输出与评分

输出 donor 分层证据、策略、缺口说明、provenance 和 bounded claim。verifier 检查 donor 独立性、missingness、重复利用和策略门控。

### 难度证据

难点是把 technical replicate 折叠到 donor-condition-state 单元，再在 donor 层配对 control/treatment，并按 donor 异质性、缺失和状态范围判定。质量卡设置了 replicate rebalance、late-state donor restoration、early-state contraction、single donor reversal 和 inactive high-signal activation 五类变体；简单 pooled baseline 会把 `method_beta` 错判为优选。GPT-5.6-sol 第二次有效试跑 science/contract 均为 1.0，故当前是目标模型成功而非被击败。

### Oracle 为什么正确

Oracle 先按 donor 配对计算每个 condition/state 的 donor-level effect，再计算均值、范围和正向 donor 数；任何注册 donor 的非正向 reversal 先触发 `CONTRADICTORY`，不被全局均值抵消。基线结果为 `method_alpha` 和 `method_gamma` 支持、`method_beta` 矛盾；最终只在跨 early/late 均支持的候选中选择 `method_gamma`。late 状态缺一个 donor 不会被伪造补齐，正是该题要保留的 partial-identifiability 边界。

## 3.9 eb006-research-completion-008

### 科学问题

在 donor evidence 不完整时，决定继续研究、请求补证据或 hold，并确保研究完成声明不超过当前证据。

这道题把“研究完成”定义成一个可审计的门控判断：候选必须在 nominal、pooled 和 robust 三种视角下都能说明自己的稳定性，且缺失供体不能被默认当作无效或正向。模型需要解释为什么某个候选可作为下一步工作重点，同时限制结论只覆盖已登记 donor、assay 和 state。

### 数据

`observations.csv` 保存 donor/assay 观察，`research_contract.json` 定义完成条件、缺失证据和 claim boundary，`policy.json` 定义策略和成本。

### 输出与评分

输出 completion decision、evidence ledger、policy、provenance 和 audit。verifier 检查完成条件、未来结果泄漏、donor 缺失和声明膨胀。

### 难度证据

题目要求同时输出 nominal、pooled 和 robust 三种估计，并执行 leave-one-donor-out 与 measurement perturbation replay。困难点是同一候选在 nominal、pooled 和 robust estimand 下可能不同，且缺失证据只能影响对应单元，不能把整题 blanket HOLD。GPT-5.6-sol 的有效试跑给出 `nominal=C43、pooled=C28、robust=C17` 并通过科学 verifier；这确认了题目可解，但不是目标模型失败。

### Oracle 为什么正确

Oracle 对每个 registered unit 用精确数值计算 control/treatment effect，再分别重算 donor-balanced、row-pooled 和 leave-one-donor-out 场景；候选先经过每个 state 的 donor 数、均值、范围和 contradictory/weak/insufficient precedence。然后 nominal、pooled、robust 各自只在 eligible 候选中取确定性最优者，并把三者不一致记录为审计原因。这样 `C43/C28/C17` 的不同不是主观偏好，而是同一输入在三种明确 estimand 下的可复算结果。

## 3.10 eb006-research-completion-011

### 科学问题

在主 assay 与独立 assay 证据交叉验证时，判断是否满足研究完成、是否应 hold 或请求人工复核；任何未注册 donor 或 assay 缺口都必须保留。

科学上这是“独立测量是否真正复现主 assay 信号”的问题。主 assay 内部的强信号不能自动覆盖独立 assay 的缺失、方向冲突或配对不足；模型必须把局部不完整性保留下来，并说明它阻止的是哪一层声明，而不是把整份数据全部判为无效。

### 数据

`observations.csv` 保存主研究观察，`assay_observations.csv` 保存独立 assay 观察，`research_contract.json` 定义跨 assay 完成门，`policy.json` 定义策略规则。

### 输出与评分

输出跨 assay completion、evidence ledger、policy、provenance 和 audit。verifier 特别检查 registered-donor missingness、cross-assay concordance 和 hold oracle。

### 难度证据

题目在 EB006-008 的多 estimand reconciliation 上再增加独立 assay gate：36 个科学单元中 35 个可判定，1 个 assay 单元故意保留不完整。质量卡保留 row-order、replicate-balance、influence-repair、scope-noise 和 threshold-hold 变体；主要难点是局部缺失必须局部 hold，不能用完整主 assay 把独立 assay 缺口覆盖掉。GPT-5.6-sol 一次完成并通过，但另一次完成 public contract 后在 `C43|late` 的 assay 状态上失败，且不是 timeout/格式问题，因此是目前最明确的科学能力失败证据；仍需追加重复试跑。

### Oracle 为什么正确

Oracle 复用 donor-balanced、row-pooled、leave-one-donor-out 的精确计算，然后对独立 assay 逐 condition/state 检查方向一致性、最小 assay effect、effect range 和 registered donor coverage。`C43|late` 的 assay pair 缺少 treatment/control 配对，故该单元不能被标为 `SUPPORTED`；只要任一注册 assay 单元不是 `SUPPORTED`，`assay_selected` 就必须为空并设置 `cross_assay_hold=true`。这解释了为什么 Oracle 保留 hold，而不是把 35 个完整单元的支持结果扩展到缺失单元。

## 3.11 eb013-evidence-budget-routing-001

### 科学问题

在相关证据、依赖图、时间边界和有限预算下，选择使 maximum critical residual 最小的证据路线，而不是选择 nominal value 最高的请求。

科学问题是如何用有限实验预算优先消除真正的关键不确定性。模型要识别前置依赖、相关证据的重复计数和截止时间，区分“已经跨过一个阈值”与“所有关键 residual 已经足够小”；因此路线选择不能只按单个请求的 nominal information value 排序。

### 数据

`request_catalog.json` 保存请求、成本、依赖和相关性；`uncertainty_map.json` 保存不确定性项；`run_manifest.json` 保存输入版本；`rules.json` 定义折减和预算。

### 输出与评分

输出 plan、route.tsv、decision、provenance 和 audit。必须记录 bottleneck、dependency、correlation、budget 和 human review；整体弃权不应通过。

### 难度证据

难点是依赖图、时间边界和相关证据折减同时生效：某个 request 达到阈值不代表 maximum critical residual 已最小。质量卡列出 dependency graph repair、critical threshold shift、correlation reassignment 和 budget contraction 四类变体，并明确记录 observed failure：目标模型曾在达到阈值后停止，漏掉更低 residual 的路线。当前扩充后 target 尚未重跑，因此该题可以说已有真实难度信号，但不能宣称完成校准。

### Oracle 为什么正确

Oracle 根据 `rules.json` 先过滤时间有效、无 future outcome 且满足依赖的 request，再按 correlation group 计算有效 reduction，并在预算内最小化 maximum critical residual。参考组合为 `R-ASSAY + R-ORTHO`：只选 `R-ASSAY` 时最大 residual 为 0.20，加入 `R-ORTHO` 后降到 0.15、总成本为 4，因此满足主目标；便宜但相关的证据不会被重复计为独立收益。verifier 要求 route、bottleneck、correlation 和 hash 同时一致，避免只报一个最终 request。

## 3.12 eb013-evidence-budget-routing-002

### 科学问题

先选择 stage-1 request，再根据实际 observation 选择 stage-2 policy；不能预先固定 stage-2，也不能把 summary-only policy 误判为结构异常。

这道题把证据预算问题推进到自适应决策：第一阶段请求的观察结果会改变第二阶段最值得做的验证。科学上要回答的是“不同观察状态下，哪一条证据链最能降低剩余风险”，并且每个分支都要有可解释的 eligible/hold 结论，而不是只给一条平均路线。

### 数据

`stage1_requests.json` 和 `stage2_requests.json` 保存两阶段候选请求，`run_manifest.json` 保存数据版本，`rules.json` 定义观察分支、预算和相关证据折减。

### 输出与评分

输出 plan、route.tsv、decision、provenance 和 audit。verifier 检查 stage-2 是否依赖 observation、三状态覆盖、相关性 double-count、预算和 hash。

### 难度证据

这是两阶段自适应版本：stage-1 观察结果决定 stage-2 policy，且观察分支扩展为 high/mid/low。质量卡保留 observation label swap、stage-2 budget contraction、dependency repair、correlation reassignment 和 three-way observation branch；固定 stage-2 shortcut 会在多个分支上失败。当前控制校准 6 项通过、回归测试 8 passed；GPT-5.6-sol 的原始产物在 canonical policy replay 后通过，科学决策未改变，因此仍需 fixed-container 和 held-out trial。

### Oracle 为什么正确

Oracle 先枚举 stage-1 request，再对每个 observation 计算 residual、critical threshold 和 eligible 状态，形成完整的 policy tree。参考解选择 `R-ADAPTIVE`，其 stage-2 映射是 high=`R-SELECT`、mid=`R-BALANCE`、low=`R-CORR`；缺少 mid 分支、把 stage-2 固定不随观察变化或把相关证据重复计数都会改变 tree。验证器的 canonicalization 只从已声明 residual/threshold 推导等价字段，不替换科学决定，所以本次 JSON 契约修复不改变 Oracle。

## 3.13 eb010-closed-loop-ambiguity-004

### 科学问题

发现嵌套输入、重建语义词典，区分明确可继续、明确不可继续、future outcome、archived 和局部语义歧义记录；只有设计允许的歧义记录可弃权。

科学问题在于把实验记录中的自然语言状态转成可审计的研究状态。标签、叙述、历史归档和 replay 数值可能互相冲突；模型必须先发现并读取完整输入，再判断语义歧义、范围越界、未来信息泄漏和重放不稳定分别阻断哪一层决定，不能把最高 utility 当作唯一标准。

### 数据

`policy_records.json` 保存记录及 replay/label/narrative，`semantic_lexicon.json` 保存语义映射，`workflow/mission.json` 和 `operation_catalog.json` 保存发现与执行流程，`run_manifest.json` 和 `rules.json` 保存 provenance/规则。

### 输出与评分

输出 plan、decision、evidence.tsv、discovery 和 audit。verifier 检查逐记录覆盖、语义 blocker、发现文件 hash、未来 outcome 和 claim boundary。

### 难度证据

当前数据扩展为 22 条 record，难点链条是发现嵌套输入、按依赖顺序规划 workflow、重建 semantic lexicon、区分歧义与 utility，并应用 scope、leakage、stability 和 budget gates。Oracle 明确设置 choose-highest-utility、trust-label-over-narrative、ignore-archived-scope、skip-discovery-hash 和 force-proceed 等 shortcut probes。扩展后原有 trial 结论不再适用；质量卡将状态标为 ready for recalibration，而不是把旧通过结果沿用到新数据。

### Oracle 为什么正确

Oracle 先把 `label+narrative` 与 lexicon 中的 proceed/review/future-outcome 词项规范化，再计算每条 record 的 utility 均值、replay range、scope、signal、uncertainty、cost 和 future-outcome blocker。语义歧义先变成 `human_review`，future outcome 和 out-of-scope 具有更高优先级；只有无 blocker 的 eligible record 才能按 utility 最大、record id 字典序选择。扩展数据中的参考选择是 `P-OMICRON`，这是一条由逐记录门控和完整 discovery hash 得出的结果，不是按一个标签直接挑选。

## 3.14 eb010-distributional-policy-stress-006

### 科学问题

在多个 distribution profiles、scenario branches 和 action budget 下，选择 lower-tail CVaR 与 profile regret 均稳健的策略，并做 leave-one-profile-out 稳定性分析。

它对应数据分布变化下的策略选择：同一 policy 在名义分布表现好，不代表在 shift 或 rare profile 的低尾部也安全。模型要分别计算 profile 内的期望效用、低尾 CVaR 和相对 profile 最优的 regret，再用留一 profile 分析判断结论是否依赖某一个分布假设。

### 数据

`policies.json` 保存候选策略，`actions.json` 保存动作与成本，`scenarios.json` 保存场景，`rules.json` 保存 profile 权重、CVaR 和预算，`execution_manifest.json` 保存版本与 hash。

### 输出与评分

输出 policy、branches.tsv、profiles.tsv、audit 和 manifest。必须覆盖所有场景和 profile；nominal mean-only、unweighted tail、future-outcome decoy 和 over-budget policy 都应失败。

### 难度证据

难度链条包括 join 五类输入、重放 72 个 branch、应用 hard gates、整合五个 distribution profile、计算 fractional lower-tail CVaR、构造 profile regret，并重复 leave-one-profile-out。质量卡的 shortcut probes 包括 nominal mean only、unweighted tail、把不合格 policy 当成 profile best 和省略 sensitivity replay；当前 evidence surface 尚未记录 held-out variants，target 也尚未重跑。

### Oracle 为什么正确

Oracle 对每个 policy/branch 先判 scope、budget、future-outcome 和 action 完整性，再按每个 profile 的权重计算 expected utility 和 lower-tail CVaR。对每个 profile 先求可行 policy 的 best expected utility，再计算各 policy 的 profile regret；最终按最大 robust CVaR、最小 max profile regret、nominal utility 和 policy id 的确定性顺序选择 `P-ADAPT`。leave-one-profile-out 只作为稳定性诊断，不会偷偷改变主选择，因此结果可由 profile 表逐项复算。

# 4 前沿模型试跑与科学能力判断

本节只纳入本地已有、可追溯到题包质量卡或报告的结果。“模型完成”表示模型产出了可通过验证器的答案；“契约重放通过”表示原始答案在修正验证器对公开等价格式的误判后通过；“考到科学能力”只在模型对科学判断本身出现可归因错误、且不是基础设施或输出格式问题时使用。

|模型与任务|结果|是否考到科学能力|判断|
|---|---|---|---|
|GPT-5.5，`literature-screening-m1-001`|8/8 screening decisions 正确；首轮 verifier 因公开 reason-code 别名误判，校准后通过|否|证明题目可解和契约已修正，不作为模型难度结论|
|GPT-5.6-sol，`eb013-cross-context-evidence-portfolio-005`|v2/v3 均 RAW_PASS，held-out replay 通过|否|模型完成了组合优化，但没有被当前版本难住|
|GPT-5.6-sol，`eb014-sequential-evidence-feedback-002`|科学轨迹正确；部分首轮问题属于路径/adapter，当前版本 RAW_PASS|否|证明序贯任务可完成，不证明目标模型区分度|
|GPT-5.6-sol，`eb015-real-source-replacement-gate-001`|契约修正后 unchanged-artifact replay 通过，9 个来源门判断正确|否|主要是契约兼容性修复，不是模型科学失败|
|GPT-5.6-sol，`eb010-closed-loop-replay-003`|时间因果、预算和 future-outcome gate 正确；契约重放通过|否|证明任务可执行，不证明重复稳定性或难度|
|GPT-5.6-sol，`eb010-closed-loop-ambiguity-004`|发现输入并正确区分 proceed、review、future-outcome 和 archived|否|证明一次成功的语义消歧，不证明模型已被难住|
|GPT-5.6-sol，`eb006-research-completion-011`|历史 v2 试跑出现 4 个跨 assay 科学状态不匹配；不是 timeout 或格式问题|是，初步证据|模型把不完整注册供体场景错误地判为支持，属于可归因的科学判断失败；正式结论仍需 clean rerun|

总体判断：当前批次已经能区分“题目可完成”“验证器契约有问题”和“模型科学判断失败”三类情况。现有证据中，`eb006-research-completion-011` 是最明确的科学能力失败样例；其余已完成 trial 的题目多数说明模型能完成任务，但还没有形成稳定的目标模型区分度。GPT-5.5/5.6 的本地 process trial 不能替代 Harbor 固定容器、重复试跑和领域专家复核。

# 5 数据、验证与发布边界

本批题目的数据说明必须与题包中的 `task.yaml`、`data/`、`tests/`、`quality/` 保持一致。数据扩充只允许通过版本化 fixture、同步 environment/test/reference 和重新计算输入哈希完成；不能只增加题面数字或只修改参考解。

当前 14 道题均处于内部校准或待 replay 阶段。即使本地测试、contract audit 或 model trial 通过，也只能说明对应自动化门已通过，不能推出真实实验有效性、临床结论或正式 Harbor 发布资格。正式发布仍需根据每道题的 manifest 完成 fixed-container replay、必要的 held-out trial、practitioner review、来源/许可审查和 claim-boundary 审查。

# 6 当前批次汇总

|批次|数量|状态|
|---|---:|---|
|快速收口队列|10|已有目标试跑或完整 author-side 证据，仍有发布阻塞项|
|校准优化扩展|4|数据/控制面已优化，部分题尚未重新 target trial|
|合计|14|内部优化批次，不宣称正式发布|

这份 Sample 数据说明书只描述数据、科学判断和评估边界；任何模型分数、trial 结果或 verifier 通过记录都应以对应题包的版本化质量卡和原始证据为准。
