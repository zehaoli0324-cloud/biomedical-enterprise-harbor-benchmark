# 端到端造题管线

## 单一入口

本文件是从 workflow 到可运行 benchmark 的唯一总流程规范。各阶段的 schema 和操作细节分别位于 candidate、evaluation 和 runner 文档；它们不重新定义上游流程。

造题系统把“科研场景是什么”“题目为什么难”“模型是否做对”分成三个对象，并用 digest 和显式引用连接：

```text
workflow evidence
  -> scenario candidate
  -> selected task + difficulty contract
  -> materialized benchmark + verifier
  -> model trial
  -> submission evaluation
```

| 对象 | 描述 | 不能替代的内容 |
| --- | --- | --- |
| 场景与候选 | 研究角色、科学决策、错误后果和证据边界 | 高难度分数不能证明科研真实性 |
| 难度契约 | 12 个难度维度、模块和计算约束 | 复杂工具链不能替代科学判断 |
| 模型提交 | 轨迹、中间产物、最终结果和不确定性 | LLM judge 不能替代数值 oracle 和程序 verifier |

## 六阶段状态机

1. `mined`：建立来源账本，区分 operation、measurement、scientific decision 和 claim boundary。
2. `candidate_set`：生成 3-5 个不同科研决策候选，连接 evidence、scenario、judgment、difficulty 和 compute 卡。
3. `selected`：完成结构校验、独立 LLM 题目评价、hard gates 和 Pareto 选优。
4. `compiled_contract`：编译获选 TOML，固定 scenario digest、difficulty report 和 evaluation protocol。
5. `runnable`：物化 agent-visible 数据、隐藏真值、环境和 verifier，并完成 smoke/naive baseline。
6. `evaluated`：运行真实模型 trial，聚合程序检查与多 judge 评价，随后 freeze、adjudicate、revise 或 rollback。

只有满足当前阶段契约才能进入下一阶段。`contract_only` 不是可发布 benchmark；题目级 judge 的高分也不能跳过数据、环境和 verifier 物化。

## 难度维度

每个维度使用 1–5 级，并可设置权重、理由和标签：

| 维度 | 控制的困难 |
| --- | --- |
| `scientific_scenario` | 场景跨越的科研阶段、学科跨度和输出责任 |
| `scientific_judgment` | 实验单位、因果边界、证据质量和停止规则 |
| `computational_difficulty` | 算法步骤、分支、状态和中间产物依赖 |
| `tool_call_complexity` | 工具数量、顺序、版本漂移和失败恢复 |
| `retrieval_complexity` | 检索、去重、纳入标准、引用和主张支持关系 |
| `information_noise_complexity` | 冲突、缺失、重复、诱导性记录和红鲱鱼 |
| `data_type_complexity` | 文本、表格、序列、图像、结构和多模态拼接 |
| `data_complexity` | 数据量、稀疏性、批次、重复和标签层级 |
| `environment_complexity` | 依赖、容器、网络、资源和可重跑性 |
| `mathematical_complexity` | 单位、统计、多重检验、排序、敏感性和模型选择 |
| `long_horizon_complexity` | 步数、检查点、分支和端到端主张一致性 |
| `safety_risk` | 人类审批、基因编辑、临床和高风险输出边界 |

## 调节方式

### 改变同一道题的难度

- 保持 `scientific_judgment=5`，把 `tool_call_complexity` 从 2 调到 5，可测试同一科学判断在不同工具负担下的稳定性。
- 保持数据和工具不变，把 `information_noise_complexity` 从 1 调到 4，可测试模型是否会被冲突记录诱导。
- 保持研究问题不变，把 `environment_complexity` 从 2 调到 5，可测试环境和资源失败恢复。
- 提高 `long_horizon_complexity` 时必须增加 checkpoint 和中间产物要求，不能只增加 prompt 长度。

### 组合模块

模块分为 `scenario`、`judgment`、`compute`、`tooling`、`retrieval`、`noise`、`data`、`data_complexity`、`environment`、`math`、`horizon` 和 `safety`。目录在 `config/module_catalog.json` 中维护，任务只引用模块 ID，并可通过 `params` 覆盖局部参数。任务还必须在 `[scenario].card` 引用一个场景卡；任务的 `source_scenarios` 必须是场景卡来源 ID 的子集。

## 编译和评分

```bash
python3.11 -m benchmark_builder.cli validate <task.toml>
python3.11 -m benchmark_builder.cli score <task.toml>
python3.11 -m benchmark_builder.cli compile <task.toml> --out <compiled-dir>
```

评分先计算带权平均，再对高风险交互加分。例如长流程与工具编排、科学判断与噪声证据、数据复杂度与环境复杂度会产生额外难度。场景卡 digest、状态、科学判断数和 workflow handoff 会进入 spec digest；最终输出包含 spec digest，确保难度变化不能绕过科研语境变化。

## 执行检查清单

1. 使用 `skills/scenario-to-benchmark/` 从 workflow 文档、示例数据和代码中建立来源证据账本，区分工具操作、测量结果、科学决策和结论边界。
2. 生成 3-5 个不同科研决策候选，去除只改措辞、工具数量或数据规模的重复项。
3. 为每个候选连接 evidence、scenario、judgment、difficulty 和 compute 卡，先定义错了会怎样。
4. 选择数据类型和数据复杂度，再确定 agent-visible 输入。
5. 选择工具链和环境约束，冻结版本、资源和网络规则。
6. 添加信息噪声与故障注入，每个注入必须有预期行为。
7. 定义必需产物和 verifier-only 参考结果。
8. 用 `validate-candidates` 校验卡片，用三个独立 judge 评价，再通过 hard gates、最低分和 Pareto front 选出候选。
9. 编译获选 manifest 和 `evaluation_protocol.json`，固定当前 spec digest。
10. 物化 agent-visible 数据、verifier-only 真值、环境和 verifier，运行结构检查、smoke test、naive baseline 和独立重跑。
11. 在隔离 workspace 中运行真实 agent trial，保存轨迹、中间产物、资源状态和 verifier 结果。
12. 用三个独立 judge 对 trial 结构化评分，运行 `evaluate` 和 `iterate`，并将轨迹分类到 failure taxonomy；发现关键维度退化就 rollback。

skill 的输出覆盖 evidence、scenario、candidate selection 和 compiled contract；runner 只接受已经物化数据、环境、隐藏真值和 verifier 的任务。两者不能互相替代：难度分数不证明科研场景真实，场景描述也不等于可执行 verifier，编译成功也不等于任务已经可运行。

难度生成器不接受脱离场景卡的 standalone TOML。这样可以生成很难的题，但不能生成“只有工具数量很大、没有真实科研决策”的伪难题。

大模型评价和难度评价必须分开：difficulty dimensions 描述题目为何难，evaluation criteria 描述模型提交是否做对。评价报告必须绑定 `spec_digest`，迭代每轮只改一个因果因素，并保留上一轮可接受版本。

阶段细节分别见 [`candidate-pipeline.md`](candidate-pipeline.md)、[`evaluation-pipeline.md`](evaluation-pipeline.md) 和 [`trial-runner.md`](trial-runner.md)。
