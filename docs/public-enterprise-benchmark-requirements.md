# 公开企业 Benchmark 题目要求清单

这份清单把公开企业/联盟 benchmark、挑战赛、数据集和工作流中反复出现的题目契约整理成企业版的 `REQ01-REQ14`。它不是把网页摘要当作事实，而是要求每个来源逐项绑定官方页面、仓库文件、版本或运行证据；无法核验的字段保持 `PENDING_VERIFICATION`。

## 1. 通用要求矩阵

| ID | 题目要求 | 出题时必须冻结的内容 | 失败时的处理 |
| --- | --- | --- | --- |
| REQ01 | Task contract | 角色、对象、问题、成功条件、claim boundary | 回到 `candidate` |
| REQ02 | Input schema | 文件、字段、单位、主键、缺失和格式 | 阻塞编译 |
| REQ03 | Entity/unit/split | 分子、样本、plate、subject、series、时间或项目独立单位 | 重建 split/leakage audit |
| REQ04 | Label visibility | train/validation/test、盲测标签、阶段揭示、verifier-only truth | 隔离 oracle |
| REQ05 | Output/submission | 文件、字段、排序、命名、报告和日志 | verifier 拒绝不完整交付 |
| REQ06 | Metric/tolerance | 指标方向、聚合、容差、等价答案和不确定性 | 不把默认指标当真值 |
| REQ07 | Baseline/comparison | 官方 baseline、简单合法基线、比较范围和资源 | 防止把任务摩擦误判为难度 |
| REQ08 | Provenance/version | commit/tag、数据版本、内容哈希、证据 locator | 保持 `observed` |
| REQ09 | License/attribution | 数据、代码、模型、商标和再分发条款 | 禁止进入公开 Harbor 包 |
| REQ10 | Compute/environment | 依赖、权重、网络、GPU/CPU、内存、时间和费用 | 标记 `needs-environment` |
| REQ11 | Reproducibility | 参数、随机性、日志、checksum、重放命令 | 不得升级为 `ready_for_harbor` |
| REQ12 | Failure/abstention | 无效输入、工具失败、缺失证据、合理弃答和停止规则 | 加入 control plan |
| REQ13 | Claim/human boundary | 计算结果与机制、临床、商业或实验结论的边界 | 必须人工复核或降级 |
| REQ14 | Contamination/holdout | 公开答案、实体重叠、模板泄漏、时间/项目留出 | 重建真值和模型 trial |

## 2. 公开来源中的代表性要求

### 盲测 ADMET/活性挑战

[OpenADMET Blind Challenges](https://openadmet.github.io/blindchallenges/) 和 [ExpansionRx challenge announcement](https://openadmet.ghost.io/openadmet-expansionrx-blind-challenge/) 展示了典型的盲测契约：训练数据公开、测试化合物/标签隐藏、按阶段提交、按端点计算误差，并明确归一化误差指标。企业版不能把公开训练答案、排行榜或参赛者代码直接挂给 agent；应冻结 entity-level holdout、提交格式、metric 定义和隐藏 oracle。

对应重点：`REQ03`、`REQ04`、`REQ05`、`REQ06`、`REQ14`。

### 任务型 LLM/计算生物学 benchmark

[Genentech CompBioBench runner](https://github.com/Genentech/compbiobench-runner) 的公开说明强调隔离环境、结构化输出、成本追踪、失败可恢复、并行执行和多模型运行。企业版应把每道题的输入、输出、执行轨迹、资源、失败状态和模型版本写进交付契约，而不是只保留最终答案。

对应重点：`REQ05`、`REQ07`、`REQ10`、`REQ11`、`REQ12`。

### 临床统计编程工作流

[pharmaverse admiral](https://github.com/pharmaverse/admiral) 提供的是公开统计编程工作流和测试/示例材料，不等于 sponsor 患者数据或内部 SOP。企业版必须把 study rule、analysis unit、日期/censoring 规则、逐行 lineage、版本和审计交接独立冻结，并明确 synthetic fixture 的边界。

对应重点：`REQ01`、`REQ02`、`REQ03`、`REQ08`、`REQ13`。

### 高内容表型与联盟数据

[JUMP datasets](https://github.com/jump-cellpainting/datasets) 的元数据说明包含 plate、well、perturbation、batch、显微镜和 CellProfiler 版本之间的主外键关系，并要求通过数据库 schema 和约束验证数据。企业版不能把一行图像当作独立实验单位；应冻结 plate/batch/compound split、控制类型、metadata join、处理版本和 consortium attribution。

对应重点：`REQ02`、`REQ03`、`REQ08`、`REQ09`、`REQ14`。

[Recursion RxRx datasets](https://www.rxrx.ai/datasets) 还说明公共数据和 proprietary universe 是不同权限层。企业版必须把公开数据授权、内部数据声明和再分发权限分开，不能从公开页面推断企业内部数据可用。

对应重点：`REQ04`、`REQ09`、`REQ13`。

### 结构计算与 FEP

[Merck FEP benchmark](https://github.com/MCompChem/fep-benchmark) 以固定系统、实验参考值、指标和论文来源组成 benchmark 契约。企业版要同时保存 protein/ligand system manifest、实验 reference、指标、outlier 处理和 citation；商业引擎、模型权重和外部服务必须单独记录许可与环境。

对应重点：`REQ02`、`REQ06`、`REQ08`、`REQ09`、`REQ10`。

[AiZynthFinder](https://github.com/MolecularAI/aizynthfinder) 的运行要求包含 target、stock file、expansion/filter policy、搜索配置和公开模型数据。企业版应把库存约束、搜索预算、route validity、失败原因和人工审查写进任务，不得把“找到路线”解释成“已证明可实验合成”。

对应重点：`REQ01`、`REQ02`、`REQ07`、`REQ10`、`REQ13`。

### 约束优化和闭环实验设计

[BayBE](https://github.com/emdgroup/baybe) 的公开工作流要求显式定义 search space、目标、约束、探索/利用策略、预算和 backtesting。企业版不能只要求“最大化一个 proxy score”，而要输出下一批实验、约束满足、uncertainty、预算消耗和 stop/continue 理由。

对应重点：`REQ01`、`REQ02`、`REQ06`、`REQ07`、`REQ10`、`REQ12`。

## 3. 映射到企业出题工作流

```text
official source / repository
  -> source ledger + requirements_card (REQ01-REQ14)
  -> benchmark contract and provenance freeze
  -> 3-5 candidate decisions
  -> enterprise value + semantic difference review
  -> data/split/oracle/control plan
  -> difficulty + shortcut audit
  -> training value + controlled model trial
  -> license/privacy/claim review
  -> Harbor package replay
```

每个阶段都有明确的阻塞条件：

1. `requirements_card` 有未解决的 `REQ02/03/04/06/08/09` 时，不得进入 selected。
2. 候选少于 3 个、或只改变表面格式时，不得进入 transformation。
3. 没有正/负/不变性/证据不足控制时，不得校准 verifier。
4. 没有 reference、simple baseline、abstain、template 和 target model 的对照时，不得宣称 GPT 难度。
5. 没有错误归因、留出轴和污染审计时，只能 `EVAL_ONLY_UNTIL_CALIBRATED`。
6. 没有许可证、归属、隐私和 claim boundary 审核时，不得进入 `READY_FOR_HARBOR`。

## 4. 当前知识库的执行状态

当前仓库已登记 12 个来源，并为每个 bundle 生成 `requirements_card`。其中 EB002、EB003、EB004、EB005、EB006、EB007、EB008、EB010 已有官方页面级要求摘录；EB001、EB009、EB011、EB012 仍需进一步冻结任务契约、版本、许可和盲测/参考真值。该差异会保留在卡片中，不用“已收录”替代“已验证”。
