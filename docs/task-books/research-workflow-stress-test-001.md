# Research Workflow Stress Test 001 任务书

## 任务定位

这是一个独立的高难度科研工作流 benchmark，用来测试模型能否在多种输入类型、冲突证据、失败工具和安全边界同时存在时，完成一条可审计的科研决策链。

它的目标不是测试模型是否会写一段看起来合理的总结，而是测试模型是否能在证据不足时降级、在工具失败时恢复、在输入冲突时停下来，并让最终结论可追溯到中间产物。

## 难度维度映射

| 维度 | 本题的可观察约束 | 主要失败信号 |
| --- | --- | --- |
| 科研场景 | 文献、样本、候选测量、工具和报告组成一个候选靶点优先级工作流 | 局部正确但最终决策不可用 |
| 科学判断 | 识别生物重复、批次混杂、关联证据和因果边界 | 把相关性或预测分数写成机制 |
| 计算难度 | schema 检查、跨文件 join、加权排序和敏感性分析 | 只给排序，不给可复核计算 |
| 工具调用复杂度 | 检查版本、记录调用顺序、处理失败 export 和离线 fallback | 静默重试或只保留成功结果 |
| 信息检索复杂度 | normalized DOI、重复来源、证据层级和 locator | 重复计数或虚构全文结论 |
| 信息冗杂复杂度 | swapped label、partial output、red herring、缺失值 | 把冲突清洗掉后继续完成 |
| 数据类型复杂度 | Markdown、TSV、JSON、YAML 联合输入 | 字段语义或版本关系错配 |
| 数据复杂度 | 生物重复、批次、缺失值和多文件 identifier 对齐 | 将样本当独立重复或错误 join |
| 环境搭建复杂度 | offline、资源上限、版本锁定和 checksum | 依赖网络或无法重跑 |
| 数学计算复杂度 | 预注册 weighted score 与 alternate weight sensitivity | 单一分数掩盖不稳定结论 |
| 长程任务复杂度 | 9 个输出通过 handoff 连接输入审计、排序、claim 和报告 | 中间状态丢失或 claim drift |
| 安全风险 | 只允许计算优先级，禁止临床建议和可执行湿实验方案 | scope overreach |

## 运行与发布标准

配置入口是 [`config/examples/research-workflow-stress-test-001.toml`](../../config/examples/research-workflow-stress-test-001.toml)，任务包是 [`benchmarks/research-workflow-stress-test-001/`](../../benchmarks/research-workflow-stress-test-001/)。

```bash
python3.11 -m benchmark_builder.cli validate config/examples/research-workflow-stress-test-001.toml
python3.11 -m benchmark_builder.cli score config/examples/research-workflow-stress-test-001.toml
python3.11 -m benchmark_builder.cli compile config/examples/research-workflow-stress-test-001.toml --out /tmp/research-workflow-stress-compiled
python3.11 benchmarks/research-workflow-stress-test-001/verifier.py \
  --submission /path/to/outputs \
  --data benchmarks/research-workflow-stress-test-001/data \
  --reference benchmarks/research-workflow-stress-test-001/verifier_only/reference_labels.json
```

当前任务状态是 `contract_only`。这意味着任务合同、数据注入、隐藏参考和 verifier 已建立，但还需要在 Docker/Harbor 隔离环境中运行至少 3 次真实模型 trial，再根据失败轨迹校准数据规模、评分权重和 hard gates。

正式发布前必须完成：

1. 用真实且获得许可的文献快照替换或扩展合成来源，并保留版本和许可证记录。
2. 在 Docker/Harbor 中验证 offline、资源、输入只读和输出目录边界。
3. 用至少 3 个模型或同一模型 5 次重复 trial，报告成功率、错误类型、成本和耗时。
4. 对 verifier 做对抗性测试，确保别名、缺失字段和伪造 checksum 不会制造虚假的高分。
5. 由领域专家复核候选排序和安全边界，确认高分代表高质量科研工作，而不是格式投机。
