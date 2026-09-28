# Enterprise Harbor 出题 SOP V1.2

这份 SOP 是企业题从候选到 Harbor trial 的强制门禁。`compiled`、`CALIBRATED` 或静态 schema 通过都不等于可以跑 target model，更不等于 `READY_FOR_HARBOR`。

## 1. 先冻结来源和决策合同

每道题必须绑定 source ledger、公共数据/文献 registry、版本或 accession、下载入口、文件级 SHA-256、许可证和 transformation manifest。公开数据只能支持公开声明；不能把公开 workflow 或 benchmark 说成企业内部生产数据。

题目合同至少冻结：角色、业务决策、独立单位、输入字段/单位/主键、split 和可见性、required outputs、失败注入、停止/人工 handoff、claim boundary、等价答案和容差。

## 2. 题包边界

Agent 只能看到 `instruction.md`、`data/` 和可写的 `outputs/`。`verifier.py`、`tests/`、`verifier_only/reference.json` 只能在 verifier 侧使用。`instruction.md` 必须逐项写出每个 `outputs/...` 路径、字段、单位、排序、主键和允许的等价表示。

verifier 不得只接受一个隐藏答案，除非题面明确声明唯一目标、方向和 tie-break；合法替代答案应按约束、性质和容差评分。claim boundary 应检查结构化字段，而不是依赖题面未声明的固定短语。

## 3. 四类控制和五类 trial

控制计划至少包含 `positive`、`negative`、`invariance`、`insufficient_evidence`，并记录单因素变更和校准结果。模型前固定执行：

1. `reference_solution`
2. `simple_legal_baseline`
3. `always_abstain`
4. `template_or_keyword`
5. `target_model`

每一项都必须有明确状态；未执行就是 `NOT_RUN`。`reference_solution` 证明题可解，不能代替独立 verifier；`always_abstain` 不能被 verifier 错误奖励；template/keyword 用来查捷径。

## 4. 模型前 contract audit

第一次真实模型调用前，运行：

```bash
python3 scripts/check_enterprise_harbor_sop.py \
  benchmarks/<task-id> \
  --output reports/<task-id>-enterprise-sop-preflight.json
```

随后运行与模型无关的 verifier/contract audit。至少确认：独立领域专家按 instruction 产出的语义正确答案能通过；空输出、乱序、重复、单位错误、越界 claim 和证据不足能失败或转人工；oracle 与 nop 在独立 verifier 环境中完成。process-only 只能是预检。

preflight 的 `status=PASS` 只表示题包合同允许进入 target-model trial；发布仍要读取独立的 `release_status` 和 `release_blockers`。因此 `target_model=NOT_RUN` 不阻止首次 trial，但会继续阻止发布。

若出现 `enterprise-output-path-undocumented`、`enterprise-output-schema-missing`、`enterprise-verifier-phrase-undocumented` 或 `enterprise-single-answer-contract`，状态必须回退到 `CONTRACT_ONLY`，先修 instruction/verifier。

## 5. 失败归因和发布状态

模型 trial 失败必须按最早可定位节点归因：

- `agent_not_run`：provider、认证、容器或 runner 在生成前失败，不计入难度；
- `agent_completed_verifier_failed`：模型正常退出但 verifier 拒绝，必须回放 artifact 并检查合同一致性；
- `agent_completed_verifier_passed`：模型完成且通过，仍要查捷径和信息泄漏。

`TIMEOUT_INFRASTRUCTURE`、认证失败、容器未启动、artifact 未收集均是基础设施 blocker，不得写成“模型答错”或“题目足够难”。

状态只能按以下顺序推进：

```text
SOURCE_OBSERVED -> REQUIREMENTS_REVIEWED -> CANDIDATE_SET
-> SELECTED -> CONTRACT_ONLY -> CALIBRATION_READY
-> EVAL_ONLY_UNTIL_CALIBRATED -> MODEL_TRIAL_COMPLETE -> READY_FOR_HARBOR
```

`READY_FOR_HARBOR` 还需要来源/许可证/隐私、企业价值、独立 truth/verifier、四类控制、五类 trial、重放和 claim review 的独立证据。任何缺项都保持 `BLOCKED` 或 `REVIEW_REQUIRED`。

## 6. 当前批次的处理结论

本仓库当前两道新 mined task 的 reference 和控制已完成，但 target model 为 `TIMEOUT_INFRASTRUCTURE`，所以只能标记为 `BLOCKED`，不能从该结果推断 GPT 难度，也不能晋级 Harbor。先完成 preflight 和独立 verifier audit，再重跑 target model。

## 7. 可迁移的 L4 难度模块

六道 L4 题的难点分析和试跑归因见 `docs/l4-tranche-005-difficulty-analysis.md`，机器可读登记见 `config/l4_tranche_005_transferable_modules.json`。当前登记五个跨领域模块：

- `judgment_minimal_sufficient_disclosure`：只在真实 blocker 存在时 handoff，不能把所有不确定性都变成弃答。
- `judgment_contract_equivalence_and_replay`：显式区分语义判断、等价表示和合同修复后的原产物 replay。
- `judgment_local_eligibility_global_selection`：分离候选 eligibility、共享资源约束和全局 selection。
- `audit_cross_artifact_consistency`：让 decision、evidence、manifest、digest 和 claim ledger 保持同一状态。
- `math_deterministic_tie_break`：在并列或近并列目标值下使用公开、可重放的二级规则。

模块只有在 agent-visible evidence、公开合同、positive/negative/invariance/insufficient-evidence 控制和单因素 mutation 都齐全时才算实现。首轮模型因未声明的枚举和证据标签失败时，必须按 `invalid_contract_defect` 归因并保留原产物 replay；不能把合同缺陷包装成模型科学能力失败。

## 8. V1.2 本轮优化门禁

上一轮六道 L4 题暴露出“结构 preflight 通过”仍不足以保护 trial 解释。V1.2 对新题增加以下强制要求：

1. **合同审计先于模型难度结论。** `quality/contract_audit.json` 必须记录每个 required output 的路径、字段、单位/枚举、允许等价表示、claim boundary 和可回放样例，并标记 `status=PASS`。模型首轮 verifier failure 必须先在 `scientific_error`、`contract_error`、`delivery_error`、`infrastructure_error` 四类中归因；未完成归因不得写入“模型被考倒”。
2. **跨 artifact 一致性必须可验证。** 若题目有表格和汇总 JSON，verifier 必须同时检查主键覆盖、数值、状态、排序和 blocker 传播；只检查最终 winner 不算通过。至少有一个单字段 mutation 会被拒绝。
3. **难度组合要有预算。** `difficulty_card.json` 必须声明一个 `primary_module`、不超过两个 `secondary_modules`、至少三个 held-out variants，以及每个模块对应的 decision-flip control。重复文件、隐藏 enum 和增加格式负担不能计入难度。
4. **模型前证据冻结。** 在 target trial 前冻结 task/version、instruction、data、verifier、contract audit 和 control digest。任何修订都要增加 version，保留原 artifact，并对原产物 replay；不得边看模型答案边收紧 verifier。
5. **通过也要做区分度审计。** 单次 target pass 只能记为 `PASS_SINGLE_TRIAL`。要宣称模型区分度，至少需要三个 held-out variants、一次 independent verifier audit 和一次无模型的 contract replay；否则保持 `DIFFICULTY_NOT_DISCRIMINATING` 或 `REVIEW_REQUIRED`。

6. **等价表示必须在 trial 前冻结。** 对每个结构化字段登记 canonical form、允许别名、路径归一化和不可接受的缺失情况；用 reference、field-order、alias、prefix 和 single-deletion fixtures 逐项验证。缺字段、重复主键、漏记录、错误 hash 和错误科学状态不能被“别名兼容”掩盖。

7. **contract replay 必须可审计。** 首轮失败后只允许修改 verifier/contract 版本，必须保存首轮错误集、修订 diff、原始 artifact SHA-256 和 unchanged-artifact replay 结果；修改后不得直接覆盖原 trial 记录。

8. **摘要输出与 verifier 异常必须有专门防回归。** 如果合同允许 summary-only、keyed-map 或完整逐状态三种表示，verifier 必须先把字符串状态名、对象状态行、空值/不完整策略分别映射到 canonical IR，再进入科学校验；不得对合法摘要行调用字典方法。每个允许表示至少要有一个 positive fixture，每个类型错误要有一个 negative fixture。verifier 主入口必须把 `TypeError`、`AttributeError`、`KeyError`、解析错误和超时转成结构化 `infrastructure_error`/`contract_error` 结果，不能抛出未捕获异常，也不能把 crash 记为模型 scientific failure。`quality/contract_audit.json` 必须保存 `representation_matrix`、`crash_regression` 和 raw/canonical 两层结果。

9. **自主规划必须有公开工作包边界。** 当题目要求 agent 自己规划任务时，mission 的 required capabilities、可用 operation、每个 operation 的 provides/depends_on、资源/网络预算和停止条件必须存在于 agent-visible 输入；catalog 可以包含明确可识别的诱导捷径，但不能隐藏关键规则。verifier 检查能力完备子图、依赖有效性、预算、离线约束和 stop-condition 与最终动作的一致性，但接受任意合法拓扑顺序。不能用隐藏的 canonical plan 作为答案，也不能把多写一个步骤当作难度。

## 9. L5 低披露、环境复杂性与语义含糊

低披露只能减少重复解释，不能隐藏决定答案所需的规则。输入 schema、semantic lexicon、scope、阈值和环境约束可以分散在嵌套文件中，但必须能由 agent-visible manifest 和确定性 join 完整发现；verifier 必须从同一批公开输入重新推导，不能依赖未披露答案标签。

当前登记三个可迁移模块：

- `retrieval_schema_discovery`：递归发现嵌套输入，验证 manifest 覆盖、相对路径和 SHA-256，并把缺失发现与错误科学判断分开。
- `judgment_semantic_ambiguity_resolution`：当 proceed 与 review 线索同时成立时，utility 不能消解语义冲突；必须转人工 review，并保留 scope、future leakage 和 numeric blocker 的独立原因。
- `environment_schema_discovery_under_offline`：记录 network state、determinism 和输入边界；离线约束必须在 runner 或容器层可执行，不能只靠题面声明。

这类题至少增加两项控制：高 utility 的 ambiguous adversarial case，以及不改变语义的 synonym/path-prefix metamorphic case。首轮 verifier fail 后必须对原始 artifact 做 hash 固定的 contract replay：路径前缀、布尔/枚举别名和冗余语义编码属于等价表示；缺文件、漏记录、错误 scope、未来 outcome 泄漏或越过 blocker 才属于能力失败。任何 verifier 兼容修订都要保留首轮错误、修订理由和 unchanged-artifact hash，不能悄悄覆盖 trial 结果。

## 9.1 L6 证据预算路由与 minimax 难度模块

`eb013-evidence-budget-routing-001` 是第一道 L6 低披露 evidence-routing 题；`eb013-evidence-budget-routing-002` 在同一合同基础上只增加一个新的主轴：先观察、后按观测状态选择第二阶段证据。两道题都把 L5 的策略/闭环约束提升为“在预算内选择依赖有效、时间有效且能最小化最坏关键残差的证据 route”。输入仍必须全部 agent-visible；难度来自公开依赖图、观测条件、相关证据的边际收益、minimax 目标和 future-outcome 边界的联合推理，不来自隐藏 oracle 或额外格式字段。

该题的可迁移模块登记如下：

- `judgment_evidence_route_selection`（primary）：不能在找到任一 threshold-crossing route 后停止，必须比较所有合法 route 的最大 critical residual，并按公开的二级规则选择。`R-ASSAY` 单独通过局部阈值但被 `R-ASSAY + R-CORR` 支配的分支，是该模块的 decision-flip control。
- `data_dependency_graph_routing`（secondary）：route 必须满足 `depends_on`、required capability 和 temporal gate；缺少前置证据时只能请求信息或 hold，不能用高 nominal value 越级。
- `math_minimax_evidence_route_selection`（secondary）：按 `(maximum critical residual, total cost, lexical request ids)` 的公开顺序优化；必须同时报告 route、成本、残差和 tie-break witness。
- `math_correlation_adjusted_reduction`（supporting）：同一 correlation group 的证据不能重复计入 reduction，只能计入声明的最大边际降低量。该模块支持科学计算，但不替代 primary/secondary 难度预算。
- `retrieval_provenance_temporal_boundary`（supporting contract/safety）：只能使用决策时点前且未撤回的来源；future outcome、archived-only 记录和错误 hash 必须被拒绝。它是 provenance 边界，不作为额外 secondary 难度轴。
- `horizon_two_stage_acquisition`（EB013-002 primary）：第一阶段只能提交公开且依赖有效的 observation request；第二阶段必须为每个 agent-visible observation state 声明合法 policy，不能提前消耗第二阶段预算、漏掉状态、固定套用 nominal winner 或读取 future outcome。该模块的 decision-flip 是“同一第一阶段请求在 signal-high 与 signal-low 下需要不同的第二阶段 route”。

L6 的难度预算仍遵守“一主、最多两辅、至少三个 held-out variants”规则。EB013-001 的 held-outs 为 dependency graph repair、critical threshold shift、correlation group reassignment 和 budget contraction；EB013-002 额外固定 observation-label、stage-one budget、dependency-edge、future-source withdrawal 和 correlated stage-two pair 五类单因素变体。decision flips 为 future nominal winner、correlated cheap pair、missing-prerequisite request、dominated threshold-crossing route，以及 signal-high/signal-low 的条件 route 翻转。重复文件、别名枚举、输出路径或字段数量都不计入难度。

EB013-001 的既有 gpt-5.6-sol trial 给出了可归因的 mixed evidence：首轮 scientific trial 选了只满足局部阈值的 `R-ASSAY`，漏掉 `R-CORR`，因此是对 minimax route objective 的有效失败；retry 找到 `R-ASSAY + R-CORR`，初始 raw failure 仅涉及输出路径和等价 decision enum，未改动 artifact 的 contract replay 通过。后者只能记录为 `RAW_FAIL_CONTRACT_REPLAY_PASS`，不能抵销首轮的科学失败。EB013-002 在本文写入时仅完成 contract audit、无模型控制和 calibration，target-model trial 必须另行记录 raw/canonical replay，不能借用 EB013-001 的结果作为两阶段难度证据。固定容器 replay、held-out difficulty trial 和 practitioner review 仍是发布门。

### L6.2 跨域迁移批次

同一难度模块只有在跨业务域 held-out 中仍产生相同的可观察 decision flip，才算可迁移。TRANCHE-014 使用三个题包验证这一点：EB013 的一般两阶段 evidence policy、EB010 的 stop/uncertainty policy，以及 EB011 的 reproduction remediation policy。三题共享 `math_minimax_evidence_route_selection`、`horizon_two_stage_acquisition` 和 `judgment_evidence_route_selection`，但不得共享隐藏答案、候选 ID 或领域标签捷径。

EB010 必须在 `plateau` 与 `discordant` 后选择不同的 replicate/reconcile 请求；EB011 必须在 `topology_mismatch` 与 `parameter_drift` 后选择不同的 rebuild/pin 请求。每题都要包含高 nominal value 的固定策略、future-outcome 诱导项、dependency-invalid 路径，以及刚好过阈值但被更低 worst-case residual 支配的策略。只有 reference、六类 controls、独立 verifier audit 和 target trial 均按相同归因规则完成后，结果才可计入跨域难度证据。

## 10. L7 分层可识别性与独立实验单位

`eb006-donor-stratified-signal-005` 将难度从自适应 evidence policy 转向独立实验单位。主轴 `math_stratified_partial_identifiability` 要求先在 donor/state/condition 内折叠技术重复，再逐 state 使用不同的最低 donor 数、mean-effect 和 effect-range 阈值。一个 donor/state cell 缺失时，只要该 state 仍达到公开 quorum，就不能把整个候选强制标成 `INSUFFICIENT`。辅助轴 `judgment_conflict_precedence` 要求任一已识别 donor 的非正 effect 优先于 pooled mean；`noise_pooled_stratified_adversary` 通过不均衡技术重复，让错误的 observation-row pooled 计算选择不同候选。

该模块必须提供 reference、技术重复伪重复、pooled shortcut、全局阈值、任一缺失即弃答、行序不变、wrong-hash 和 claim-inflation 控制。oracle 至少用一套不导入 verifier 的独立实现复算 donor effects、state mean/range、status 和 winner。verifier 应分别输出 `science_score` 与 `contract_score`；delimiter、JSON 表示、排序或 artifact 收集错误不能记为实验单位推理失败。

首轮冻结 trial 在 300 秒边界前写出并自检全部正确产物，但 agent 会话未正常结束，分类为 `TIMEOUT_INFRASTRUCTURE_OUTPUT_VERIFIED`，不进入难度分母。相同哈希题包在 420 秒重跑中正常退出并 `RAW_PASS`；两轮四份产物哈希完全一致。因此当前模块只证明能拒绝朴素 pooled/blanket-abstain 捷径，没有考倒 `gpt-5.6-sol`。下一版只允许增加一个新 primary axis：leave-one-donor-out 稳定性；不得通过增加文件、隐藏 enum 或收紧格式来升级难度。

## 10. 输出合同归一化门（V1.2 增补）

格式失败不能直接当作科学能力失败。每道题在 target trial 前必须把 verifier 拆成三个顺序层，并在 `quality/contract_audit.json` 中记录同一份规则：

1. **Raw delivery**：只检查 required output 是否存在、可读取、编码正确、没有越界路径。该层失败记为 `delivery_error`，不得推断科学判断。
2. **Canonicalization**：把允许的表示映射到 canonical intermediate representation（IR）。字段级 registry 必须声明 canonical 类型、允许别名/分隔符/路径前缀/根节点空值、缺失语义和禁止表示。归一化不得补造缺失记录、吞掉重复主键、修复错误 hash、改变数值或提升 claim permission。
3. **Scientific verification**：只对 canonical IR 检查 join、阈值、顺序、敏感性、provenance、claim boundary 和最终决策。该层失败才可归因为 `scientific_error`。

合同审计至少要有 `canonical_outputs` 或 `equivalence_registry`，每个输出字段都要列出 `canonical`、`equivalents`、`forbidden` 和 `missing_semantics`。每道题在模型前运行无模型矩阵：canonical reference、字段/行顺序变化、已声明别名、路径前缀或根节点空值、单字段删除、重复主键/错误 hash/错误科学状态。前四项应在归一化后保持语义结果，后三项必须失败或进入人工复核。

target trial 结果必须同时保存 `raw_verifier_result`、`canonical_replay_result`、首轮错误、修订版本、原始 artifact SHA-256 和 unchanged-artifact replay。推荐状态为 `RAW_FAIL_CONTRACT_REPLAY_PASS`、`RAW_PASS`、`SCIENTIFIC_FAIL`、`DELIVERY_FAIL` 和 `INFRASTRUCTURE_FAIL`；只有 canonical replay 仍失败时，才把结果写入“模型被考倒”或难度区分度统计。合同修复不得覆盖原始 trial，且不得改变 scientific decision、blocker 集合或 claim boundary。

这条门禁解决的是“严格但不公平”的 verifier，而不是把 verifier 变宽松：允许的只是事先登记的等价表示；遗漏、重复、篡改 provenance、未来信息泄漏和越级 claim 仍必须拒绝。

### EB013-002 verifier crash 复盘

`eb013-evidence-budget-routing-002-gpt56sol-006` 的模型产物给出了正确的 `R-ADAPTIVE` 策略、三状态 action mapping、最坏残差和成本，但 `decision.json` 用字符串数组概括 `observation_states`。旧 verifier 将该合法摘要当成完整对象行并调用 `.get()`，产生未捕获 `AttributeError`；runner 因而记录 `infrastructure_error`。修订后的 verifier 先区分 summary-only 与完整 replay，并把全 `null` action mapping 规范为 incomplete policy；未修改的五份 artifact 随后 replay PASS。

该案例固定以下判定：verifier crash 不等于模型失败；正确科学 route 不能因等价摘要表示被拒绝；兼容修订必须保持 route、预算、残差、eligibility、provenance 和 claim boundary 的原校验强度。后续每个允许 summary row 的题包都必须在 trial 前提供完整对象 positive、summary-only positive、incomplete-null positive、错误类型 negative 和“主入口不抛异常”回归测试。

## 11. 先修合同，再升难度

同一批题不得同时修复输出合同和增加科学难度。处理顺序固定为：

```text
CONTRACT_TRIAGE
-> CANONICAL_CONTRACT_FROZEN
-> RAW_TRIAL_REPLAYED
-> CONTRACT_STABLE
-> DIFFICULTY_ESCALATION
-> HELD_OUT_DIFFICULTY_TRIAL
```

- `CONTRACT_TRIAGE`：按 delivery、contract、scientific、infrastructure 四类归因首轮失败。
- `CANONICAL_CONTRACT_FROZEN`：冻结 required outputs、字段 registry、等价表示、禁止表示、mutation matrix 和 verifier 版本。
- `RAW_TRIAL_REPLAYED`：用未修改 artifact 完成 canonical replay；原始错误、hash 和修订 diff 必须保留。
- `CONTRACT_STABLE`：至少一个 reference、一个等价表示、一个字段删除、一个错误 hash 和一个错误科学状态 fixture 的结果符合预期；不能有未归因的格式失败。
- `DIFFICULTY_ESCALATION`：只新增一个 primary difficulty module，最多两个 secondary modules；不得借增加字段、枚举或输出格式制造难度。
- `HELD_OUT_DIFFICULTY_TRIAL`：用新的单因素 decision-flip / held-out variant 验证新增难度，不能把合同修复 replay 当成难度证据。

如果仍存在 `RAW_FAIL_CONTRACT_REPLAY_PASS` 或未解决的 `contract_error`，题目只能停留在 `CONTRACT_STABLE` 之前，禁止进入下一档难度设计。

## 12. Adaptive-policy replay 难度模块

`horizon_adaptive_policy_replay` 用于检验 agent 是否覆盖 stage-1 输入中声明的全部 observation states，而不是只回答题面示例或常见分支。题面必须公开 state 列表、每个 state 的合法 action、依赖、预算、逐状态计算和 worst-case 聚合规则；verifier 必须从 agent-visible 输入枚举完整 policy，不能依赖隐藏 canonical branch 名称。

该模块至少包含六类控制：完整三状态 positive、缺少一个状态 negative、状态顺序 invariance、单分支预算不足、依赖无效 action，以及新增 held-out state。decision flip 必须由“补入或撤回一个可观察状态后，原 policy 从 eligible 变为 incomplete/hold，或最优 action mapping 改变”产生。只增加行数、文件数或输出字段不算难度。

`states`/`observation_states`、`observation`/`observation_state` 等预登记别名只在 canonicalization 层处理；别名归一化不得生成缺失分支、补造 residual、修复错误 action 或忽略 provenance hash。target trial 必须同时保存 raw verdict 与 unchanged-artifact replay，只有完整 state coverage 和科学计算都通过，才能认定该模块通过。

## 13. 观测前共享准备成本

`math_ex_ante_shared_setup` 要求先承诺所有分支可能需要的准备，再观察结果。准备费按整张策略使用的 family 并集计一次，执行费按实际分支计；分别检查 stage-1、commitment 和最坏分支总预算。必须公开成本时点、共用关系、全部依赖、逐轴阈值和排序规则。

实现时至少保留两个可行竞争策略，并证明逐分支 greedy、只付观测分支准备费、重复计共享准备费会产生错误成本或选择。预算、准备价格、action 撤回三个单因素变体应实测产生决策翻转。用不同搜索顺序和精确数值实现交叉核对 oracle；自动数学核对与人工科学复核分别记录。跨业务迁移未经检验时标记 NOT_RUN。

新题必须提供自包含输出合同。逐行校验表格主键、动作、数值与 JSON 决策，不能只比较行数。试跑使用冻结的题包与 verifier，并等待 agent 正常退出；文件出现不是完成信号。保存原始 verdict、产物 hash、重放结果和 adapter 版本，避免构建脚本重置历史 trial。

## 14. 可观察信息边界与多维压力

新增模块 `horizon_observation_equivalence`：必须区分决策时真正可见的 observation label 与仅用于评分的 latent world。同一 label 对应的所有 world 必须使用同一后续动作。`math_distributional_minimax` 则对每个 world、每个 axis 分别计算 residual/threshold，再取最坏值；不得擅自使用均值或最大绝对残差。

多维加难采用一个 primary、最多两个 secondary，其余作为明确列出的支持约束。维度数量不是难度证据。必须在模型前证明：至少两个可行竞争策略；平均风险、绝对残差或廉价优先等朴素策略会选错；观测分组、来源撤回、容量或阈值的单因素变化可改变动作、第一阶段选择或 hold 状态。仅标签重命名不算决策翻转。

EB013-004 的验证顺序为 label-first Decimal oracle 与 world-first Fraction oracle 对齐，再运行缺失/重复 world、世界 ID 偷看、错误 hash、错误来源、非有限数和越界 claim 的真实产物变异。模型可自行选择算法和工具，但预算、截止时间、观测能力和输出合同不能隐藏。原题与旧 trial 保留；新变体单独冻结，结果不能与旧题合并计算通过率。

本地 calibration 使用等待完整进程结束的 adapter。记录 adapter hash、输入/规则/verifier hash、真实退出状态、产物 hash 和原始评分。timeout 只记 timeout，未见输出不能推断模型没有思考，更不能推断启动阶段故障。自动 oracle 核对不冒充独立人工审查；process-cwd 模式不冒充容器隔离，正式发布仍需独立隔离重放和领域审查。

## 15. 部分可观测、分布风险与时点证据

增加难度维度时，把一个新的 primary module 与最多两个 secondary modules 组合；原有预算约束可作为保留机制，但不得把同一失败重复计入多个维度。`eb013-partial-observation-risk-004` 的组合为：`horizon_observation_nonanticipativity`（主）、`math_distributionally_robust_cvar`、`retrieval_asof_tombstone_resolution`，保留共享准备预算。

- **信息与时序维度**：规划者可见的假设 world 不等于执行时可见的 observation。同一 observation 下必须用同一 action；先定 probe 和准备，再观察。公开 observation map，禁止隐藏关键规则。以 world revelation 对照检验最优策略是否翻转。
- **数学与不确定性维度**：声明每个概率模型、风险水平、尾部质量分摊与排序规则。CVaR 的边界 world 必须按概率质量截取，不能退化成 mean 或 max。通过 nominal-only ablation 检验决策翻转，用 alpha 变化检验数值敏感性；两者分别记录。
- **检索与证据时点维度**：先按 decision date 过滤，再选最新完整 snapshot；withdrawal 是禁用标记，不能回退旧 active 记录。校验每个动作的 revision、availability、capabilities，再进入优化。以撤回移除对照检验决策翻转。

至少提供一套算法结构不同的精确 oracle：例如 observation-first + Decimal + 尾部积分，与 world-first + Fraction + 阈值最小化交叉核对。自动交叉核对不等于人工科学复核。观测、分布、证据和预算的单因素控制需分别留下实际结果；只改变数值而未改变选择的实验标记 sensitivity，不计为 decision flip。跨域迁移与模型 held-out trial 未执行时必须标记 NOT_RUN。

## 出题完成门：默认 Trial 与分析

每次新题构建或影响科学决策、输入、输出合同、verifier 的实质修改完成后，默认立即执行目标模型 trial 和结果分析，无需再次询问是否试跑。仅文档勘误不触发重跑。控制测试通过或标记 `PRETRIAL_VALIDATED` 只是中间状态，不是交付完成。

固定顺序为：控制与独立 oracle 检查 → 冻结输入/合同/verifier/adapter → 使用既定目标模型完成完整运行 → 原始产物评分 → 未修改产物的冻结重放 → 逐项结果归因与难度结论 → 归档。多题批次逐题记录，不用一题 trial 代替整批。模型或预算需要实质变更时另行确认，不自动升级模型或无限重试。

每题保存 trial ID、模型、时间与超时限制、退出状态、隔离方式、原始评分、产物和事件日志 hash、冻结重放、关键决策对照、失败层级及题目缺陷。分析必须回答“是否选对、证据与分支是否完整、是否只因合同失败、有没有题目或判分错误、本次能否支持难度结论”。单次通过说明本次未难住该模型；单次失败也不证明普遍能力缺陷。

遇到鉴权、配额、网络或基础设施阻塞时保留实际记录并报告 `BLOCKED`/`INFRASTRUCTURE_FAIL`；不得写成科学失败或省略 trial 状态。试跑期间不改冻结题面与判分规则，修复必须新版本、新 trial ID，旧产物与原始 verdict 不覆盖。仅控制通过、未跑目标模型的题目必须明确标记未完成此门。

## 可退回交卷的研究完成门

不要以“多想几次”或固定聊天轮数作为难度机制。先公开可验证的研究要求：主分析、必要的竞争解释或独立复算、合理敏感性检查、实际分歧与结论边界。定义唯一的计算问题时，不强迫凑多种方法。一次程序调用可完成大量有效探索，分析时应检查程序内部覆盖而不是仅统计轮数。

完成门只返回实际缺失的 artifact、字段、研究案例覆盖或可复算性问题。独立科学 verifier 在交卷后评分，不把预期数值、正确候选或隐藏测试结果逐轮喂给模型。完整首次提交立即接受；可复现但错误的提交可通过完成门、在科学评分层失败。必须有这种反例控制，防止混淆“做完”与“做对”。

运行器保存每次交卷的原始快照、真实执行日志、反馈、代码/输入 hash 和累计预算。声明最多提交次数及全程共享时间，正常结束才检查交卷；模型超时或基础设施错误单独归因。预算耗尽保留未完成项，不无限重启。继续执行可采用同一会话或保留工作区的新会话，但必须如实登记。

EB006-006 原型采用主分析、pooled 竞争解释诊断和全体 leave-one-donor-out 检查。三种排序故意可能不同，必须重算并定位敏感供者。公开完成门独立运行提交代码两次及一次行序变体，再由最终 verifier 对正确性和改变测量值后的程序输出评分。运行器所有回执由系统生成，不能相信模型自报“已经运行”。该本地执行原型没有安全沙箱，生产发布仍需容器、网络和资源隔离。两轮 gated trial 都正确重算出 nominal `C43`、pooled `C28`、robust `C17`，并写出完整 executable artifacts；首轮同时暴露 `reason_codes` 本应是无序集合以及试跑期间源合同发生并发变更的问题，第二轮在最终回复前发生 SSE 重连并耗尽 adapter 预算。冻结 workspace 的 completion replay、行序 replay、输入扰动 replay 和 scientific verifier 均通过。因此记录为 `TIMEOUT_INFRASTRUCTURE_OUTPUT_VERIFIED`，不计入模型难度分母，也不能声称模型被考倒。

运行器必须在长时间科学 replay 前先检查必需路径与非空文件，区分工作区根文件和 `outputs/` 交付文件；不得自动搬移模型文件。adapter 的 reconnect/error 事件进入基础设施记录，不能静默吞掉，也不能用“已有结果”冒充正常 turn completion。共享预算耗尽时仍应对已有 artifact 执行公开 completion replay 并归档 receipt，状态记为 `timeout_output_complete` 或 `timeout`；该 replay 不能把退出码 124 洗成正式通过。试跑使用的题面、公开合同、verifier 和 adapter 必须从同一冻结快照读取，禁止边跑边改源文件。预算耗尽后保留当前 artifact、未完成项和最后错误，禁止无限重启。

最小控制矩阵：缺项→退回→补齐→接受；首次完整→直接接受；最大次数耗尽；输入篡改；可复现错误答案；常量输出程序；主/替代/敏感性选择翻转；顺序不变性。记录真实试跑退回次数，未触发退回就明确报告零次，不将机制存在说成模型发生了多轮探索。

## 真实数据和真实文献替换

十题替换计划的唯一登记入口是 `Downloads/ten-task-real-data-replacement-plan.md`，机器可审计副本是 `config/real_data_replacement_registry.json`。当前十题按 `REAL_PUBLIC_RAW`、`REAL_PUBLIC_DERIVED`、`SYNTHETIC_CALIBRATION`、`RECIPE_ONLY` 和 `STAGING_REBIND_REQUIRED` 分层；下载到文件不等于已完成真实数据验证。

每题的真实化必须冻结 accession/DOI、项目 URL、下载 URL、版本或访问日期、许可证/权利、文件清单、逐文件 SHA-256、变换谱系及行/图像/帧选择规则。每个科学字段写入 `data/numeric_provenance.tsv`，校准文件标记 `CALIBRATION_EXCLUDED`；`data/release_input_manifest.json` 是 agent-visible allowlist。先从最小确定性 snapshot 重算 reference 和 hidden labels，再重建 verifier、claim-evidence matrix、正/负/不变性/证据不足 controls，完成许可与独立科学复核后才能打包。

计划中的主要入口包括 CRISPR 论文补充数据、BBBC021 官方数据页和 Zenodo MD 档案；同时登记 PBMC3k、GSE90546、GlycoPOST 和 LINCS 入口。来源链接是研究入口而非再分发授权：CRISPR 补充文件、BBBC021 图像/ground truth 和 Zenodo 大型轨迹都要做文件级 rights/许可判断。BBBC021 页面标为 v1 并列出图像、compound 和 MoA 文件；Zenodo 记录为 DOI `10.5281/zenodo.10362368`、v1，存档下载和 checksum 必须与冻结 manifest 一致。许可证、原始结构金标准、accession、独立复核或 verifier rebind 任一缺失时，题目保持 `BLOCKED`/`REVIEW_REQUIRED`，不能把 staging 或 synthetic calibration 写成真实科学证据。

真实化和加难分开版本管理：先完成来源/许可/claim boundary 门，再做 contract audit、模型 trial 和分析；真实数据替换不得在模型答错后反向调整 hidden labels 或 verifier。所有真实 trial 继续保存原始输入 hash、下载清单、变换脚本、环境、结果和未修改 replay。

## EB014 增补：证据缺口与追加研究

EB014-001 将任务从“对已算好的分数排序”推进到“测量重建 → 前提状态 → 结论权限 → 追加研究 → 条件重放”。主模块为 `research_minimum_additional_evidence`，辅模块为 `judgment_claim_transportability_boundary` 和 `horizon_adaptive_research_priority`；独立来源 quorum 是支持约束，不重复计为第四个主难度。模块条目在 `config/reusable_difficulty_modules.json`，参数、控制与迁移边界随模块保存。

出题时保留任务目标、验收规则、全部可选结果、预算、作用域、停止规则与输出合同；可以不提供步骤、工具选择、候选筛选顺序和中间答案。降低信息披露应删除答案捷径，而不是删掉能唯一判断正确性的条件。允许模型自行规划，不允许 verifier 依赖未披露的枚举名、默认值或规则。

以下问题必须在模型试跑前避免：

1. 输入不能包含 `recommended`、指定 `first_action`、预设 `claim_ceiling` 或按状态写好的最优分支。来源记录提供原始观测与元数据，由逐字段规则推导状态；oracle 不能按候选 ID 分支。
2. 明确区分 unknown、refuted 和 supported。证据不足不等于反证；合成验收规则中的 refuted 也不是反向生物学或因果证明。原始作用域结论与外推结论之间必须有公开的桥接前提。
3. 规划目标不能只奖励“必然阳性”：研究结果未观察时不得抬高当前 claim。可用公开的结论消歧权重，把支持与否定都计为解决问题；同时公开负结果的处置和前提冲突优先级。
4. 最坏成本相同不代表每条路径都高效。声明何时强制停止，或明确额外的成本排序规则；用“问题已解决仍继续花钱”的控制检查，不能由隐藏 verifier 事后补加停止条件。
5. 每个所选动作的每个结果都要重放，累计成本、依赖和当前权限逐状态重算。当前证据 ledger 与 hypothetical replay 必须分文件；只计划执行桥接研究不能立即授权外推。
6. 静态结果目录必须标明是条件策略重放，不冒充在线实验、工具服务或真实反馈。若要考在线获取能力，另建有调用记录和状态隔离的环境，不能凭静态 CSV/JSON 宣称已覆盖。

验收矩阵至少包括：独立组重复、撤回/过期来源、错误作用域、未来信息、测量阈值、预算收缩、依赖、缺失/重复/额外分支、数值非有限、错误 hash，以及已登记的等价表示。标签改名和行顺序只计 invariance；改变真实策略才计 decision flip。自动化 prose 关键词命中不作为科学正确性的证据，叙述质量由另记状态的人工复核负责。

EB014-001 的预试跑证据为 24 个产物检查、8 个输入变体，其中 6 个实际策略翻转、1 个顺序不变性、1 个标签等价性。递归 Decimal 全策略树与独立 Fraction 两阶段笛卡尔积求解交叉核对；两者独立计算证据状态。该结果只能标记 `PRETRIAL_VALIDATED`。目标模型 trial、隔离容器重放、跨域迁移和领域人工审查尚未执行时必须各记 `NOT_RUN`，不可写成“模型被考倒”或“已验证可迁移”。

EB014 后续已执行 `gpt56sol-v1-001`：gpt-5.6-sol 原始评分与冻结重放均通过，约 565 秒，无超时。本次未难住模型。该实例仅有 12 个合法策略，主要是单条两阶段依赖链，可作为正确性锚点，不能把模块数量当成高难度证明。完整记录在题包 `quality/trial_analysis.md`；跨域、held-out 模型试跑和人工复核状态不随本次通过自动提升。

复用顺序：先选择一个真实决策及待解决结论，再登记前提、作用域、独立单位和候选行动，构造至少一个会选错的朴素策略，完成单因素翻转与合同审计后冻结题包，最后跑模型并区分科学、合同、交付和基础设施失败。人工检查还应确认合成规则没有被包装成普适科学规律。

## 16. 分层证据充分性与独立 follow-up

题目需要跨 context、batch、cohort 或 donor 比较时，禁止用 pooled 汇总替代注册层级的科学决策。每个层级必须分别输出 `SUPPORTED`、`CONFLICTED` 或 `INSUFFICIENT`，并公开独立统计单位、质量过滤、方向阈值和停止规则。任一层缺失或方向冲突时，claim handoff 必须保留边界，不能因为 pooled mean 为正而强行支持。

follow-up 组合题必须区分 independent group 与 related replicate。相同成本或相同记录数不代表相同信息量；相关重复不能增加 independent count。候选组合按预算整体优化，目标顺序、空组合、最便宜策略和 tie-break 必须公开。至少执行“相关重复”“新增独立组”“替换低质量/冲突记录”“预算收缩”四类控制，并记录实际 selected portfolio 与 context 状态变化。

充分性模块的最小证据矩阵包括：同向充分 positive、方向翻转 negative、单层缺失 abstention、pooled-only negative、独立 follow-up positive、related-repeat negative、行序/标识重命名 invariance。只改变样本量、行数或输出字段而不改变独立性、分层状态或 claim permission，不算新难度。

## 17. 嵌套输出合同的显式 shape 门

JSON required output 不能只列字段名。凡是有嵌套对象、数组元素或相互依赖字段，instruction 必须给出最小合法 JSON shape 示例，并同时声明键名、层级、类型、允许空值和禁止的顶层别名。`task.yaml` 的 required fields、公开 `output_contract.json` 和 verifier 的 canonical parser 必须使用同一层级定义。

合同校准至少加入一组“正确科学决策 + 错误嵌套层级”的 negative fixture；例如 checksum 必须位于 `input_sha256` 对象内时，顶层同名键不能被宽松接受。target trial 发生此类失败时，先归类为 `RAW_FAIL_CONTRACT`，保留原始产物和 hash，再只修订合同说明并递增 task version。修订版必须对未修改 scientific decision 做冻结重放；只有修订版仍失败，才进入模型难度统计。

## 18. 序贯反馈与长轨迹校准门

需要持续研究轨迹时，必须把一次模型交互定义为“模型消息发出动作并获得环境反馈”的轮次；同一消息中的并行工具调用只计一轮。工具调用总数、环境实验次数、交卷退回次数和有效决策轮次分开记录，不能用脚本循环或拆文件凑出超过 40 轮。

交互题的最小状态机为：公开初始证据 → 单个动作请求 → 隐藏但冻结的环境回执 → 累计预算/状态更新 → 下一合法动作或停止/人工 handoff。回执只能包含已声明的测量与成本，不得返回隐藏分数、正确类别或推荐下一动作。重复动作、未来结果泄漏、预算重置和从新会话伪装连续轨迹必须拒绝或单独归因。

题面应公开完成契约和合理提前停止；完成检查只验证产物、执行回执、依赖、预算和 claim boundary，不把科学评分反馈给正在运行的模型。完整提交即使少于 40 轮也应允许交卷；超过 40 轮只是预注册的轨迹属性。报告必须同时给出长度、科学质量、交付质量、成本和终止原因，不能把长而重复的轨迹当作难度证据。

长轨迹试点先做固定动作路径的服务端回放，再做目标模型 trial。固定路径必须能在不暴露 hidden scenario 的情况下重放，输入、场景、回执和事件日志可校验。若模型首轮写出请求但 provider、网络或 adapter 在回执前失败，分类为 `INFRASTRUCTURE_FAIL`，不计入“模型被考倒”；保留请求、退出码和事件日志。只有模型收到真实反馈后仍违反依赖、claim boundary 或预算，才进入科学/交付错误分析。

### 序贯题的公开交卷退回与错误归因

序贯题不得把最终输出 schema 留在隐藏 verifier 中。嵌套容器名、字段类型、枚举、布尔常量、hash 覆盖范围和 provenance 元数据都必须在 agent-visible `output_contract` 中声明。`context_status` 等状态还要说明它表示证据强度还是决策权限；例如观测到并确认 `context_shift` 可以支持“存在偏移”，但 transport 决策仍应为 `HOLD`。未声明这些语义造成的 raw failure 是合同缺陷，不是模型失败。

环境接受 `stop` 后必须提供独立的最终交付阶段，不再要求或允许新实验。runner 先执行只依赖公开文件的 completion gate：检查 required files、JSON shape、required checks、stop reason、claim boundary 和 provenance hash。缺项时返回具体公开缺项并允许在共享总预算内修复；不得返回隐藏 scenario、预期科学状态或 verifier 分数。随后独立 scientific verifier 才检查真实观测、依赖、预算和 claim boundary。

adapter 必须使用全程共享 deadline，并在请求文件完整落盘后主动回收当前模型进程、消费请求、写入冻结环境回执，再启动下一轮。单轮超时前已落盘的合法请求应先被消费并记录；provider/SSE 未退出、app-server 初始化失败和陈旧 `running` manifest 仍按基础设施归因。隐藏 task 路径不得传入模型子进程环境。

`eb014-sequential-evidence-feedback-002` v1.0.2 的冻结 trial `sequential-gpt56sol-007` 正常完成：5 个环境动作、10 个可观察模型 turn、47 次工具调用、1 次 completion gate 接受，agent exit code 0，verifier PASS。模型依次完成 quality audit、context comparison、independent replication、orthogonal handoff 与 stop，并保持 `registered_cohort_only`。因此该题证明序贯 completion gate 可运行且能增加真实研究行为，但单次 trial 没有考倒 `gpt-5.6-sol`；固定容器 replay 和 practitioner review 完成前仍保持 `BLOCKED`。
