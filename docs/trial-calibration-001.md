# GPT-5.5 Trial Calibration 001

这是 `literature-screening-m1-001` 的第一次真实模型校准记录。模型固定为 `gpt-5.5`，通过本机已登录的 Codex CLI adapter 执行。模型使用的是合成冻结数据，不代表真实文献筛选能力的最终结论。

## 有效试跑

| 项目 | 值 |
| --- | --- |
| task | `literature-screening-m1-001` |
| model | `gpt-5.5` |
| adapter | `benchmark_runner/adapters/codex_gpt55.py` |
| trial | `trial-gpt55-codex-004` |
| workspace | `/private/tmp/benchmark-runs/literature-screening-m1-001/trial-gpt55-codex-004` |
| execution backend | `process_cwd_only`，仓库外 workspace |
| raw runner result | `verifier_fail`, score `97.5` |
| calibrated verifier result | `pass`, score `100.0` |

重新评分不是修改模型输出，而是修正了 verifier 对公开允许的 `LIT-001` reason-code alias 的处理；原始 `verifier_result.json` 应保留，重评分结果另存为 `verifier_result.recalibrated.json`。

## 结果摘要

- 8/8 screening decisions 正确；
- `include`、`exclude`、`context_only` 和 `uncertain` 四类决策均被正确使用；
- `LIT-005` DOI 重复、`LIT-003` 相关性证据和 `LIT-007` 不确定队列均处理正确；
- evidence source coverage、uncertainty queue 和 input checksum 均通过；
- 首轮暴露了任务契约必须明确 numeric confidence、公开 reason-code 集合和 Markdown heading 规则。

## 失效 trial

- `trial-gpt55-codex-001`：adapter 把 Codex 全局参数放在 `exec` 子命令后，模型未启动；属于 adapter 基础设施错误。
- `trial-gpt55-codex-002`：模型完成了任务，但 workspace 位于仓库内，暴露了父级 Git 文件可见性问题；不能作为有效成绩。
- `trial-gpt55-codex-003`：workspace 已移到仓库外，但旧任务契约没有明确 confidence 和 reason-code 格式，模型科学决策正确而 verifier 过度惩罚；作为契约校准证据保留。

## 下一步

1. 在 Docker daemon 有权限的机器上使用同一任务和 GPT-5.5 重跑，确认 `--network none`、只读输入挂载和资源限制真实生效。
2. 在同一版本任务上重复至少 3 次，报告决策稳定性、artifact 稳定性和成本/耗时。
3. 对公开真实文献快照做 provenance 和许可复核后，再替换当前合成输入。
4. 只有 Docker/Harbor 隔离和重复 trial 都通过后，才把结果纳入正式 benchmark calibration。
