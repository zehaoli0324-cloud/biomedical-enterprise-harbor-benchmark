# 企业价值与 GPT 难度门

本文件把两个参考项目中的有效机制合并到企业 benchmark：科研场景仓库负责“工作流 -> 研究/分析决策 -> 可观察产物 -> verifier”，Harbor science factory 负责改题差异、科学价值控制、正负/不变性对照、solver/judge 隔离和模型试跑。企业版再增加真实业务采用和训练信号两组门。

## 1. 企业任务必须回答什么

一张 `enterprise_value_card` 至少要有：

| 问题 | 必填证据 |
| --- | --- |
| 谁在企业里使用结果 | 明确角色、项目阶段和人审 owner |
| 他要做什么决定 | proceed / stop / review / prioritize 等可执行动作 |
| 决定会交给谁 | 下游 handoff 和交付 artifact |
| 做错有什么代价 | 实验浪费、错误统计结论、审计失败、资源/安全风险 |
| 题目新在哪里 | 相对来源的语义变化、变化机制和 before/after 证据 |
| 怎样证明有用 | 采用规则、停止规则或独立实践者复核 |

以下情况只能是公开 workflow 或教学 fixture，不能称为真实企业任务：

- 只有企业名称，没有企业角色和下游动作；
- 只有 leaderboard 指标，没有业务决策或风险后果；
- 只有教程命令，没有失败停止、人工复核和交接字段；
- 用公开镜像或合成数据，却声称是企业内部数据。

## 2. 改题的新意不是加摩擦

每个来源先生成 3-5 个候选，再按 `decision`、`unit`、`error_consequence`、`handoff`、`stopping_rule` 去重。候选至少有两个语义差异，并且至少改变以下之一：

- 真实业务决策或估计对象；
- 主动考察的失败机制；
- 可见/隐藏证据和独立真值路线。

换文件名、改 prompt、增加工具调用、提高数据量、改变阈值或更换随机种子，只能算实例或压力变体，不能单独算新题。

## 3. GPT 难度的可验证定义

任务难度不由 prompt 长度或工具数量决定。至少需要一条可审计的多步链：

```text
provenance / schema check
  -> independent unit + split / design reasoning
  -> competing method or candidate choice
  -> evidence reconciliation and uncertainty
  -> bounded enterprise decision
  -> handoff artifact and claim ledger
```

难度卡必须同时写出：

- 竞争性选择：例如 proceed vs stop、支持 vs 弃答、候选 A vs B；
- 状态依赖：前置元数据或 split 失败后，后续结论权限发生变化；
- 失败注入：单位、批次、实体重叠、缺失、来源冲突、工具失败或标签不可见；
- 捷径探针：关键词、公开答案、常数预测、始终支持、始终弃答、输出数量；
- 正确的简单基线：防止把合法的直接计算误判为低质量；
- 可接受答案类：等价方法、合理不确定性和必须拒绝的越权主张。

## 4. 训练价值如何被证明

训练价值不是一次低分。`training_value_card` 要说明：

1. 目标能力：输入理解、实验单位、方法选择、证据引用、主张边界和交付；
2. 错误标签：把失败定位到最早有依据的错误节点，而不是只记最终 reward；
3. 反馈粒度：artifact、criterion、claim、failure-injection 四级至少覆盖三级；
4. 迁移轴：留出企业、实体、时间、批次、来源版本或任务实例；
5. 污染控制：冻结官方 commit、隐藏 oracle、实体级 holdout，禁止公开答案复制；
6. 训练用途：在控制和模型试跑完成前保持 `EVAL_ONLY_UNTIL_CALIBRATED`。

## 5. 最小模型试跑矩阵

每个候选的 `model_trial_card` 至少保留以下策略：

| 策略 | 目的 |
| --- | --- |
| reference solution | 证明存在合法解，并校验 verifier |
| simple legal baseline | 判断是否只是直接计算 |
| always abstain | 检查是否过度奖励保守弃答 |
| template/keyword | 检查题干和标签捷径 |
| target model | 测量 GPT 的自主分析、工具和交付 |

结果要分开报告科学正确性、证据 grounding、决策有用性、artifact 完整性、复现性、不确定性/主张边界和安全/人审。一次模型失败不能直接归因于“题很难”，必须结合轨迹判断是材料、环境、预算还是科学推理失败。

## 6. 发布门

```text
DRAFT
  -> enterprise value review
  -> candidate selection (3-5, semantic dedup)
  -> controls calibrated
  -> difficulty + shortcut audit
  -> model trial and failure attribution
  -> license/privacy/attribution review
  -> Harbor package replay
  -> READY_FOR_HARBOR
```

任一门缺证据时保持 `DRAFT`、`REVIEW_REQUIRED`、`NOT_RUN` 或 `BLOCKED`。机械 schema 通过、模型分数下降、题目数量增加都不能越过缺失的业务价值、真值、许可或模型试跑证据。
