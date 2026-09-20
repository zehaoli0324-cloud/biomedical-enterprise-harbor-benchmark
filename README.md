# Biomedical Enterprise Harbor Benchmark

把生物医药企业公开可核验的研发、分析和统计编程工作流，转换为可运行、可审计、可复现的 Harbor benchmark。

本仓库的目标不是把一个数据集压缩成题目，而是保留企业工作流中的关键判断、数据血缘、工具边界、失败恢复和人工审核节点。

## 方法主线

```text
enterprise workflow / source evidence
  -> provenance ledger + scenario card
  -> 3-5 task candidates
  -> hard gates + multi-reviewer selection
  -> difficulty config + compiled contract
  -> isolated agent trial + hidden verifier
  -> scientific / reproducibility / evidence review
```

对应目录：

| 阶段 | 产物 | 入口 |
| --- | --- | --- |
| 来源登记 | 企业工作流、来源、许可和真实性口径 | [`data/enterprise_workflow_inventory.csv`](data/enterprise_workflow_inventory.csv) |
| 场景建模 | 场景卡、业务决策和失败注入 | [`benchmarks/`](benchmarks/) |
| 候选与难度 | 候选池、模块目录、TOML 配置 | [`candidate_pools/`](candidate_pools/)、[`config/`](config/) |
| 任务编译 | manifest、难度报告和评审协议 | [`benchmark_builder/`](benchmark_builder/) |
| 试跑与评审 | 隔离工作区、verifier、judge 聚合 | [`benchmark_runner/`](benchmark_runner/)、[`docs/evaluation-pipeline.md`](docs/evaluation-pipeline.md) |

## 当前 vertical slice

[`biogen-adme-audit-001`](benchmarks/biogen-adme-audit-001/) 是首个企业风格样题：agent 对一份冻结的 ADME 测量表执行训练/测试结构审计，识别跨 split 的同结构泄漏、单位不一致和缺失值，并提交带证据的审计报告。

它参考选题地图中的 Biogen ADME 方向，但当前输入是小型合成校准 fixture，不声称来自 Biogen 内部数据。隐藏真值仅供 verifier 使用，不能挂载到 agent-visible 目录。

参考仓库中的 [`literature-screening-m1-001`](benchmarks/literature-screening-m1-001/) 保留为通用文献筛选校准样例，用来回归 builder 和 verifier 管线。

## 快速开始

要求 Python 3.11+（本机也可使用 3.14）。

```bash
python3 -m benchmark_builder.cli validate config/examples/biomedical-enterprise-adme-audit-001.toml
python3 -m benchmark_builder.cli score config/examples/biomedical-enterprise-adme-audit-001.toml
python3 -m benchmark_builder.cli compile \\
  config/examples/biomedical-enterprise-adme-audit-001.toml \\
  --out /tmp/biomedical-enterprise-adme-audit-compiled
```

直接运行合成样题 verifier：

```bash
python3 benchmarks/biogen-adme-audit-001/verifier.py \\
  --submission /path/to/outputs \\
  --data benchmarks/biogen-adme-audit-001/data \\
  --reference benchmarks/biogen-adme-audit-001/verifier_only/reference.json
```

运行测试：

```bash
python3 -m pytest
```

## 企业真实性分级

每个来源都要标注口径，不能只因为题目出现企业名称就称为企业真实任务：

- `A`：企业真实实验或研发项目数据，有可核验出处。
- `B`：企业发布、整理或维护的公共 benchmark / 数据集。
- `C`：多家企业参与的联盟数据。
- `W`：企业公开工作流、工具或示例；示例数据可能是合成数据。
- `S`：明确的模拟、增强或教学 fixture。

正式发布前还必须独立核对授权、版本、数据哈希、隐藏真值、资源预算和模型试跑结果。当前仓库是框架和校准起点，不代表已经完成任何企业内部数据授权或 Harbor 生产部署。

## 设计原则

1. 科学正确性、证据追溯、工程复现、交付完整性和安全边界分开评分。
2. 任务难度绑定到可观察产物，而不是只在配置里提高分数。
3. 公开数据必须披露改编关系，并通过新切分、失败注入或新业务规则降低答案捷径。
4. verifier 必须独立重算关键结果，不能只检查文件存在或 agent 自报分数。
5. 当真值、许可或输入不足时，任务状态应为 `candidate` / `needs-data`，而不是伪装成 `ready`。

## 参考来源

本项目的候选生成、难度编译和评审结构参考 [`skill-scenario-to-benchmark`](https://github.com/zehaoli0324-cloud/skill-scenario-to-benchmark)。领域候选清单来源于本地的《生物医药企业 Harbor 选题与资源地图》研究表，后续会逐条补充公开来源、许可和运行证据。
