# 造题配置

- `module_catalog.json` 是可复用模块的注册表。模块 ID、所属类别、控制的难度维度和常见失败模式都在这里声明。
- `examples/*.toml` 是已经选定、作为仓库示例维护的任务难度配置。候选 TOML 可以先保留在 `candidate_pools/`，选优后再决定是否提升为长期示例。
- `examples/*.toml` 必须通过 `[scenario].card` 引用一个场景卡；难度生成器会校验来源场景覆盖、科学判断、workflow handoff 和 release gates。

## 添加模块

1. 在 `module_catalog.json` 添加唯一 `id`。
2. 指定一个模块类别和一个难度维度。
3. 列出它可产生或影响的 artifact，以及典型 failure modes。
4. 在至少一个任务配置中使用它。
5. 为模块补充一个触发条件、预期 agent 行为和 verifier signal；这些信息最终应进入任务的 `failure_injections` 或 scenario card。

模块目录是索引，不是科学有效性的证明。新增模块仍需经过 scenario-to-benchmark skill 规定的 provenance、observability、verifiability 和 naive-resistance gates。

推荐顺序：先运行 `scenario-to-benchmark` 建立证据与场景，再生成候选卡和候选 TOML，完成 `validate-candidates -> candidate-protocol -> select-candidates` 后，才对获选配置运行 `validate -> score -> compile -> protocol -> evaluate -> iterate`。不能反过来先追求 frontier 分数再补科研语境。
