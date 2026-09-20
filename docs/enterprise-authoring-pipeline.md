# Enterprise workflow authoring pipeline

每个企业风格 benchmark 按以下顺序推进。任何一步证据不足，都应停留在 `candidate` 或 `needs-data`，不能仅靠补写题面进入 `ready`。

## 1. 来源与真实性

在 `data/enterprise_workflow_inventory.csv` 登记组织、来源链接或 accession、发布日期、版本、许可和真实性口径（A/B/C/W/S）。把企业参与、企业发布和企业真实实验分开记录。

## 2. 场景卡

场景卡必须写清楚研究对象、业务决策、错误后果、跨步骤 handoff、必需产物和失败注入。每个科学判断都要能在输出或 verifier 中观察到。

## 3. 候选生成与选优

同一个 workflow 先生成多个不同的决策目标，例如预测、质量审计和闭环优化。先过确定性 hard gate，再由领域科学家、方法审计员和证据审计员独立评审；不要用单一总分掩盖安全或许可阻塞。

## 4. 任务契约

`instruction.md` 只描述 agent 可见输入、约束和输出 schema；隐藏真值、oracle 和 verifier 置于 `verifier_only/` 或隔离执行环境。任务必须声明网络、资源、随机性、版本和人工审核边界。

## 5. 参考解和 verifier

参考解用于确认任务可解，不等于真值来源。verifier 要独立重算关键字段，覆盖空输出、乱序 ID、单位错误、重复计数和越界结论等负例。

## 6. 试跑与发布

发布前保存输入哈希、环境摘要、资源剖析、至少一次干净参考解运行、模型 trial 轨迹和三类评审结果。若公开答案已可检索，应重新切分、改写业务规则或明确将任务标为校准题。
