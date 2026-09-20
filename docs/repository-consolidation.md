# 仓库整合说明

## 结论

`skill-scenario-to-benchmark` 是后续唯一维护的主仓库。原 `research-benchmark` 的 `main` 提交 `52580d3` 已是当前主线历史的祖先，因此研究资产、提交历史和文件来源均已被保留，不需要再次复制目录或创建 unrelated-history merge。

整合后的职责是：

```text
原 research-benchmark
  场景清单 + 失败分类 + benchmark 设计 + 研究计划
                         |
                         v
skill-scenario-to-benchmark
  场景挖掘 skill + 候选选优 + 难度编译 + 任务资产
  + 隔离执行 + hidden verifier + LLM 评价与迭代
```

## 维护边界

- GitHub 主仓库：`zehaoli0324-cloud/skill-scenario-to-benchmark`。
- `research-benchmark` 只作为历史来源和对照，不再接受独立功能开发。
- 新 workflow 从 `skills/scenario-to-benchmark/` 进入，不在研究文档中另建一套造题步骤。
- `docs/authoring-pipeline.md` 是端到端 authoring 流程的单一规范。
- `docs/candidate-pipeline.md`、`docs/evaluation-pipeline.md` 和 `docs/trial-runner.md` 只负责各自阶段的详细契约。
- `docs/benchmark-design.md`、`docs/research-agenda.md` 和 `docs/scenario-gap-analysis.md` 是研究依据，不是第二套执行入口。

## Git 验证

整合分支建立时，以下关系成立：

```text
research-benchmark main (52580d3)
  is ancestor of
skill-scenario-to-benchmark main (86016f2)
```

因此验收重点是目录职责、入口和概念去重，而不是文件数量或一次新的 merge commit。旧仓库若在此后出现必要修复，应以明确的 cherry-pick 或补丁进入主仓库，并记录来源；不要恢复双向同步。
