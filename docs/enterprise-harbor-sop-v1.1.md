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

8. **自主规划必须有公开工作包边界。** 当题目要求 agent 自己规划任务时，mission 的 required capabilities、可用 operation、每个 operation 的 provides/depends_on、资源/网络预算和停止条件必须存在于 agent-visible 输入；catalog 可以包含明确可识别的诱导捷径，但不能隐藏关键规则。verifier 检查能力完备子图、依赖有效性、预算、离线约束和 stop-condition 与最终动作的一致性，但接受任意合法拓扑顺序。不能用隐藏的 canonical plan 作为答案，也不能把多写一个步骤当作难度。

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

## 10. 输出合同归一化门（V1.2 增补）

格式失败不能直接当作科学能力失败。每道题在 target trial 前必须把 verifier 拆成三个顺序层，并在 `quality/contract_audit.json` 中记录同一份规则：

1. **Raw delivery**：只检查 required output 是否存在、可读取、编码正确、没有越界路径。该层失败记为 `delivery_error`，不得推断科学判断。
2. **Canonicalization**：把允许的表示映射到 canonical intermediate representation（IR）。字段级 registry 必须声明 canonical 类型、允许别名/分隔符/路径前缀/根节点空值、缺失语义和禁止表示。归一化不得补造缺失记录、吞掉重复主键、修复错误 hash、改变数值或提升 claim permission。
3. **Scientific verification**：只对 canonical IR 检查 join、阈值、顺序、敏感性、provenance、claim boundary 和最终决策。该层失败才可归因为 `scientific_error`。

合同审计至少要有 `canonical_outputs` 或 `equivalence_registry`，每个输出字段都要列出 `canonical`、`equivalents`、`forbidden` 和 `missing_semantics`。每道题在模型前运行无模型矩阵：canonical reference、字段/行顺序变化、已声明别名、路径前缀或根节点空值、单字段删除、重复主键/错误 hash/错误科学状态。前四项应在归一化后保持语义结果，后三项必须失败或进入人工复核。

target trial 结果必须同时保存 `raw_verifier_result`、`canonical_replay_result`、首轮错误、修订版本、原始 artifact SHA-256 和 unchanged-artifact replay。推荐状态为 `RAW_FAIL_CONTRACT_REPLAY_PASS`、`RAW_PASS`、`SCIENTIFIC_FAIL`、`DELIVERY_FAIL` 和 `INFRASTRUCTURE_FAIL`；只有 canonical replay 仍失败时，才把结果写入“模型被考倒”或难度区分度统计。合同修复不得覆盖原始 trial，且不得改变 scientific decision、blocker 集合或 claim boundary。

这条门禁解决的是“严格但不公平”的 verifier，而不是把 verifier 变宽松：允许的只是事先登记的等价表示；遗漏、重复、篡改 provenance、未来信息泄漏和越级 claim 仍必须拒绝。

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

## 15. 部分可观测、分布风险与时点证据

增加难度维度时，把一个新的 primary module 与最多两个 secondary modules 组合；原有预算约束可作为保留机制，但不得把同一失败重复计入多个维度。`eb013-partial-observation-risk-004` 的组合为：`horizon_observation_nonanticipativity`（主）、`math_distributionally_robust_cvar`、`retrieval_asof_tombstone_resolution`，保留共享准备预算。

- **信息与时序维度**：规划者可见的假设 world 不等于执行时可见的 observation。同一 observation 下必须用同一 action；先定 probe 和准备，再观察。公开 observation map，禁止隐藏关键规则。以 world revelation 对照检验最优策略是否翻转。
- **数学与不确定性维度**：声明每个概率模型、风险水平、尾部质量分摊与排序规则。CVaR 的边界 world 必须按概率质量截取，不能退化成 mean 或 max。通过 nominal-only ablation 检验决策翻转，用 alpha 变化检验数值敏感性；两者分别记录。
- **检索与证据时点维度**：先按 decision date 过滤，再选最新完整 snapshot；withdrawal 是禁用标记，不能回退旧 active 记录。校验每个动作的 revision、availability、capabilities，再进入优化。以撤回移除对照检验决策翻转。

至少提供一套算法结构不同的精确 oracle：例如 observation-first + Decimal + 尾部积分，与 world-first + Fraction + 阈值最小化交叉核对。自动交叉核对不等于人工科学复核。观测、分布、证据和预算的单因素控制需分别留下实际结果；只改变数值而未改变选择的实验标记 sensitivity，不计为 decision flip。跨域迁移与模型 held-out trial 未执行时必须标记 NOT_RUN。
