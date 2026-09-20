# Benchmark 任务包

这里保存从场景、模块和难度配置编译出的可执行 benchmark 任务。

## 造题管线

```text
场景清单 + 模块目录 + difficulty.toml
                    |
                    v
             benchmark_builder
          validate -> score -> compile
                    |
                    v
       task_manifest.json + difficulty_report.md
                    |
                    v
        数据实例 / environment / verifier / trials
```

每个任务包至少包含任务契约、agent-visible 输入、隐藏参考结果、verifier 和 trial 轨迹。难度配置与任务实现分离，便于在不改科学问题的情况下改变复杂度。

当前任务：

| 任务 | 场景组合 | 状态 |
| --- | --- | --- |
| `crispr-resistance-e2e-001` | pooled CRISPR screen + bulk RNA-seq + guide 设计 + 编辑验证 + 引用/图表审计 | 契约已冻结，数据与 verifier 待接入 |
| [`admiral-adsl-derivation-001`](admiral-adsl-derivation-001/) | pharmaverse 风格 SDTM → ADSL 规则派生、逐行血缘和下游 handoff 审计 | 首个临床统计工作流校准题，合成数据、已具备 verifier |
| [`eb001-split-leakage-001`](eb001-split-leakage-001/) | ADME 分子身份、canonical structure 与 scaffold split 泄漏审计 | 首批规模化校准题，合成数据、已具备 verifier；待控制实验和模型 trial |
| [`eb004-adtte-censoring-002`](eb004-adtte-censoring-002/) | ADTTE 事件选择、截止日截断、部分日期和缺失随访审计 | 合成数据、已具备 verifier；待控制实验和模型 trial |
| [`eb004-adtte-censoring-002`](eb004-adtte-censoring-002/) | ADTTE PFS 事件/删失、cutoff、竞争事件和部分日期审计 | 首批临床统计扩展校准题，合成数据、已具备 verifier；待控制实验和模型 trial |
| [`literature-screening-m1-001`](literature-screening-m1-001/) | M1 文献规模化筛读 + A11 证据表构建 | 首个离线 vertical slice，已具备数据、隐藏标签和 verifier |
| [`research-workflow-stress-test-001`](research-workflow-stress-test-001/) | 多类型科研输入 + 冲突证据 + 失败工具恢复 + 敏感性分析 | 独立高难度任务包，已具备任务书、数据、隐藏标签和 verifier；待真实 trial |

第一批规模化题包位于 [`candidate_pools/enterprise-v1/contracts/`](../candidate_pools/enterprise-v1/contracts/)，覆盖 ADME split、CompBio failure recovery、ADTTE censoring、Cell Painting normalization、retrosynthesis stock constraints 和 BayBE next-batch。当前 EB001 与 EB004 已物化为 synthetic calibration slice；其余四题仍为 contract-only。所有题目的控制实验、独立模型试跑和企业采用证据仍是发布阻塞项。

## 首个可运行 vertical slice

`literature-screening-m1-001` 是从场景表到下游 benchmark 的第一道完整案例。它把 Excel 中的 M1/A11 场景压缩成一个可复现的离线任务：Agent 读取冻结的文献 metadata/摘要快照和预注册规则，为每条记录给出 `include`、`exclude`、`context_only` 或 `uncertain` 决策，并提交证据表、不确定性队列、运行 manifest 和边界清楚的报告。

任务目录中的关键组件：

- 场景卡：[`scenario-card.yaml`](literature-screening-m1-001/scenario-card.yaml)
- Agent 输入和规则：[`data/constraints.yaml`](literature-screening-m1-001/data/constraints.yaml)、[`data/literature_records.tsv`](literature-screening-m1-001/data/literature_records.tsv)
- 任务说明和交付接口：[`instruction.md`](literature-screening-m1-001/instruction.md)、[`expected_artifacts.md`](literature-screening-m1-001/expected_artifacts.md)
- 隐藏参考标签：[`verifier_only/reference_labels.json`](literature-screening-m1-001/verifier_only/reference_labels.json)
- 程序 verifier：[`verifier.py`](literature-screening-m1-001/verifier.py)
- verifier 测试：[`tests/test_verifier.py`](literature-screening-m1-001/tests/test_verifier.py)

本题故意包含 DOI 重复冲突、仅相关性证据、动物模型、错误 outcome 和信息不足记录，测试模型是否会去重、区分证据强度、进入 uncertainty queue，而不是依赖关键词完成筛选。校准配置见 [`config/examples/literature-screening-m1-001.toml`](../config/examples/literature-screening-m1-001.toml)。

## 多维难度压力测试

[`research-workflow-stress-test-001`](research-workflow-stress-test-001/) 是一个与文献筛选 vertical slice 分开的任务。它把科研场景、科学判断、计算、工具调用、检索、信息冗杂、数据类型、数据复杂度、环境、数学、长程任务和安全边界同时写进任务合同。每个维度都有对应输入注入和输出检查，避免“难度”只停留在配置分数。

任务书、维度映射、正式发布前置条件见 [`docs/task-books/research-workflow-stress-test-001.md`](../docs/task-books/research-workflow-stress-test-001.md)。

运行任务契约和难度检查：

```bash
python3.11 -m benchmark_builder.cli validate config/examples/literature-screening-m1-001.toml
python3.11 -m benchmark_builder.cli score config/examples/literature-screening-m1-001.toml
python3.11 -m benchmark_builder.cli compile config/examples/literature-screening-m1-001.toml --out /tmp/literature-screening-compiled
```

直接运行 verifier：

```bash
python3.11 benchmarks/literature-screening-m1-001/verifier.py \
  --submission /path/to/outputs \
  --data benchmarks/literature-screening-m1-001/data \
  --reference benchmarks/literature-screening-m1-001/verifier_only/reference_labels.json
```

隐藏参考文件只供 verifier 使用，不能作为 Agent 输入挂载。当前数据是用于 verifier 校准的合成冻结记录，后续可以在同一契约下替换为经过许可和版本锁定的真实文献快照。

造题命令示例：

```bash
python -m benchmark_builder.cli validate config/examples/crispr-resistance-e2e-001.toml
python -m benchmark_builder.cli score config/examples/crispr-resistance-e2e-001.toml
python -m benchmark_builder.cli compile config/examples/crispr-resistance-e2e-001.toml --out /tmp/crispr-compiled
```

编译后，使用 `protocol` 生成 provider-neutral 的 judge 协议，用 `evaluate` 聚合结构化的大模型评价，用 `iterate` 根据弱项和跨轮退化生成下一轮唯一修改建议。完整规则见 [`docs/evaluation-pipeline.md`](../docs/evaluation-pipeline.md)。

真实模型 trial 的前置工程、adapter 环境变量、隔离边界和归档格式见 [`docs/trial-runner.md`](../docs/trial-runner.md)。当前 runner 是进程级基线，不等同于容器或 Harbor 的强隔离执行环境。

在本机没有 `python` 别名时使用 `python3.11`，或先激活项目虚拟环境。CI 会安装测试依赖。

## 临床统计工作流首题

`admiral-adsl-derivation-001` 从 EB004 的 pharmaverse 公开工作流中抽取“按冻结研究规则派生受试者级分析数据并决定是否交接”的决策。它使用六个合成受试者和五条暴露记录，注入 screen failure、无暴露、缺失 `RFENDTC` 和截止日截断四类边界；verifier 独立重算 ADSL 行、计数和输入哈希，并检查逐行血缘与合成数据声明。

```bash
python3 -m benchmark_builder.cli validate config/examples/admiral-adsl-derivation-001.toml
python3 benchmarks/admiral-adsl-derivation-001/verifier.py \
  --submission /path/to/outputs \
  --data benchmarks/admiral-adsl-derivation-001/data \
  --reference benchmarks/admiral-adsl-derivation-001/verifier_only/reference.json
```
