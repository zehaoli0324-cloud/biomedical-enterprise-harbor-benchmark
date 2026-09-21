# Enterprise Harbor 出题 SOP V1.1

这份 SOP 是企业题从候选到 Harbor trial 的强制门禁。`compiled`、`CALIBRATED` 或静态 schema 通过都不等于可以跑 target model，更不等于 `READY_FOR_HARBOR`。

## 1. 先冻结来源和决策合同

每道题必须绑定 source ledger、公共数据/文献 registry、版本或 accession、下载入口、文件级 SHA-256、许可证和 transformation manifest。公开数据只能支持公开声明；不能把公开 workflow 或 benchmark 说成企业内部生产数据。

题目合同至少冻结：角色、业务决策、独立单位、输入字段/单位/主键、split 和可见性、required outputs、失败注入、停止/人工 handoff、claim boundary、等价答案和容差。

## 2. 题包边界

Agent 只能看到 `instruction.md`、`data/` 和可写的 `outputs/`。`verifier.py`、`tests/`、`verifier_only/reference.json` 只能在 verifier 侧使用。`instruction.md` 必须逐项写出每个 `outputs/...` 路径、字段、单位、排序、主键和允许的等价表示。

verifier 不得只接受一个隐藏答案，除非题面明确声明唯一目标、方向和 tie-break；合法替代答案应按约束、性质和容差评分。claim boundary 应检查结构化字段，而不是依赖题面未声明的固定短语。

## 3. 四类控制和五类 trial

控制计划至少包含 `positive`、`negative`、`invariance`、`insufficient_evidence`，并记录单因素变更和校准结果。模型前固定执行：

1. `reference_solution`
2. `simple_legal_baseline`
3. `always_abstain`
4. `template_or_keyword`
5. `target_model`

每一项都必须有明确状态；未执行就是 `NOT_RUN`。`reference_solution` 证明题可解，不能代替独立 verifier；`always_abstain` 不能被 verifier 错误奖励；template/keyword 用来查捷径。

## 4. 模型前 contract audit

第一次真实模型调用前，运行：

```bash
python3 scripts/check_enterprise_harbor_sop.py \
  benchmarks/<task-id> \
  --output reports/<task-id>-enterprise-sop-preflight.json
```

随后运行与模型无关的 verifier/contract audit。至少确认：独立领域专家按 instruction 产出的语义正确答案能通过；空输出、乱序、重复、单位错误、越界 claim 和证据不足能失败或转人工；oracle 与 nop 在独立 verifier 环境中完成。process-only 只能是预检。

preflight 的 `status=PASS` 只表示题包合同允许进入 target-model trial；发布仍要读取独立的 `release_status` 和 `release_blockers`。因此 `target_model=NOT_RUN` 不阻止首次 trial，但会继续阻止发布。

若出现 `enterprise-output-path-undocumented`、`enterprise-output-schema-missing`、`enterprise-verifier-phrase-undocumented` 或 `enterprise-single-answer-contract`，状态必须回退到 `CONTRACT_ONLY`，先修 instruction/verifier。

## 5. 失败归因和发布状态

模型 trial 失败必须按最早可定位节点归因：

- `agent_not_run`：provider、认证、容器或 runner 在生成前失败，不计入难度；
- `agent_completed_verifier_failed`：模型正常退出但 verifier 拒绝，必须回放 artifact 并检查合同一致性；
- `agent_completed_verifier_passed`：模型完成且通过，仍要查捷径和信息泄漏。

`TIMEOUT_INFRASTRUCTURE`、认证失败、容器未启动、artifact 未收集均是基础设施 blocker，不得写成“模型答错”或“题目足够难”。

状态只能按以下顺序推进：

```text
SOURCE_OBSERVED -> REQUIREMENTS_REVIEWED -> CANDIDATE_SET
-> SELECTED -> CONTRACT_ONLY -> CALIBRATION_READY
-> EVAL_ONLY_UNTIL_CALIBRATED -> MODEL_TRIAL_COMPLETE -> READY_FOR_HARBOR
```

`READY_FOR_HARBOR` 还需要来源/许可证/隐私、企业价值、独立 truth/verifier、四类控制、五类 trial、重放和 claim review 的独立证据。任何缺项都保持 `BLOCKED` 或 `REVIEW_REQUIRED`。

## 6. 当前批次的处理结论

本仓库当前两道新 mined task 的 reference 和控制已完成，但 target model 为 `TIMEOUT_INFRASTRUCTURE`，所以只能标记为 `BLOCKED`，不能从该结果推断 GPT 难度，也不能晋级 Harbor。先完成 preflight 和独立 verifier audit，再重跑 target model。
