# Benchmark Review Agent

一个用于 benchmark task 审核、验证和证据汇总的智能体基架，参考 Harbor 的自动检查和大模型审核流程。

## 目标

- 在提交给人工审核前，先运行可重复的结构与配置检查。
- 读取 oracle/verifier 的运行结果，验证任务是否可执行、是否能区分正确与错误答案。
- 将确定性检查和 LLM 评审放进同一个可审计的报告中。
- 让每个结论都带有文件路径、检查名称和证据，便于修复和复核。

## 当前架构

```text
task directory
      |
      v
deterministic checks -----> gate results
      |
      +---- trial artifacts -> execution checks
      |
      +---- optional LLM judge -> review findings
                                      |
                                      v
                              ReviewReport (JSON)
```

默认支持 Harbor/Terminal-Bench 常见的任务文件：`task.toml`、`README.md`、`environment/`、`solution/` 和 `verifier/`。

## 快速开始

```bash
python -m benchmark_review_agent.cli review ./path/to/task --output review.json
```

也可以直接使用模块入口：

```bash
PYTHONPATH=src python -m benchmark_review_agent.cli review ./path/to/task
```

如果要接入大模型，提供一个实现 `LLMJudge` 协议的适配器，并通过 `ReviewPipeline(..., judge=adapter)` 注入。项目刻意不绑定某一家模型供应商。

## 设计原则

1. **确定性检查先行**：格式、路径、元数据和运行产物等问题不交给模型猜测。
2. **模型结论必须可追溯**：模型输出只能增加 finding，不能覆盖硬性 gate 结果。
3. **失败可分级**：`blocker` 会阻止合并，`warning` 需要人工确认，`info` 只做记录。
4. **不上传任务数据**：默认 CLI 只在本地读取任务目录和生成 JSON 报告。

## 开发

```bash
python -m pytest
```

详见 [docs/architecture.md](docs/architecture.md)。

