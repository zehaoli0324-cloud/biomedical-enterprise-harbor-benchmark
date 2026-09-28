# Pipeline And Task Remediation Issue

建议标题：`[P0] 按《改题方案与检查标准 v1.0》重构出题管线并完成现有题目返工`

依据：`docs/改题方案与检查标准-v1.0.md`（2026-09-23，含 2026-09-24 v12-v14 补充）、`docs/enterprise-harbor-sop-v1.1.md`、`reports/repository_audit_index_20260928.md`。

## 背景与当前判断

当前仓库已经有较完整的题目物化、verifier、质量卡、模型 trial、replay 和打包资产，但流程仍是多次手工生成、跨目录复制和局部脚本拼接。检查标准反复暴露的根因是：规范来源不唯一、题包副本可漂移、静态 PASS 与动态/科学 PASS 混用、来源冻结与科学审阅没有进入统一状态机。

当前范围分开统计：

- 正式 Git 题目范围：32 道。
- 工作区题目范围：46 道。
- 尚未晋级正式范围的候选题：14 道。
- 最近全量测试：318 passed, 6 skipped。
- `crispr-resistance-e2e-001` 仍缺完整 verifier/reference。
- 本地 evidence map 11 份，source manifest 3 份，source freeze manifest 0 份，named scientific review 0 份。

因此当前结论是：工程校准资产较完整，但仍是 internal calibration/review snapshot，不是 Harbor release candidate。

## 改造目标

完成后应满足：

1. 每个题目只有一个规范来源、一个版本身份和一个可重放的构建产物。
2. 每次改题都能从设计、来源、数据、verifier、控制、trial 到归档追溯。
3. `PASS`、`NOT_RUN`、`REVIEW_REQUIRED`、`BLOCKED`、`PUBLISHED` 等状态 fail-closed，不能由文件存在或静态扫描自动升级。
4. 题目科学可答性、判分公平性、数据真实性、模型难度和发布资格分开统计。
5. 任何发布包均可在干净环境中复建、oracle/nop 回放、解包复核并由独立人员审阅。

## P0：先改造出题管线

### P0.1 规范源与版本治理

- [ ] 定义唯一 canonical source root；明确 `candidate_pools`、`benchmarks`、`dist`、外部仓库的读写方向。
- [ ] 为每题建立 `task_id + task_version + source_commit + data_fingerprint + contract_fingerprint` 身份。
- [ ] 建立 promotion state machine：`SOURCE_OBSERVED -> REQUIREMENTS_REVIEWED -> CANDIDATE_SET -> SELECTED -> CONTRACT_ONLY -> CALIBRATION_READY -> MODEL_TRIAL_COMPLETE -> READY_FOR_HARBOR -> PUBLISHED`。
- [ ] 明确 `pipeline_status`、`evidence_status`、`review_status`、`release_status` 四条状态轴；任何缺件保持 `NOT_RUN/REVIEW_REQUIRED/BLOCKED`。
- [ ] 禁止从 Desktop、skill 仓库、research-benchmark 或旧 tarball 反向覆盖 canonical source；同步必须单向且记录 manifest。

验收：同一题从任一生成入口重建后，文件清单、版本、hash 和状态一致；冲突时构建失败而不是静默覆盖。

### P0.2 统一题包 schema 和生成器

- [ ] 统一 `task.yaml` 与 `task.toml` 的任务注册、required outputs、网络/资源、verifier 环境和版本字段；兼容层必须显式标记，不能靠目录扫描猜测。
- [ ] 以 `candidate_design.json`、`scenario-card.yaml`、`output_contract.json`、`source_manifest.json`、`quality/sop_card.json` 为规范输入，禁止脚本在多个地方硬编码同一字段。
- [ ] 生成 `instruction.md`、`environment/instruction.md`、`data/`、`environment/data/`、`tests/verification_data/` 的同步副本，并产出 copy manifest/hash。
- [ ] 将 verifier 设为单一规范源；根目录副本要么删除，要么只能由生成器同步，CI 必须阻止漂移。
- [ ] 从 verifier 实际读取集合反推 `artifacts`，在物化阶段阻断漏声明。

验收：P1 副本一致、P5 artifacts 差集为空、所有 agent-visible 文件都进入 agent 镜像，隐藏 truth 不进入 agent 镜像。

### P0.3 把检查标准变成一条可执行门禁

- [ ] 把静态检查（格式、语法、instruction 副本、可发现取值、基础镜像、隔离、verifier 漂移）整合为仓库级命令。
- [ ] 把动态检查固定为 oracle=1、nop=0、删必需产物失败、篡关键字段失败、语义等价表达通过。
- [ ] 把 mutation、reference、legal baseline、always-abstain、shortcut/template、target model 统一写入 trial manifest。
- [ ] 删除产物探针必须从 `task.toml.artifacts` 和 verifier 读取集合自动生成，防止探针本身空操作。
- [ ] 对字符串做 basename/大小写/枚举同义词/数值容差归一化；每个归一化点自动生成正例和负例。
- [ ] 把 `exception_type`、provider/auth/container/timeout/artifact collection 失败从科学分母剔除，记录为 infrastructure blocker。
- [ ] job-config 启动前检查任务数，禁止多个 `-p` 静默覆盖。

验收：单命令输出 machine-readable gate report；任一动态门禁未运行时不能显示 PASS，所有结果绑定输入 hash 和 verifier hash。

### P0.4 来源、证据与科学审阅流水线

- [ ] 为每个正式题建立逐文件 `source_manifest.json`，记录来源身份、访问入口、许可/隐私、文件 hash、可见范围和 claim boundary。
- [ ] 建立 `source_freeze_manifest.json`、`numeric_provenance.tsv`、`release_input_manifest.json` 三者的闭合检查。
- [ ] 建立 `claim_evidence_map.tsv`，逐个 judgment unit 连接数据字段、来源、计算、参考答案和 verifier 项。
- [ ] 建立具名 `scientific_review.json` 工作流，审阅者、范围、结论、日期和未解决问题均必填；不得由脚本自动填 APPROVED。
- [ ] 将 synthetic fixture、derived-from-public、public-source-frozen 分级；合成数据不能升级为真实科学证据。
- [ ] 大型原始文件采用 hash/cache 引用和最小公开 processed metadata，禁止未经审计的重复打包。

验收：严格真实数据门禁和 source-derived replay 均有记录；缺 source freeze、rights/privacy 或 scientific review 时 release 必须 BLOCKED。

### P0.5 试跑、成本和归档治理

- [ ] 先运行器验收，再运行题目难度校准；长流程只统计有效轨迹属性，不设置最低交卷轮数。
- [ ] 固定模型、timeout、reasoning effort、预算、容器 digest 和网络模式；单题冒烟后再批量运行。
- [ ] 记录轨迹中的科学正确性、交付完整性、有效新增工作、工具/运行失败和成本，不把长轮数等同于难度。
- [ ] 每次数据、题面、输出契约或 verifier 修改都自动标记旧 trial 为 superseded，禁止混用。
- [ ] 打包前清理 jobs/trials/logs/cache/bytecode，生成 `.tar.gz + .sha256`，解包后独立 `diff -rq`。

验收：发布包可在干净机器独立构建和回放；报告能区分 raw fail、contract replay pass、scientific fail 和 infrastructure fail。

## P1：现有题目返工顺序

### P1.1 先分流 46 道题

- [ ] 32 道正式题逐题补齐 release matrix；明确 `KEEP_CALIBRATION`、`REPAIR`、`REAL_SOURCE_MIGRATION`、`RETIRE`、`PROMOTE_CANDIDATE`。
- [ ] 14 道候选题保持 candidate-only，直到 schema、来源、控制、当前版本 trial 和 package replay 完成；不得混入正式统计。
- [ ] 完成跨仓库 lineage/dedup 审查，确认同一题族只保留一个 canonical version，其他版本标记 lineage variant 或 retired duplicate。

### P1.2 立即阻断题

- [ ] `crispr-resistance-e2e-001`：补 verifier/reference 和物化数据；若不能提供许可冻结数据，缩窄为 contract-review task。
- [ ] `literature-screening-m1-001`、`research-workflow-stress-test-001`：替换 placeholder/missing DOI，补 source manifest、claim map 和科学审阅；在此之前保持 calibration-only。
- [ ] `eb015-real-source-replacement-gate-001`：完成 source rights、逐文件 SHA-256 freeze、source alias/path 修复、verifier rebind、可运行测试入口和 fixed-container replay。
- [ ] `eb006-research-completion-011`：做 clean target rerun；保留先前 `C43|late` scientific mismatch，不得用 contract replay 覆盖。

### P1.3 先关闭固定容器队列

- [ ] 对 `eb013-cross-context-evidence-portfolio-005`、`eb014-sequential-evidence-feedback-002`、`eb010-adaptive-policy-regret-005`、`eb010-closed-loop-replay-003`、`eb013-partial-observation-risk-004`、`eb013-shared-setup-routing-003`、`eb006-donor-stratified-signal-005`、`eb006-research-completion-008` 执行 fixed-container replay。
- [ ] 每题保存 task data fingerprint、container image digest、verifier result、oracle/nop、mutation 结果和 archive SHA-256。
- [ ] `eb014` 补 trajectory analysis；`eb013` 补 held-out target trials；所有题安排 practitioner review。

### P1.4 六道证据路由/不确定性题

- [ ] 对 `eb010-closed-loop-ambiguity-004`、`eb010-distributional-policy-stress-006`、`eb010-stop-uncertainty-002`、`eb011-reproduction-manifest-001`、`eb013-evidence-budget-routing-001/002` 完成当前数据版本的 reference、mutation、baseline 和 target calibration。
- [ ] 执行四种弃权变体：全部弃权、全部确定回答、正例+证据不足弃权、正例改错误弃权。
- [ ] 按独立判断单元记录 `score`、`score_weight`、`abstention_fraction` 和 blanket-abstain 对照；弃权比例与权重超过标准时缩窄题目或补数据。
- [ ] 为每个输出补最小合法 JSON shape、字段层级、空值/排序/唯一性/单位/容差和等价最优解规则。

### P1.5 其余正式题的批量返工

- [ ] 扫描所有 verifier 字面量，把协议拼写公开到 instruction，把科学结论留在 verifier 计算中。
- [ ] 对所有自由文本证据检查改用结构化字段或段落/否定感知逻辑，补正反双向 probe。
- [ ] 对所有数值比较补正确值、精度内近似值、真实错误值三件套。
- [ ] 补齐 `README` 的 `Task description / Difficulty / Reference solution / Verification`，以及 `difficulty_explanation`、`solution_explanation`、`verification_explanation`。
- [ ] 为每题建立五类 scenario：sufficient、insufficient、counterexample、equivalent、malformed，并把五类都接入控制或 mutation。
- [ ] 对输出多而可见数据少的题逐题做 evidence-surface 审计；数据不足不能靠 blanket abstention 通过。

## P2：难度、差异化与发布提升

- [ ] 只有 oracle/nop、控制、当前版本 target trial、held-out trial、fixed-container replay 和 review 全部闭合后，才允许更新 `difficulty_claim`。
- [ ] 对模型已稳定通过的题增加真实的 primary difficulty axis（隐藏 scenario family、观察依赖、跨阶段约束或可证伪扰动），不通过加长 prompt、无依据子问题或额外弃权机会增难。
- [ ] 为每个新增难度模块登记科学用途、数据要求、对照、兼容/冲突模块、失败归因和复用范围。
- [ ] 以一个窄而完整的真实数据题作为 real-only pilot，完成来源重建、独立复算、正确/等价/目标错例、单轴对照后再扩展题族。
- [ ] 形成 practitioner review roster 和发布审批记录；任何自动审计只能说明机械门禁，不得替代科学判断。

## 交付物

- [ ] `config/task_schema.v2.json` 与状态机定义。
- [ ] `scripts/build_task.py` / `scripts/check_task_package.py` / `scripts/run_task_gates.py` 三个统一入口。
- [ ] 逐题 `quality/release_matrix.json`、`source_manifest.json`、`source_freeze_manifest.json`、`claim_evidence_map.tsv`、`scientific_review.json`。
- [ ] 每次构建的 `build_manifest.json`，包含 source commit、task version、输入/输出 hash、verifier hash、container digest 和 gate results。
- [ ] 32 道正式题和 14 道候选题的分流清单、lineage/dedup 清单和 promotion 记录。
- [ ] fixed-container replay、abstention variants、held-out trials、practitioner review 和发布包 SHA-256 的归档索引。

## 完成定义

- [ ] 新题只能经统一六步流程进入候选；任何步骤缺产物即阻断。
- [ ] 旧题逐题有明确 disposition，不能继续使用模糊的“有报告=已完成”。
- [ ] 正式发布题全部通过静态、动态、mutation、来源、科学审阅、fixed-container、包装和人工复核门禁。
- [ ] 所有模型结果按当前题目版本和数据 fingerprint 归档，`NOT_RUN`、`SUPERSEDED`、`INFRASTRUCTURE_BLOCKED` 不进入难度结论。
- [ ] GitHub issue、仓库审计索引和最终发布 manifest 可以相互链接并复核同一版本。

