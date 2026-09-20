# 多卡候选生成、评价与选优管线

本文只展开端到端流程的候选阶段。上游来源账本和下游编译、试跑、提交评价以 [`authoring-pipeline.md`](authoring-pipeline.md) 为准。

## 为什么需要候选池

一个开源 workflow 通常只暴露操作和文件接口，不唯一决定科研任务。同一个文献工作流可以对应纳入排除、证据复核资源分配、主张审计等不同研究决策。因此，造题不应从 workflow 直接跳到一份难度配置，而应先生成多个可比较的候选。

```text
workflow evidence
  -> 3-5 个不同科研决策候选
  -> 五类卡片的交叉校验
  -> 三个独立 LLM judge
  -> hard gates + criterion floors
  -> Pareto front + 推荐候选
  -> compile -> agent trial -> submission evaluation
```

## 五类卡片

| 卡片 | 核心问题 | 机器校验 |
| --- | --- | --- |
| Workflow evidence | workflow 实际支持哪些操作和语境，哪些推断没有依据 | 来源、locator、证据层级和核验状态非空 |
| Scientific scenario | 谁在什么研究阶段做什么决定，错了有何后果 | 科学判断、handoff、release gate 完整 |
| Scientific judgment | 哪些选择不能由模板或单一规则代替 | 每个判断都有 observable、verifier 和 claim boundary |
| Difficulty | 任务为什么难，难度来自哪个模块 | 12 维完整、模块 ID 合法、硬链接场景卡 |
| Compute | 是否能在固定预算内执行和复核 | 阶段输入输出、失败行为、资源和程序检查完整 |

卡片之间不是自由组合。候选加载器会验证 task ID、scenario ID、scientific judgment 覆盖、TOML 到场景卡的路径，以及计算卡和 TOML 的网络/CPU/内存一致性。任何一张卡修改都会改变候选池 digest，使旧 judge 结果失效。

## 候选生成

每个 workflow 默认生成 3-5 个候选，并至少改变两个科研变量：科学决策、分析单位、证据歧义、错误后果、下游 handoff 或停止规则。只改 prompt 写法、工具数量、数据量和输出格式不算新候选。

生成阶段先去掉语义重复项，再物化卡片。共享 workflow evidence card 是允许的，但各候选必须有自己的 scenario、judgment、difficulty 和 compute contract。找不到独立 verifier route 的候选不能进入评价。

## LLM 题目评价

三个 judge 必须独立运行：领域科学家、benchmark 方法学审计员、计算与复现审计员。评价九项内容：科研真实性、研究价值、科学判断、可观察性、可验证性、抗朴素捷径、计算可行性、可复现性、校准后的真实难度。

以下为 hard gates，任一 judge 判为失败就不能靠平均分补偿：科研真实性、可观察性、可验证性、结论安全、无隐藏真值泄漏、预算内可执行。

## 选优与迭代

先应用 hard gates 和各维度最低分，再在六个主要目标上计算 Pareto front。只有每个评价维度的评审一致性都达到阈值的前沿候选才能被推荐；声明的权重只用于前沿内部 tie-break。报告始终保留完整前沿，避免把有意义的“科学价值与执行成本”权衡压成伪精确总分。

没有合格候选时，`iterate-candidates` 会选择最接近合格的候选，只指定一张卡和一个最弱缺陷进行修改。修订后必须重新生成 digest 并重跑三位 judge。选出候选后，selection report 中的 difficulty-card 路径直接进入已有 `compile`、trial runner、submission evaluation 和迭代管线。

## 命令

```bash
python3.11 -m benchmark_builder.cli validate-candidates <candidate-set.json>
python3.11 -m benchmark_builder.cli candidate-protocol <candidate-set.json> --out <protocol.json>
python3.11 -m benchmark_builder.cli select-candidates <candidate-set.json> --judgments <reviews.json> --out <selection.json>
python3.11 -m benchmark_builder.cli iterate-candidates <candidate-set.json> --selection <selection.json> --out <iteration.json>
```

可运行的三候选示例位于 `candidate_pools/literature-screening-m1/`。
