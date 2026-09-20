# 企业 Benchmark 知识库与改题管线

## 结论

企业 benchmark 改题不应直接复用科研场景的 `workflow -> scientific decision -> task` 单链。建议使用两条并行输入：

```text
公开企业 benchmark / workflow                    已有 skill / 科研场景
          |                                                |
          v                                                v
  企业来源与契约卡                              科研场景与方法卡
          |                                                |
          +------------------+-----------------------------+
                             v
             企业工作流语境 + 可观察决策 + 改题候选
                             |
          +------------------+-----------------------------+
          v                  v                            v
       data card        evaluation card                risk card
          \                  |                            /
           +-----------------+---------------------------+
                             v
                   Harbor delivery card
```

左侧回答“这是否真的和企业有关、公开契约是什么”；右侧回答“这是否形成了真实研究/分析决策”。两侧证据都不完整时，状态必须保持 `candidate` 或 `needs-data`。

## 知识库分层

### 1. Source layer

记录官方仓库、数据卡、挑战说明、论文、组织账号、commit/tag、访问日期、内容哈希、许可和企业参与关系。企业参与关系必须使用枚举或明确文字：`owner`、`data_contributor`、`benchmark_publisher`、`workflow_maintainer`、`consortium_member`、`third_party_reference`。

### 2. Benchmark layer

恢复原始 benchmark 契约：对象、任务、输入、输出、split、盲测状态、排行榜限制、指标、baseline、可见标签、资源需求和原始 failure mode。这里允许记录“未找到”的字段，不能用常识填充。

### 3. Workflow layer

把 benchmark 映射回真实工作节点：谁使用、处于发现/临床统计/表型筛选哪个阶段、错误会影响什么 handoff、独立实验单位是什么、哪些结论仍需人工或实验确认。这个层是企业版本相对普通 benchmark 知识库最关键的增量。

### 4. Transformation layer

每个改题版本建立独立的 transformation card。建议至少从以下维度中选三项，并且至少两项是语义变化：

| 企业改题维度 | 说明 | 可观察产物 |
| --- | --- | --- |
| `business_decision` | 从模型得分改成可执行的研发/分析决策 | 决策表、停止/升级理由 |
| `enterprise_context` | 角色、阶段、交接人、预算和审批节点 | workflow handoff、审批门 |
| `data_visibility` | 公开/盲测/部分标签/隐藏 oracle 的边界 | 可见清单、挂载测试 |
| `split_and_unit` | 分子、样本、患者、板、批次和时间的独立单位 | split manifest、重叠审计 |
| `failure_mode` | 泄漏、单位、批次、事件、约束或工具失败 | 失败注入与 verifier signal |
| `evaluation_contract` | 指标、容差、等价答案、资源和多步反馈 | evaluation card、negative matrix |
| `claim_boundary` | 计算结果、实验验证、临床/商业结论的边界 | risk card、claim ledger |
| `license_and_attribution` | 数据和代码能否进入 solver、镜像或发布包 | license matrix、NOTICE |

只有改 prompt、换文件名、换企业背景、换输出格式或增加调用次数，不构成企业 benchmark 派生题。

### 5. Delivery layer

最后才生成 Harbor task package。`harbor_delivery_card` 必须把 agent-visible、author-only 和 verifier-only 分开，登记 `task.toml`/`instruction.md`/environment/verifier/oracle/reference solution、资源和网络策略。Harbor 的目录通过之后，仍需科学、许可、隐私和模型试跑门。

## 新增质量模块

企业版在科研场景五卡和 Harbor 改题卡之外，增加六张质量卡，分别回答“是否有企业意义”和“是否对 GPT 有难度与训练价值”：

| 卡片 | 核心问题 | 未完成时的状态 |
| --- | --- | --- |
| `candidate_set_card` | 一个来源能否展开 3-5 个不同业务决策 | `DRAFT` |
| `enterprise_value_card` | 谁使用、做什么决定、交给谁、错了损失什么 | `REVIEW_REQUIRED` |
| `control_plan_card` | 正例、负例、不变性、证据不足例是否能校准判分 | `NOT_RUN` |
| `difficulty_card` | 是否存在证据整合、竞争性选择、状态依赖和捷径探针 | `DRAFT` |
| `training_value_card` | 错误是否可定位、可反馈、可迁移且不依赖答案记忆 | `EVAL_ONLY_UNTIL_CALIBRATED` |
| `model_trial_card` | 参考解、简单基线、始终弃答、模板基线和目标模型如何比较 | `NOT_RUN` |

六张卡不能用文字自证。每张卡都要绑定可执行控制、输入/输出哈希、独立真值或专家规则；未运行的项必须保留 `NOT_RUN`，不得折算为通过。

## 三类题源的差异

### 真实企业数据（A）

优先改成数据审计、时间/项目 split、缺失与不确定性、跨实验交接题。标签的企业归属和访问条款必须单独确认；不可把公开镜像的标签重新包装成内部数据。

### 企业发布 benchmark（B/C）

优先改成新子集、新的业务决策或新失败注入，并保留原始 benchmark 的 attribution 和污染风险。若原题有公开答案，不应只封装原题，应使用离线 hidden oracle、实体级新 split 或新的 evidence-boundary 任务。

### 企业公开 workflow（W）

优先改成约束、边界、handoff 和人工审核题。工具教程只证明可执行操作，不证明生产环境的业务规则；必须把示例数据、企业代码、工具默认参数和真正的内部 SOP 分开。

## 批量爬取与审核顺序

1. 用 `knowledge_base/seeds/official_sources.json` 维护官方入口；先抓组织仓库和数据卡，再扩展论文、挑战平台和二手实现。
2. 运行收集器保存 URL、HTTP 状态、标题、正文摘要、哈希和访问日期；收集器输出不直接升级为 verified。
3. 人工/程序化提取 source card 与 benchmark card；为每条事实绑定 heading、README 段落、文件、代码函数、数据卡字段或论文表格定位。
4. 仅在企业参与关系、许可、原始契约和数据可获取性都明确后进入 workflow card。
5. 对每个 benchmark 生成 3-5 个不同决策候选，再进入 transformation/data/evaluation/risk/Harbor 卡链。
6. 运行负例、参考解、独立重算、隔离测试和模型 trial；保存 `NOT_RUN`，不要把未执行写成通过。

## 与两个参考仓库的对应

- 科研 skill 仓库提供 source ledger、scenario card、候选集合、五卡链接、difficulty contract 和多 judge 选优。
- TB-Science 改题工厂提供 before/after 哈希、六维差异、claim ledger、scientific value controls、正反对照、solver/judge 隔离和 Harbor 打包门。
- 企业仓库在两者之间增加 enterprise attribution、benchmark contract、license/privacy/biosafety card 和 customer-facing claim boundary；这四项不能由科研场景卡隐含代替。

## 首批建议题族

1. ADME/ADMET：Biogen、ExpansionRx、PXR challenge；先做 split/单位/盲测/不确定性审计。
2. 高内容表型：JUMP、Recursion；先做 plate/compound split、批次校正和机制外推边界。
3. 临床统计编程：pharmaverse admiral；先做 ADSL/ADTTE 的规则派生和边界案例，不声称真实患者数据。
4. 分子设计与合成：AiZynthFinder、REINVENT4、BayBE；先做库存/约束/代理目标/人工审批，不把高分写成活性或可合成性证明。
5. FEP/结构计算：Merck FEP、Uni-FEP；先做单位、配体映射、参考集和异常审计，避免把商业引擎可用性混入题目能力。
