# Agent-visible Data Contract

当前任务处于 `contract_only` 阶段，因此本目录暂不包含真实测序数据、文献全文或隐藏参考答案。以下目录是 Stage 1 的固定入口：

```text
data/
├── screen/
├── rnaseq/
├── amplicon/
├── literature/
└── constraints.yaml
```

Stage 1 物化数据时必须同时提交 `input_manifest.yaml`，记录每个输入的来源、版本、checksum、许可和是否属于 agent-visible evidence。隐藏的参考排序、故障注入标签和 verifier-only 结果不得放入这些目录。

数据规模应优先选择能够在任务约束内完成 smoke run 的小型实例，再提供同一科学问题的规模化变体。数据生成不能改变 `task.yaml` 中的字段契约和失败注入语义。
