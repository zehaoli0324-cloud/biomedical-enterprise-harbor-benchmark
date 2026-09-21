# Enterprise workflow authoring pipeline

本流程的单一题包 preflight 入口是 `scripts/check_enterprise_harbor_sop.py`。它只判断结构和状态边界，不把静态通过升级为 Harbor 发布；每个 blocker 都必须进入题包报告并保留。

每个企业风格 benchmark 按以下顺序推进。任何一步证据不足，都应停留在 `candidate` 或 `needs-data`，不能仅靠补写题面进入 `ready`。

## 1. 来源与真实性

在 `data/enterprise_workflow_inventory.csv` 登记组织、来源链接或 accession、发布日期、版本、许可和真实性口径（A/B/C/W/S）。把企业参与、企业发布和企业真实实验分开记录。

同时在 `data/public_data_literature_registry.json` 登记可下载的公共数据、数据论文、科学背景主张和公式/计算方法。A/B/C/W/S 只描述来源真实性，不能替代 accession、下载入口、文件级 SHA-256、变换谱系和方法引用。未声明的合成、手工拼凑或无来源拼接数据只能被标记为工程 fixture，不能支持科学结论。

## 2. 场景卡

场景卡必须写清楚研究对象、业务决策、错误后果、跨步骤 handoff、必需产物和失败注入。每个科学判断都要能在输出或 verifier 中观察到。

## 3. 候选生成与选优

同一个 workflow 先生成多个不同的决策目标，例如预测、质量审计和闭环优化。先过确定性 hard gate，再由领域科学家、方法审计员和证据审计员独立评审；不要用单一总分掩盖安全或许可阻塞。

## 4. 任务契约

`instruction.md` 只描述 agent 可见输入、约束和输出 schema；隐藏真值、oracle 和 verifier 置于 `verifier_only/` 或隔离执行环境。任务必须声明网络、资源、随机性、版本和人工审核边界。

生产 TOML 可用以下门禁绑定证据注册表：

```toml
[evidence]
required = true
registry = "../../data/public_data_literature_registry.json"
```

编译器会验证 registry 的公开 accession、下载入口、citation 和 registry digest，并把 digest 写入 `task_manifest.json`。实际题包仍需另存下载文件清单、哈希和 transformation manifest。

### 4.1 Enterprise contract 任务布局

合成/校准型 enterprise task 使用以下最小目录合同：

```text
task.yaml
instruction.md
data/                         # agent-visible frozen fixture
verifier.py                   # runner-side verifier, never agent-visible
tests/                        # verifier and control tests
verifier_only/reference.json  # hidden truth, never mounted to the agent
```

`instruction.md` 必须明确任务目标、输入边界、required artifacts、停止/人工 handoff 和 claim boundary；不强制套用 Harbor 的 `Task/Solution/Verification` 标题。Agent workspace 只能包含 `instruction.md`、`data/` 和可写的 `outputs/`，不得复制 `verifier.py`、`tests/` 或 `verifier_only/`。

验证代理对 enterprise task 执行 fail-closed 检查：缺少 `verifier.py`、非空 `data/`、`tests/` 或 `verifier_only/reference.json` 时为 blocker；结构检查通过不代表科学复核、许可证复核或模型试跑已经完成。

## 5. 参考解和 verifier

参考解用于确认任务可解，不等于真值来源。verifier 要独立重算关键字段，覆盖空输出、乱序 ID、单位错误、重复计数和越界结论等负例。

## 6. 试跑与发布

发布前保存输入哈希、环境摘要、资源剖析、至少一次干净参考解运行、模型 trial 轨迹和三类评审结果。若公开答案已可检索，应重新切分、改写业务规则或明确将任务标为校准题。

### 6.1 试跑状态纪律

每道题按以下顺序记录：`reference_solution`、`simple_legal_baseline`、`always_abstain`、`template_or_keyword`、`target_model`。任一策略未执行必须保留 `NOT_RUN`，不能因为 verifier 或 card bundle 通过而升级为 `COMPLETE`。`READY_FOR_HARBOR` 还需要控制校准、目标模型 trial、可复现性、许可证、claim boundary 和科学复核全部有独立证据。

---

# 企业 Benchmark 出题任务书 V1.0

本节是企业 benchmark 的执行任务书。它把公开 benchmark 的共同要求、企业真实性、题目差异化、GPT 难度、训练价值和 Harbor 发布条件合并为一个可执行的状态机。它适用于企业公开 benchmark、联盟数据、企业公开 workflow，以及明确标记为合成/增强的校准题；不允许把合成题冒称为企业内部任务。

## A. 目标与非目标

### 目标

每道题都要把一个公开可核验的来源，转成一个有明确企业角色、业务决策、下游 handoff、错误代价和人工边界的可审计任务。题目必须同时满足：

1. agent 可见证据足以识别任务目标或识别证据不足；
2. verifier 能独立区分正确、错误、等价答案和合理弃答；
3. 失败可以定位到输入、方法、计算/工具、证据、主张边界或交付节点；
4. 任务难度来自真实的证据整合和竞争性决策，而不是 prompt 长度、工具数量或格式摩擦；
5. 数据、代码、模型、商标、隐私和 claim boundary 均有独立记录。

### 非目标

- 公开数据集名称不能证明企业内部数据或生产 SOP；
- 公开 leaderboard 不能直接作为隐藏真值；
- builder/schema 通过不能替代科学、许可、隐私和模型试跑；
- 一个失败的 target-model trial 不能单独证明题目“足够难”；
- 仅改 prompt、文件名、输出格式、阈值、随机种子或工具调用次数不算新企业题。

## B. 题源分类与真实性口径

在 source ledger 中给每个来源标注以下类别，并把企业参与关系单独写清楚：

| 类别 | 含义 | 允许的声明 |
| --- | --- | --- |
| `A` | 企业真实实验或研发项目数据，有可核验出处 | 可以描述为企业相关真实数据，但仍需授权/隐私审查 |
| `B` | 企业发布、维护或整理的公共 benchmark/数据集 | 只能描述为企业发布的公开 benchmark |
| `C` | 多企业或联盟共同维护的数据/挑战 | 必须披露联盟归属和再分发边界 |
| `W` | 企业公开 workflow、工具或示例 | 只能描述为企业公开 workflow，不等于生产 SOP |
| `S` | 合成、增强或教学 fixture | 必须明确标记 synthetic/calibration，不得冒称企业数据 |

每条来源至少保存组织、角色（owner/data contributor/publisher/maintainer/consortium member/third-party reference）、官方 URL、commit/tag、访问日期、内容哈希、许可证、数据访问状态和证据定位。

## C. REQ01-REQ14 公开契约矩阵

来源要求卡必须覆盖 14 个维度。正文规范与来源登记位于 `docs/public-enterprise-benchmark-requirements.md` 和 `knowledge_base/registry/public_benchmark_requirements.json`；卡片中的状态不能从 `observed` 自动升级为 `verified`。

| ID | 必须冻结的契约 | Harbor/出题产物 |
| --- | --- | --- |
| REQ01 | 角色、对象、目标、成功条件、claim boundary | task/instruction contract |
| REQ02 | 输入文件、字段、单位、主键、缺失和依赖 | agent-visible data card |
| REQ03 | 独立实体、实验单位和 train/validation/test 或时间/项目 split | split manifest、leakage verifier |
| REQ04 | 标签可见性、盲测阶段、阶段性揭示、verifier-only truth | visibility policy、oracle |
| REQ05 | 输出文件、字段、命名、排序、报告和日志 | required artifact schema |
| REQ06 | 指标方向、聚合、容差、等价答案和不确定性 | evaluation card |
| REQ07 | 官方 baseline、简单合法 baseline、资源和比较范围 | model-trial/difficulty card |
| REQ08 | commit/tag、数据版本、哈希和证据 locator | source ledger、manifest |
| REQ09 | 数据、代码、模型、商标和再分发许可/归属 | risk/license card |
| REQ10 | 依赖、权重、工具、网络、CPU/GPU、内存、时间和费用 | Harbor environment |
| REQ11 | 参数、随机性、日志、checksum 和重放命令 | reproducibility manifest |
| REQ12 | 无效输入、工具失败、缺失证据、合理弃答和停止规则 | control plan、verifier |
| REQ13 | 计算输出不能支持的机制、临床、商业或实验结论 | claim ledger、人审边界 |
| REQ14 | 公开答案、实体重叠、模板泄漏、holdout 和迁移污染 | risk card、held-out trial |

### 强制要求

REQ02、REQ03、REQ04、REQ06、REQ08、REQ09 任一维度不是 `VERIFIED`，来源只能停留在 `DRAFT`/`REVIEW_REQUIRED`，候选不能进入 `selected`。缺少官方定位时，状态必须保持 `PENDING_VERIFICATION`，不能用模型总结或搜索摘要补齐。

### 公开来源到要求维度的设计依据

下面的来源不是自动通过门禁的名单，而是设计 `requirements_card` 时的证据入口。每条来源仍需绑定固定版本、官方定位、访问日期和许可结论：

| 来源示例 | 反复出现的企业契约 | 主要冻结项 |
| --- | --- | --- |
| OpenADMET Blind Challenges、ExpansionRx | 盲测化合物、阶段性提交、端点指标 | entity-level holdout、标签可见性、提交格式、误差定义（REQ03/04/05/06/14） |
| Genentech CompBioBench runner | 隔离环境、结构化输出、成本追踪、失败恢复、多模型运行 | 环境、资源、日志、失败状态和 artifact schema（REQ05/07/10/11/12） |
| JUMP Cell Painting datasets | plate/well/perturbation/batch 元数据、主外键和数据库约束 | 实验单位、metadata join、replicate/plate split、版本和污染审计（REQ02/03/08/14） |
| Merck FEP benchmark | 固定系统、实验参考值、指标和来源论文 | system manifest、reference、outlier 规则、指标、商业工具许可（REQ02/06/08/09/10） |
| AiZynthFinder | stock、expansion/filter policy、搜索配置和路线结果 | 库存约束、搜索预算、失败原因、route validity 和人审边界（REQ01/02/07/10/12/13） |
| BayBE | search space、目标、约束、探索/利用策略、预算和 backtesting | 下一批实验、约束满足、uncertainty、成本和 stop/continue 规则（REQ01/06/07/10/12） |
| RxRx datasets | 公共数据与 proprietary universe 的权限区分 | 数据归属、再分发、标签可见性、企业声明边界（REQ04/09/13） |

`requirements_card` 的设计字段为：`requirement_id`、`status`、`evidence_url`/`evidence_locator`、`evidence_summary`、`harbor_action` 和 `blocking_rule`。当前 validator 已强制前五项和 REQ01-REQ14 完整覆盖；`blocking_rule` 用于记录该维度对 selected/Harbor 的阻塞关系。只有来源证据和版本都可复查，状态才可从 `OBSERVED_FROM_REGISTRY` 或 `PENDING_VERIFICATION` 升级为 `VERIFIED`。

## D. 16 张卡片与可见性

每个 v2 bundle 固定 16 张卡片：

```text
source + benchmark + workflow + transformation + data + evaluation + risk + harbor + review
+ candidate_set + enterprise_value + requirements + control_plan + difficulty + training_value + model_trial
```

卡片的职责和可见性必须分开：

- agent-visible：benchmark、workflow、data、harbor 和允许公开的 enterprise context；
- author-only：source、transformation、candidate_set、requirements、control_plan、difficulty、training_value、model_trial、risk、review；
- verifier-only：隐藏 truth、negative cases、oracle 和 control expected truth。

卡片的状态纪律如下：`DRAFT` 表示尚未完成设计，`REVIEW_REQUIRED` 表示需要人工/领域复核，`NOT_RUN` 表示还没有执行，`EVAL_ONLY_UNTIL_CALIBRATED` 表示不得用于训练，`READY_FOR_HARBOR` 只在所有发布门有证据后使用。

## E. 企业题设计步骤

### E1. 恢复原始 benchmark 契约

从官方页面、仓库、数据卡、论文 Data Availability 和运行配置中建立 source ledger。逐条填写 REQ01-REQ14，记录“观察到什么”“官方定位在哪里”“是否已固定版本”“是否可复现”。公开答案、排行榜和教程只能作为风险输入，不能直接作为 oracle。

### E2. 建立企业工作节点

在 enterprise value card 中明确：角色、项目阶段、对象、业务决策、下游接收者、必需 artifact、错误代价、人审 owner、采用/暂停规则和 claim boundary。若只有企业名称、没有角色和 handoff，最多标记为公开 workflow 或 synthetic calibration。

### E3. 生成 3-5 个候选决策

同一来源先生成 3-5 个候选，每个候选至少在两个语义轴上不同，并至少改变以下一项：业务决策/估计对象、失败机制、证据可见性与真值路线、下游 handoff 或停止规则。候选必须写出独立单位、错误后果、失败注入、必需产物和 GPT 难度机制。少于 3 个、语义重复或只有表面变化时，不能进入 selected。

### E4. 冻结数据、split 和真值路线

把输入 schema、单位、主键、实验单位、split、标签可见性、holdout、隐藏 truth 路线和许可证写入 data/evaluation/risk 卡。公开 benchmark 的 entity-level overlap、时间泄漏、模板泄漏和答案污染必须有审计；没有独立 truth route 的候选不能物化。

### E5. 设计四类控制

每道题至少有正例、负例、不变性例和证据不足例：

| 控制 | 目的 |
| --- | --- |
| positive | 证明参考解和合法等价答案可以通过 |
| negative | 关键数值、字段、方法或主张错误时必须失败 |
| invariance | 只改变顺序、无关命名或等价表示时决策保持不变 |
| insufficient evidence | 证据不足时必须弃答/转人工，不能强行给 winner |

### E6. 设计 GPT 难度和训练信号

至少形成一条可审计链：`schema/provenance -> independent unit/split -> competing choice -> evidence reconciliation -> bounded decision -> handoff/claim ledger`。难度卡必须包含状态依赖、失败注入、捷径探针和简单合法 baseline；training value card 必须包含错误标签、反馈粒度、留出轴、污染控制和使用状态。

#### E6.1 科学判断难度模块

优先从科研判断本身增加难度，而不是增加 prompt、文件或格式要求。当前可复用模块包括：

| 模块 | 适用判断 | 必须物化的证据/冲突 |
| --- | --- | --- |
| `judgment_claim_preserving_recovery` | 失败恢复是否仍回答同一科学问题 | 至少一个等价 fallback 和一个运行成功但 reference、version、estimand 或输入定义漂移的 fallback |
| `judgment_batch_identifiability` | 生物信号能否与批次/控制漂移区分 | 多批次重复、控制漂移、至少两个合理 normalization，以及一个降低批次指标但损伤表型的分支 |
| `judgment_route_feasibility` | 计算路线是否具有足够的化学证据进入人工评审 | 逐步 precedent、scope、chemoselectivity、stereochemistry、protection 和 stock 证据；不得直接给最终 `reaction_valid` 标签 |
| `judgment_value_of_information` | 下一批实验如何权衡探索、利用、失败风险与冗余 | 候选不确定性、预测收益、失败概率、成本和候选相关性；禁止未来 outcome 泄漏 |
| `math_hierarchical_batch_sensitivity` | normalization 对批次和表型结论的敏感性 | batch/condition/replicate 层级、控制范围、效应保留和不平衡/缺失控制 |
| `math_batch_acquisition_under_uncertainty` | 约束批次 acquisition 的可复核计算 | 声明 acquisition 公式、风险和相关性惩罚、合法组合、tie-break 与敏感性条件 |

模块登记不等于难度实现。每个新增模块必须同时满足：

1. agent-visible fixture 中存在会改变科学决策的竞争证据；
2. instruction 公开目标、阈值、允许的证据边界和等价答案类；
3. verifier 检查中间科学判断，而不只检查最终 winner 或固定措辞；
4. negative control 单独破坏该模块的关键假设，invariance control 保持该判断不变；
5. simple legal baseline 与 target model 重跑后，才能更新 `scientific_judgment` 等级。

若模块在当前数据中不会触发，例如相关性惩罚只连接不可能共同入选的候选，必须视为未实现并从难度配置移除。若 agent-visible 数据直接提供最终判断标签，例如 `reaction_valid=true`，不得再以对应领域推理模块提高难度。

难度等级与目标模型区分度必须分开记录。单次目标模型通过不自动降低已经物化且通过控制校准的结构难度，但只能记为 `PASS_SINGLE_TRIAL`，不得宣称该题能区分目标模型；至少完成重复试跑和独立领域复核后才能形成稳定的模型难度结论。反过来，若模型给出正确科学判断，但因 instruction 未声明的字段位置、等价命名或固定措辞被拒绝，必须修复 contract，并用未改动的原产物 replay；replay 通过时记录 `PASS_AFTER_CONTRACT_REPLAY`，原失败归入 verifier/contract，不计入科学难度证据。

### E7. 编译、隔离和试跑

物化 `task.yaml`/`task.toml`、`instruction.md`、agent-visible fixture、`solution/`、独立 `verifier`、`tests/`、环境和运行 manifest。依次执行 schema/结构检查、solver/judge 隔离、参考解、nop/always-abstain、template/keyword、简单合法 baseline、Docker/Harbor replay 和 target-model trial。

### E8. 模型前契约审计（强制）

在第一次真实模型调用之前，必须完成一次与模型无关的 contract audit。目的不是预测模型能否答对，而是确认“独立领域专家按 instruction 完成的语义正确答案”不会因为未公开的格式或措辞细节被拒绝。

审计至少包括：

1. `required_outputs` 为每个 artifact 声明路径、字段、单位、主键、排序和允许的等价表示；instruction 逐一引用这些路径和字段。
2. verifier 不能只接受一个隐藏答案，除非 instruction 明确声明唯一目标、优化方向、tie-break 和不可替代的 reference decision。对于合法替代答案，应使用约束/性质/容差验证。
3. verifier 中的 claim-boundary 不能依赖未写入 instruction 的精确短语；应优先检查结构化字段，例如 `causal_claim=false`、`human_review_required=true`、`provenance.input_sha256`。
4. 用 author-side reference submission、简单合法答案、始终弃答和模板/关键词答案分别运行 verifier；每个失败必须能归因到 artifact、计算、证据、claim boundary 或交付节点。
5. 先运行至少一次独立 verifier 环境的 oracle 和 nop；process-only 运行只能作为预检，不能替代 separate verifier mode。

若 contract audit 发现 undocumented phrase、single-answer assumption、provenance schema 未声明或独立合法答案被拒绝，任务停留在 `CONTRACT_ONLY`，不得把后续模型失败解释为任务难度。

## F. 选择与发布状态机

```text
SOURCE_OBSERVED
  -> REQUIREMENTS_REVIEWED
  -> CANDIDATE_SET (3-5)
  -> SELECTED (关键 REQ 已 VERIFIED + 企业价值/差异复核)
  -> CONTRACT_ONLY
  -> CALIBRATION_READY
  -> EVAL_ONLY_UNTIL_CALIBRATED
  -> MODEL_TRIAL_COMPLETE
  -> READY_FOR_HARBOR
```

任何一个关键门失败都只能进入 `DRAFT`、`REVIEW_REQUIRED`、`CONTRACT_ONLY`、`NOT_RUN` 或 `BLOCKED`。`READY_FOR_HARBOR` 必须同时具备：来源和关键 REQ 已核验、企业价值复核、候选差异证据、独立 truth/verifier、四类控制已校准、五类模型策略已试跑、错误归因/留出/污染审计、许可证/隐私/claim review、固定容器回放。

## G. 最小模型试跑矩阵

每题必须比较以下五种策略，缺任一种不能声称 GPT 难度：

1. `reference_solution`：证明任务可解并验证评分逻辑；
2. `simple_legal_baseline`：判断题目是否只是直接计算或格式劳动；
3. `always_abstain`：检查 verifier 是否错误奖励保守弃答；
4. `template_or_keyword`：检查题干、标签和固定答案捷径；
5. `target_model`：测量真实模型的证据整合、决策、工具和交付能力。

结果必须分开记录科学正确性、证据 grounding、决策有用性、artifact 完整性、复现性、不确定性/claim boundary、安全和人审。失败要按最早可定位节点归因，不能把总 reward 直接等同于难度。

模型 trial 失败后必须先做三分法：

- `agent_not_run`：provider、认证、容器或 runner 在模型生成前失败；不计入难度。
- `agent_completed_verifier_failed`：模型正常退出并写出产物，但 verifier 拒绝；必须回放 artifact 并检查 instruction/verifier 是否一致。
- `agent_completed_verifier_passed`：模型正常退出且 verifier 通过；仍需检查是否走了捷径或获得了不应可见的信息。

只有第二类经过 contract audit 排除题面/验证器问题后，才可以作为模型能力或任务难度证据。

## H. 任务书交付清单

每个进入合同编译的候选至少提交：

- `source ledger`、requirements card 和版本/哈希证据；
- candidate set、enterprise value、transformation 和 claim ledger；
- data/split/visibility、evaluation、risk 和 license matrix；
- control plan、difficulty、training value 和 model trial card；
- agent-visible fixture、verifier-only truth、独立 verifier、正/负/不变性/证据不足样例；
- `task.yaml`/`task.toml`、`instruction.md`、环境、运行日志和重放命令；
- review decision、release blockers、错误归因、模型轨迹和最终状态。

推荐校验命令：

```bash
python3 scripts/validate_knowledge_base.py
python3 scripts/validate_card_bundle.py knowledge_base/draft_bundles/<bundle>
python3 scripts/validate_candidate_matrix.py candidate_pools/enterprise-v1
python3 scripts/compile_contract_batch.py
python3 scripts/run_calibration_controls.py
python3 -m pytest -q
```

对已经物化的 enterprise task，追加：

```bash
python3 scripts/check_enterprise_harbor_sop.py \
  benchmarks/<task-id> \
  --output reports/<task-id>-enterprise-sop-preflight.json
```

该检查强制题包包含 `task.yaml`、`instruction.md`、非空 `data/`、`tests/`、独立 `verifier.py` 和隐藏 reference；逐项核对 `required_outputs` 是否在 instruction 中声明且位于 `outputs/`；核对四类控制、五类 trial 和 `quality/sop_card.json`。`status=PASS` 只表示允许进入 target-model trial，发布必须另查 `release_status`。目标模型超时、认证、provider、容器和 artifact 收集失败均只生成 infrastructure release blocker，不得计入难度。

在 target-model trial 之前，还应对每个 enterprise task 运行验证器 agent 的
contract audit：

```bash
PYTHONPATH=/path/to/benchmark-verification-agent/src python3 -m benchmark_review_agent.cli review \
  benchmarks/eb010-next-batch-001 --judge none
```

`enterprise-output-path-undocumented`、`enterprise-output-schema-missing`、
`enterprise-verifier-phrase-undocumented` 和
`enterprise-single-answer-contract` 任一出现，都应先修 instruction/verifier
合同，再解释模型 trial 结果。

当前知识库基线为 12 个来源 benchmark、5 类 workflow、10 个改题模式、10 个企业质量模块和 14 个来源要求维度。首批 tranche 的题目状态以 `candidate_pools/enterprise-v1/contracts/manifest.json` 为准；题目数量、schema 通过或静态 review 通过都不能替代企业价值、模型试跑和 Harbor 发布门。
