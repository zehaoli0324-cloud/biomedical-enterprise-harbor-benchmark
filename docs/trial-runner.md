# Trial Runner 前置工程说明书

本文说明如何把一个已经通过任务契约和 verifier 校准的 benchmark 交给真实模型执行，并保存可比较、可审计的 trial 结果。

当前实现是 provider-neutral 的命令型 runner。它不绑定 OpenAI、Anthropic 或本地模型 SDK；具体模型由一个外部 adapter command 调用。runner 负责任务材料、工作目录、日志、verifier 和归档。

当前目标模型 trial 使用 GPT-5.6。接入方式是本机已登录的 Codex CLI，adapter 位于 [`benchmark_runner/adapters/codex_gpt55.py`](../benchmark_runner/adapters/codex_gpt55.py)，支持 `gpt-5.5`、`gpt-5.6` 和 `gpt-5.6-sol`。本项目的 Codex CLI adapter 只用于本地 calibration run，正式批量运行仍应使用 Docker/Harbor 隔离和固定凭据策略。

## 1. 当前实现范围

已经实现：

- 从任务目录复制 `instruction.md` 和 `data/` 到 agent-visible workspace；
- 不把 `verifier_only/`、`verifier.py` 和 `tests/` 复制给 Agent；
- 生成 `manifest.json`，记录 task、trial、输入文件 hash 和隔离边界；
- 通过统一的 `BENCHMARK_*` 环境变量启动外部 Agent adapter；
- 捕获 stdout、stderr 和进程级 JSONL transcript；
- 支持超时并归档 timeout 状态；
- 在 Agent 结束后从 runner 侧调用 hidden verifier；
- 保存 verifier JSON、退出码、分数和输出文件 hash；
- 通过测试验证正常、verifier 失败和 timeout 三类路径。

实现入口：

- runner CLI：[`benchmark_runner/cli.py`](../benchmark_runner/cli.py)
- trial 执行：[`benchmark_runner/runner.py`](../benchmark_runner/runner.py)
- 输入复制与 hash：[`benchmark_runner/files.py`](../benchmark_runner/files.py)
- 数据模型：[`benchmark_runner/models.py`](../benchmark_runner/models.py)
- runner 测试：[`benchmark_runner/tests/test_runner.py`](../benchmark_runner/tests/test_runner.py)

## 2. 重要安全边界

当前版本同时提供两种 backend：`process` 是本机预检模式，隔离模式为 `process_cwd_only`；`docker` 是正式运行的隔离基线。Docker backend 只挂载 `instruction.md` 和 `data/` 为只读、`outputs/` 和事件日志为可写，默认 `--network none`、只读根文件系统、丢弃 capabilities、禁止提权、限制 CPU/内存/PID。

因此当前版本适合：

- 本地预检；
- 合成小数据校准；
- 低风险模型 adapter 集成；
- 验证任务、verifier 和归档格式。

Enterprise trial 的 process backend 只证明模型能否在 agent-visible workspace 中完成任务；它不是 TB-Science 所要求的 separate verifier mode。正式结论还必须在 verifier 独立环境中重放，确保 Agent 无法读取 verifier、测试文件或 hidden reference，也无法在 verifier 阶段修改提交产物。

Docker backend 需要本机 Docker daemon 或 Harbor execution environment。若 daemon 不可用，runner 不会伪装成已完成隔离运行。`manifest.json` 会记录当前执行层：

```json
{
  "isolation_mode": "process_cwd_only",
  "network_policy": "off_requested",
  "network_enforcement": "caller_or_container_required"
}
```

Docker backend 的命令构造和镜像基线见 [`docker_backend.py`](../benchmark_runner/docker_backend.py) 与 [`docker/agent-base.Dockerfile`](../docker/agent-base.Dockerfile)。当前 Docker 镜像只是最小 Python agent 基线；要在容器内运行 GPT-5.5，需要把模型 adapter 和合法的凭据注入策略构建进专用镜像，不能把宿主机的 Codex OAuth 状态直接复制进去。

## 3. 运行前预检

以第一个 vertical slice 为例：

```bash
python3.11 -m benchmark_builder.cli validate \
  config/examples/literature-screening-m1-001.toml

python3.11 -m benchmark_builder.cli score \
  config/examples/literature-screening-m1-001.toml

python3.11 -m benchmark_builder.cli compile \
  config/examples/literature-screening-m1-001.toml \
  --out /tmp/literature-screening-compiled
```

然后创建一个只包含 Agent 可见文件的 trial workspace：

```bash
python3.11 -m benchmark_runner.cli prepare \
  benchmarks/literature-screening-m1-001 \
  --out /tmp/benchmark-runs/literature-screening-m1-001 \
  --trial-id trial-preflight-001
```

trial 输出必须放在任务所属 Git 仓库之外。否则进程级 Agent 可能通过当前目录的父路径看到仓库文件，破坏 agent-visible 边界；runner 会主动拒绝仓库内的 `--out` 路径。Docker backend 即使使用外部输出目录也应保持这一约束。

预检完成后，目录中应有：

```text
runs/literature-screening-m1-001/trial-preflight-001/
├── agent_workspace/
│   ├── instruction.md
│   ├── data/
│   └── outputs/
├── manifest.json
└── prompt.md
```

`agent_workspace/` 中不应出现：

```text
verifier_only/
verifier.py
tests/
```

## 4. Adapter 接口

runner 通过命令启动外部 adapter。adapter 必须从环境变量读取路径：

| 环境变量 | 含义 |
| --- | --- |
| `BENCHMARK_TASK_ID` | 任务 ID |
| `BENCHMARK_TRIAL_ID` | trial ID |
| `BENCHMARK_WORKSPACE` | Agent 当前工作目录 |
| `BENCHMARK_OUTPUTS` | 必须写入最终产物的目录 |
| `BENCHMARK_PROMPT` | `instruction.md` 的副本 |
| `BENCHMARK_EVENT_LOG` | 可选的 adapter 结构化事件日志路径 |
| `BENCHMARK_NETWORK_POLICY` | 当前值为 `off_requested`，不是强制防火墙 |

默认情况下 runner 不把宿主机的 API key 传给 adapter。需要调用远程模型时，必须显式传递变量名：

```bash
python3.11 -m benchmark_runner.cli run \
  benchmarks/literature-screening-m1-001 \
  --out /tmp/benchmark-runs/literature-screening-m1-001 \
  --command 'python3.11 /absolute/path/to/model_adapter.py --model MODEL_NAME' \
  --pass-env OPENAI_API_KEY
```

manifest 只保存 `OPENAI_API_KEY` 这个变量名，不保存变量值。不要把 API key 写进 `--command`、task 文件或 trial 目录。

adapter 的职责是：

1. 把 `BENCHMARK_PROMPT` 传给具体模型；
2. 根据模型协议提供允许的工具；
3. 将模型要求的文件写入 `BENCHMARK_OUTPUTS`；
4. 将工具调用或结构化事件写入 `BENCHMARK_EVENT_LOG`；
5. 模型完成后正常退出；
6. 如果模型或 API 出错，返回非零退出码。

runner 不假设模型会自动生成正确的文件，也不会把自然语言回答转换成结构化 artifact。输出契约必须由 Agent adapter 或模型自己完成。

## 5. 启动一次真实模型 trial

GPT-5.6 calibration trial 使用本机 Codex CLI adapter：

```bash
python3.11 -m benchmark_runner.cli run \
  benchmarks/literature-screening-m1-001 \
  --out /tmp/benchmark-runs/literature-screening-m1-001 \
  --trial-id trial-gpt56-codex-001 \
  --timeout 600 \
  --command 'python3.11 /absolute/path/to/benchmark_runner/adapters/codex_gpt55.py --model gpt-5.6-sol'
```

The runner changes the agent process working directory to the copied task
workspace. Use an absolute adapter path (or an installed console entry point);
`python -m benchmark_runner...` and repository-relative adapter paths may fail
before the model starts because the package is no longer on `sys.path`.

正式隔离 backend 的启动形式：

```bash
python3.11 -m benchmark_runner.cli run \
  benchmarks/literature-screening-m1-001 \
  --out runs/literature-screening-m1-001 \
  --trial-id trial-gpt56-docker-001 \
  --backend docker \
  --docker-image research-benchmark-agent:py311 \
  --docker-network none \
  --docker-cpus 2 \
  --docker-memory 1g \
  --timeout 600 \
  --command 'python3 /adapter/codex_gpt55.py --model gpt-5.6'
```

该 Docker 命令要求镜像内已经存在 adapter 和模型访问凭据策略；本仓库不会把 Codex 登录态或 API key 打包进镜像。

runner 会执行：

```text
prepare workspace
  -> start adapter
  -> capture stdout/stderr
  -> wait or timeout
  -> run benchmarks/literature-screening-m1-001/verifier.py
  -> save verifier_result.json
  -> update manifest.json
```

返回状态包括：

| 状态 | 含义 |
| --- | --- |
| `pass` | Agent 正常退出且 verifier 通过 |
| `verifier_fail` | Agent 正常退出，但产物未通过 verifier |
| `agent_error` | Agent 命令非零退出或无法启动 |
| `timeout` | 超过 runner timeout |
| `infrastructure_error` | verifier 或归档基础设施异常 |

分析 trial 时要区分 `agent_not_run`、`agent_completed_verifier_failed` 和
`agent_completed_verifier_passed`。只有模型正常退出、产物已归档、且先排除
instruction/verifier 合同缺陷后，`verifier_fail` 才能作为模型能力或任务难度证据。

## 6. Trial 归档结构

一次完整运行应形成：

```text
trial-20260918T120000Z/
├── agent_workspace/
│   ├── instruction.md
│   ├── data/
│   └── outputs/
├── prompt.md
├── manifest.json
├── stdout.log
├── stderr.log
├── transcript.jsonl
├── agent_events.jsonl       # adapter 提供时
├── verifier_stdout.log
├── verifier_stderr.log
└── verifier_result.json
```

trial 结果默认留在 `/tmp/benchmark-runs/` 或对象存储，不应未经数据许可直接提交到代码仓库。仓库中的 `runs/` 仍加入 `.gitignore`，但忽略规则不是隔离措施。

## 7. 当前 runner 还没有做的事情

这些能力不能假装已经完成：

1. **供应商 API 适配器**：GPT-5.6 的本机 Codex CLI adapter 已完成；Docker 内的凭据注入、API adapter 和 token/cost 统计仍需单独配置。
2. **Docker daemon/Harbor 实跑**：Docker 命令构造已完成，但必须在有 Docker socket 权限的机器上 smoke test；Harbor adapter 仍未实现。
3. **资源限制审计**：Docker 已声明 CPU、内存、PID 和 timeout；磁盘配额、子进程树回收和宿主机审计仍需作业层补充。
4. **工具调用语义解析**：当前 transcript 记录进程输出；真正的 tool call、tool result、退出码和参数需要 adapter 写入结构化事件。
5. **并行和重试策略**：目前一次 CLI 调用执行一个 trial；批量运行、退避和失败重试需要单独的 job layer。
6. **trial 统计分析**：尚未自动计算多次运行的一致性、置信区间、成本和模型间显著差异。
7. **失败 taxonomy 自动标注**：当前需要根据 transcript 和 verifier 结果人工或由后续 reviewer agent 标注 F2/F3/F9/F12 等类别。

## 8. 校准顺序

真实模型接入应按以下顺序进行：

```text
golden submission
  -> verifier mutation tests
  -> runner prepare test
  -> fake adapter run
  -> keyword baseline
  -> one real model trial
  -> three repeated trials
  -> multiple models/configurations
  -> transcript failure annotation
  -> expert review
  -> task difficulty calibration
```

当前仓库已经完成前四步的代码基础：任务有 hidden reference，verifier 有正常和故意失败测试，runner 有 prepare、正常进程、verifier failure 和 timeout 测试。下一步应实现一个具体模型 adapter，并先跑一次单模型 trial；在单模型 trial 的归档和隔离都正确之前，不应批量比较模型。

对于使用 `verifier_only/reference.json` 且 verifier 返回 `{passed: bool}` 的企业校准题，runner 现在同时支持 `reference_labels.json` 和 `reference.json`，并会把 `passed` 归一化为标准 `status`。作者侧的四个非模型基线可用以下命令运行；它们不会访问 agent workspace，也不会被计入目标模型结果：

```bash
python3 scripts/run_enterprise_baselines.py
```

该命令只把参考解、简单合法、始终弃答和模板/关键词基线写入任务质量记录，目标模型仍保持 `NOT_RUN`。

历史 GPT-5.5 校准结果见 [`docs/trial-calibration-001.md`](trial-calibration-001.md)。其中明确区分了 adapter 启动错误、workspace 隔离错误、任务契约问题和模型实际筛选结果。GPT-5.6 的每次 trial 必须另存独立目录和 manifest，不得覆盖历史记录。
