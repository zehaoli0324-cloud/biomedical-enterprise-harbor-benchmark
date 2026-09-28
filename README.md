# Biomedical Enterprise Harbor Benchmark

把生物医药企业公开可核验的研发、分析和统计编程工作流，转换成可运行、可审计、可复现的 Harbor 题包。

这里的核心对象不是“一个数据集 + 一段 prompt”，而是一条可以被复核的决策链：来源证据 -> 业务场景 -> 候选决策 -> 输入和输出合同 -> 隐藏真值与 verifier -> 控制校准 -> 模型 trial -> Harbor 发布门。

## 先看当前进展

当前仓库处于 `knowledge-base + synthetic calibration` 阶段。公开来源、企业价值、难度和训练价值已经登记，但合成 fixture 不能冒称企业内部数据，未完成的模型 trial 不能冒称难度证据。

最近一轮 seed mining 已发现 4 个新的语义候选：

| 候选 | 决策轴 | 当前状态 | 进展入口 |
| --- | --- | --- | --- |
| `eb003-replay-provenance-004` | 交付后 provenance/environment 是否支持 replay | controls calibrated；target model infrastructure blocked | [brief](candidate_pools/enterprise-v1/question_briefs/eb003-replay-provenance-004.json)、[task](benchmarks/eb003-replay-provenance-004/) |
| `eb009-diversity-coverage-004` | synthesis handoff 前的 scaffold/chemical-space coverage | controls calibrated；target model infrastructure blocked | [brief](candidate_pools/enterprise-v1/question_briefs/eb009-diversity-coverage-004.json)、[task](benchmarks/eb009-diversity-coverage-004/) |
| `eb006-signal-noise-004` | profile handoff 前 signal 与 plate/technical noise 是否可辨识 | controls/baselines complete；contract revised；target rerun infrastructure blocked | [brief](candidate_pools/enterprise-v1/question_briefs/eb006-signal-noise-004.json)、[task](benchmarks/eb006-signal-noise-004/) |
| `eb010-measurement-value-004` | next batch 前应优先请求哪项 measurement | controls/baselines/audit complete；target unchanged artifacts pass after verifier contract replay；fixed-container replay pending | [brief](candidate_pools/enterprise-v1/question_briefs/eb010-measurement-value-004.json)、[task](benchmarks/eb010-measurement-value-004/) |
| `TRANCHE-005` | L4 难度升级：恢复、层级 normalization、route portfolio、两阶段 batch、measurement request、cross-handoff | 6/6 gpt-5.6-sol target trials pass after explicit-contract replay；未显示模型区分度；fixed-container/practitioner review pending | [tranche](candidate_pools/enterprise-v1/scale_tranche_005.json)、[difficulty modules](docs/enterprise-difficulty-escalation-v1.md) |
| `TRANCHE-006` | L5 闭环 policy replay：时间因果、预算、未来结果防泄漏和跨 seed 稳定性 | controls calibrated；gpt-5.6-sol 本地 trial 经 verifier contract replay 通过；固定容器 replay 和 practitioner review 未完成 | [tranche](candidate_pools/enterprise-v1/scale_tranche_006.json)、[task](benchmarks/eb010-closed-loop-replay-003/) |
| `TRANCHE-007` | L5.1 低披露 nested discovery、agent 自主 capability subgraph、语义含糊、保守升级和离线 provenance | 1 个 synthetic package；v0.7.1 contract audit passed；target-model self-planned clean first-pass trial | [tranche](candidate_pools/enterprise-v1/scale_tranche_007.json)、[task](benchmarks/eb010-closed-loop-ambiguity-004/) |
| `TRANCHE-008` | L5.2 自适应策略树、硬约束门和逐情景 minimax regret | controls/baselines/audit complete；gpt-5.6-sol formal trial passed；未考倒目标模型；fixed-container/practitioner review pending | [tranche](candidate_pools/enterprise-v1/scale_tranche_008.json)、[task](benchmarks/eb010-adaptive-policy-regret-005/) |
| `TRANCHE-009` | L5.3 分布漂移、weighted lower-tail CVaR、profile regret 和敏感性 replay | controls/baselines/audit complete；gpt-5.6-sol unchanged-artifact contract replay passed；未考倒目标模型 | [tranche](candidate_pools/enterprise-v1/scale_tranche_009.json)、[task](benchmarks/eb010-distributional-policy-stress-006/) |
| `TRANCHE-010` | L5.4 recovery -> normalization -> route -> policy 的跨阶段 claim/provenance handoff | controls/baselines/audit complete；gpt-5.6-sol unchanged-artifact contract replay passed；未考倒目标模型 | [tranche](candidate_pools/enterprise-v1/scale_tranche_010.json)、[task](benchmarks/eb012-cross-stage-chain-002/) |
| `TRANCHE-011` | L5.5 evidence retraction、checkpoint replay、shared-lot 和 maximin portfolio | controls/baselines/audit complete；gpt-5.6-sol unchanged-artifact contract replay passed；未考倒目标模型 | [tranche](candidate_pools/enterprise-v1/scale_tranche_011.json)、[task](benchmarks/eb012-revocation-portfolio-003/) |
| `TRANCHE-012` | L6 低披露 evidence routing：依赖图、相关证据、共享预算、未来结果边界与自主停止 | mixed valid evidence：一次 minimax scientific failure；一次正确 route 但 delivery contract replay pass；fixed-container/practitioner review pending | [tranche](candidate_pools/enterprise-v1/scale_tranche_012.json)、[task](benchmarks/eb013-evidence-budget-routing-001/) |
| `TRANCHE-013` | 复用 minimax evidence-route 模块：二阶段 observation policy、stop/uncertainty handoff、reproduction manifest | EB013-002 已物化并通过结构/模块校验；EB010 stop 与 EB011 reproduction 作为 held-out contract candidates | [tranche](candidate_pools/enterprise-v1/scale_tranche_013.json)、[reusable module](config/reusable_difficulty_modules.json)、[task](benchmarks/eb013-evidence-budget-routing-002/) |
| `TRANCHE-014` | L6.2 跨域 transfer batch：二阶段 evidence policy、minimax residual、stop uncertainty 与 reproduction drift | EB010/EB011 scientific route 通过 contract replay；EB013-002 同一产物经 verifier canonicalization 修复后 replay 通过；fixed-container/practitioner review pending | [tranche](candidate_pools/enterprise-v1/scale_tranche_014.json)、[stop task](benchmarks/eb010-stop-uncertainty-002/)、[reproduction task](benchmarks/eb011-reproduction-manifest-001/) |
| `EB013-004` | L6.3 信息边界、共享准备、分布压力、来源时间与相关证据的联合优化 | 18 controls + 8 variants complete；两次 gpt-5.6-sol frozen local trial 均 RAW_PASS；未考倒目标模型，下一版需新增 primary difficulty axis | [task](benchmarks/eb013-observation-boundary-004/)、[difficulty analysis](docs/enterprise-difficulty-escalation-v1.md) |

TRANCHE-014 author bundle: `/private/tmp/l6.2-transfer-tranche-014-v6.tar.gz`，SHA-256 为 `6cb382fc53bb527174f35e7aa1424a176c44ca5f1c95feb3b5928dd6df77409c`，包含 93 个校验过的 payload 文件；该归档仍标记为 `release_status=BLOCKED`。

本轮新增难度模块 `math_minimax_evidence_route_selection`：模型必须先最小化所有有效路线中的最大关键残差，再按成本和 lexical IDs tie-break；“刚好跨过阈值”不是停止条件。该模块已登记在 [module catalog](config/module_catalog.json)，并由 EB013 的 target trial 产生了可归因的 threshold-satisficing failure。

EB013 author-side bundle: `dist/l6-evidence-budget-routing-013.tar.gz`，SHA-256 为 `35bda1e775638c28163e6c5420ba00fa52a7cd97ab5f0be75a8d8efb0ecd2825`，包含 45 个校验过的 payload 文件；该归档仍标记为 `release_status=BLOCKED`。

当前 [contract manifest](candidate_pools/enterprise-v1/contracts/manifest.json) 已注册 26 个 enterprise/calibration task；每题编译结果汇总在 [batch_compile_report.json](candidate_pools/enterprise-v1/contracts/batch_compile_report.json)。前两道 mined task 的进展见 [scale_tranche_002.json](candidate_pools/enterprise-v1/scale_tranche_002.json)，EB006 的合同修订和 trial 归因见 [scale_tranche_003.json](candidate_pools/enterprise-v1/scale_tranche_003.json)，EB010 measurement-value 的完整推进记录见 [scale_tranche_004.json](candidate_pools/enterprise-v1/scale_tranche_004.json)，L4 难度升级批次见 [scale_tranche_005.json](candidate_pools/enterprise-v1/scale_tranche_005.json)，L5 闭环 replay 批次见 [scale_tranche_006.json](candidate_pools/enterprise-v1/scale_tranche_006.json)，L5.1 低披露语义 discovery 批次见 [scale_tranche_007.json](candidate_pools/enterprise-v1/scale_tranche_007.json)，L5.2 adaptive policy regret 批次见 [scale_tranche_008.json](candidate_pools/enterprise-v1/scale_tranche_008.json)，L5.3 distributional stress 批次见 [scale_tranche_009.json](candidate_pools/enterprise-v1/scale_tranche_009.json)，L5.4 跨阶段 handoff 批次见 [scale_tranche_010.json](candidate_pools/enterprise-v1/scale_tranche_010.json)，L5.5 revocation portfolio 见 [scale_tranche_011.json](candidate_pools/enterprise-v1/scale_tranche_011.json)，L6 evidence routing 见 [scale_tranche_012.json](candidate_pools/enterprise-v1/scale_tranche_012.json)，L6.2 跨域 transfer batch 见 [scale_tranche_014.json](candidate_pools/enterprise-v1/scale_tranche_014.json)。`TIMEOUT_INFRASTRUCTURE`、认证、容器和 artifact 收集失败都只算基础设施阻塞，不算模型难度。

本仓库新增的总门禁是 [Enterprise Harbor SOP V1.1](docs/enterprise-harbor-sop-v1.1.md) 和 [check_enterprise_harbor_sop.py](scripts/check_enterprise_harbor_sop.py)。它把 `pretrial PASS` 和 `release BLOCKED` 分开：题包可以进入 target-model trial，不代表可以发布到 Harbor。

## 一张架构图

```text
公开来源 / 论文 / 数据卡 / workflow
             |
             v
knowledge_base + data/public_data_literature_registry.json
             |
             v
source ledger + REQ01-REQ14 + scenario card
             |
             v
candidate_pools/enterprise-v1/  (3-5 个语义不同候选)
             |
             v
question brief -> contract TOML -> benchmark_builder 编译
             |
             v
benchmarks/<task-id>/
  instruction.md + data/ + outputs/       agent 可见/可写
  verifier.py + tests/ + verifier_only/   runner/judge 私有
  quality/ + controls/                    author-side 质量证据
             |
             v
preflight -> independent contract audit -> controls -> baselines
             |
             v
target-model trial -> Harbor/Docker replay -> review/release gate
```

## 每个部分怎么工作

### 1. `knowledge_base/`：来源和设计知识

这里不存“模型认为可信的摘要”，而存可追溯的来源记录：官方 URL、版本/commit、访问日期、许可证、证据定位和声明边界。

- `knowledge_base/seeds/official_sources.json` 是 seed mining 的入口。
- `knowledge_base/harvest/` 保存来源 harvest 的原始和规范化记录。
- `knowledge_base/registry/public_benchmark_requirements.json` 把来源中反复出现的要求整理成 REQ01-REQ14。
- `knowledge_base/draft_bundles/` 保存来源、workflow、transformation、evaluation、risk、review 等卡片。

这里解决“题目从哪里来、能声称什么、哪些字段还没核验”，不直接生成可运行题包。校验命令：

```bash
python3 scripts/validate_knowledge_base.py
```

### 2. `data/`：公共数据和文献证据注册表

`data/public_data_literature_registry.json` 记录可下载数据、数据论文、科学主张、公式/计算方法、accession、下载入口、citation 和哈希。合成或手工 fixture 必须标记为 calibration，不能把真实性等级 A/B/C/W/S 当作 accession 或实验真值的替代品。

### 3. `candidate_pools/`：从 seed 挖掘决策差异

`candidate_pools/enterprise-v1/` 是候选矩阵的工作区：

- `source_ledger.json`：候选与来源、证据等级和许可的连接。
- `question_briefs/`：每个候选的业务角色、独立单位、handoff、失败注入、required artifacts 和 GPT 难度机制。
- `EBxxx-...-candidate-set.json`：同一来源的候选集合，要求 3-5 个真正不同的决策，不接受只改文件名、格式、随机种子或 prompt 长度。
- `contracts/*.toml`：把选中的候选映射到难度模块、资源约束、scenario card 和 evidence registry。
- `compiled/`：编译后的 manifest、difficulty report 和 evaluation protocol。
- `seed_mining_report.json`：记录扫描了哪些旧 seed、拒绝了哪些 surface-only variant、发现了哪些新语义轴。

候选矩阵校验：

```bash
python3 scripts/validate_candidate_matrix.py candidate_pools/enterprise-v1
```

### 4. `config/` 和 `benchmark_builder/`：把决策合同编译成可比较配置

`config/module_catalog.json` 定义可复用的 scenario、judgment、compute、tooling、noise、data、environment、math、horizon 和 safety 模块。每个 TOML 必须覆盖全部 difficulty dimension，并链接一个 scenario card。

`benchmark_builder/` 负责解析 TOML 和 scenario card、检查模块类别和 evidence registry、计算可解释的 difficulty score，并生成 `task_manifest.json`、`difficulty_report.md` 和 `evaluation_protocol.json`。编译不是题目可运行证明，只说明合同和难度配置完整：

```bash
python3 scripts/compile_contract_batch.py
```

### 5. `benchmarks/<task-id>/`：真正运行的 enterprise task

每道题必须把 agent 可见内容和 judge 私有内容分开：

```text
benchmarks/<task-id>/
├── task.yaml                    # ID、输入边界、required_outputs、资源和网络
├── scenario-card.yaml            # 业务决策、handoff、错误后果和停止规则
├── instruction.md                # agent 唯一说明；逐项写 outputs/ 路径和字段
├── data/                         # 冻结的 agent-visible fixture
├── outputs/                      # agent 可写的提交目录
├── verifier.py                   # 独立重算和等价答案检查
├── tests/                        # verifier、空输出、负例和控制测试
├── verifier_only/reference.json  # 隐藏真值，只给 verifier/author runner
├── controls/                     # 四类控制结果
└── quality/                      # author-side 质量和状态卡
```

`instruction.md` 不能暴露 `verifier.py`、`tests/`、`verifier_only/`，也不能依赖题面没有声明的固定短语。`verifier.py` 不能只比较一个隐藏答案，除非题面明确声明唯一目标和 tie-break；它还必须拒绝空输出、乱序/重复、单位错误、provenance 错误、越界 claim 和证据不足。

### 6. `quality/`：发布前的 author-side 证据

质量卡说明“为什么这道题值得做、现在走到哪一步”：

- `candidate_set_card.json`：候选数量、语义轴和选优门。
- `enterprise_value_card.json`：角色、业务决策、下游接收者、错误代价和人审 owner。
- `control_plan_card.json`：四类控制和单因素变更策略。
- `difficulty_card.json`：状态依赖、竞争性选择、失败机制和捷径探针。
- `training_value_card.json`：错误标签、反馈粒度、留出轴和污染控制。
- `model_trial_card.json` / `model_trial_results.json`：五类策略的运行状态和失败归因。
- `sop_card.json`：SOP 版本、contract status、control status、独立 verifier audit 和 release blockers。

四类控制分别证明合法答案可过、错误答案会失败、无关表示不影响判断、证据不足时会弃答或转人工。

### 7. `scripts/`：每个门的可重复命令

- `validate_knowledge_base.py`：来源和质量卡完整性。
- `validate_candidate_matrix.py`：候选差异和状态边界。
- `compile_contract_batch.py`：TOML -> compiled contract。
- `check_enterprise_harbor_sop.py`：题包结构、输出合同、控制、baseline、独立 verifier audit 和发布阻塞。
- `run_*controls.py`：四类控制。
- `run_*baselines.py`：reference、simple legal、always abstain、template/keyword。
- `materialize_*.py`：把 brief 物化为 fixture、verifier、tests 和 quality cards。

题包进入 target-model trial 前运行：

```bash
python3 scripts/check_enterprise_harbor_sop.py \
  benchmarks/<task-id> \
  --output reports/<task-id>-enterprise-sop-preflight.json
```

`status=PASS` 只表示允许进入 target-model trial；`release_status=BLOCKED` 仍会阻止 Harbor 发布。

### 8. `benchmark_runner/`：模型 trial 和 artifact 归因

runner 创建隔离工作区、挂载 agent-visible 输入、执行模型、保存输出并运行 verifier。正式隔离使用 Docker/Harbor；process-only 只是本机预检。

固定比较五种策略：`reference_solution`、`simple_legal_baseline`、`always_abstain`、`template_or_keyword`、`target_model`。失败分为 `agent_not_run`、`agent_completed_verifier_failed`、`agent_completed_verifier_passed`。超时、认证失败、容器未启动、artifact 未收集是 infrastructure blocker，不能当作“题目难”。

### 9. Harbor 发布门

```text
SOURCE_OBSERVED -> REQUIREMENTS_REVIEWED -> CANDIDATE_SET
-> SELECTED -> CONTRACT_ONLY -> CALIBRATION_READY
-> EVAL_ONLY_UNTIL_CALIBRATED -> MODEL_TRIAL_COMPLETE -> READY_FOR_HARBOR
```

`READY_FOR_HARBOR` 必须同时有来源与关键 REQ 核验、企业价值复核、独立 truth/verifier、四类控制、五类 trial、独立 contract audit、许可证/隐私/claim review、固定容器回放和可重现 manifest。

## 从零开始的执行顺序

### A. 验证仓库和来源

```bash
python3 scripts/validate_knowledge_base.py
python3 scripts/validate_candidate_matrix.py candidate_pools/enterprise-v1
python3 -m pytest -q
```

### B. 选择或挖掘候选

先读 [scaled-question-generation.md](docs/scaled-question-generation.md)、[candidate-pipeline.md](docs/candidate-pipeline.md) 和 [enterprise-authoring-pipeline.md](docs/enterprise-authoring-pipeline.md)，再查看 `seed_mining_report.json` 和 question briefs。新候选必须能说明语义差异、独立单位、handoff、失败注入和 hidden truth route。

### C. 编译并物化题包

```bash
python3 scripts/compile_contract_batch.py
python3 scripts/materialize_mined_candidates.py
```

物化后先跑独立 contract audit：

```bash
PYTHONPATH=/path/to/benchmark-verification-agent/src \
python3 -m benchmark_review_agent.cli review \
  benchmarks/<task-id> --judge none
```

### D. 控制、baseline、trial

```bash
python3 scripts/run_mined_candidate_controls.py
python3 scripts/run_mined_candidate_baselines.py
```

只有 baseline 和 controls 清楚后，才启动 target model。结果写入 `quality/model_trial_results.json`，并保留原始 trial artifact、失败类型和重放命令。

## 重要文档索引

- [Enterprise Harbor SOP V1.1](docs/enterprise-harbor-sop-v1.1.md)：题包 preflight、contract audit、失败归因和发布门。
- [Enterprise authoring pipeline](docs/enterprise-authoring-pipeline.md)：企业题从来源到题包的详细任务书。
- [Scaled question generation](docs/scaled-question-generation.md)：批次选择、候选校验、合同编译和题包物化。
- [Trial runner](docs/trial-runner.md)：process/Docker runner、artifact 和结果归因。
- [Evaluation pipeline](docs/evaluation-pipeline.md)：solver、verifier、judge 和发布前评估。
- [Failure taxonomy](docs/failure-taxonomy.md)：输入、方法、工具、证据、claim boundary 和交付失败分类。
- [Public benchmark requirements](docs/public-enterprise-benchmark-requirements.md)：REQ01-REQ14 来源契约。
- [Enterprise value and GPT difficulty](docs/enterprise-value-and-gpt-difficulty.md)：企业价值、语义新意和模型难度的分离。
- [Current trial analysis](docs/trial-analysis-gpt56-sol-001.md)：已有模型 trial 和合同修订记录。
- [Reference factory SOP](https://github.com/zehaoli0324-cloud/harbor-science-bench-factory)：来源、oracle/nop、Docker replay 和 trial SOP。

## 真实性和安全边界

来源口径仅表示来源关系：`A` 企业真实实验/研发数据，`B` 企业发布或维护的公共 benchmark，`C` 联盟数据，`W` 企业公开 workflow/工具，`S` 合成或教学 fixture。无论哪一类，都还需要版本、哈希、许可证、隐私、隐藏真值和 claim boundary 审查。

当前仓库不声称拥有企业内部数据，不把公共 benchmark 的 leaderboard 当作隐藏真值，也不把一次模型失败当作科学结论。
