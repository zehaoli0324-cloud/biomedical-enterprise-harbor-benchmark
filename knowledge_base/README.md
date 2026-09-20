# 企业 Benchmark 知识库

这里不是链接收藏夹，而是把公开企业 benchmark 还原成可审计的证据图。知识库中的记录只描述来源实际支持的内容；“企业名称出现于页面”不等于“企业内部真实任务”。

## 与科研场景知识库的区别

科研场景知识库通常从 workflow/tool 出发，重点是研究对象、科学问题、判断和证据边界。企业 benchmark 知识库在此基础上增加四个独立层：

1. **企业归属证据**：企业是数据拥有者、数据贡献者、工具维护者、联盟成员，还是仅被第三方引用。
2. **benchmark 契约**：任务、输入/输出、split、盲测/排行榜、指标、提交限制和官方 baseline。
3. **商业与再分发边界**：数据、代码、模型权重、商标、患者/客户数据和外部服务分别记录许可与访问状态。
4. **业务真实性与合规**：公开流程是否代表生产工作、计算结果能否支持研发决策、哪些结论必须由专家或实验确认。

## 实体与卡片链

```text
source_record
  -> enterprise_benchmark_record
  -> enterprise_workflow_card
  -> transformation_card
  -> data_card + evaluation_card + risk_card
  -> harbor_delivery_card
  -> model_trial_card / review_card
```

一个来源可以有多个 benchmark，一个 benchmark 可以派生多个改题版本；每个派生版本都必须保留 source/version/hash 链，不能在原题目录上原地覆盖。

## 目录

- [`registry/enterprise_benchmarks.jsonl`](registry/enterprise_benchmarks.jsonl)：公开企业 benchmark / workflow 登记表。
- [`registry/workflows.jsonl`](registry/workflows.jsonl)：从 benchmark 恢复出的业务工作流和科研决策。
- [`registry/transformation_patterns.jsonl`](registry/transformation_patterns.jsonl)：可复用的改题模式，不代表已经完成的题包。
- [`seeds/official_sources.json`](seeds/official_sources.json)：爬取入口、来源类型和待核验项。
- [`schemas/`](schemas/)：source、benchmark、workflow、transformation、data、evaluation、risk、Harbor 和 review 卡的最小契约。
- [`templates/`](templates/)：新记录和新改题版本的作者模板。
- [`draft_bundles/`](draft_bundles/)：由登记表批量生成的改题卡骨架；所有 bundle 默认处于 `DRAFT`，必须经过来源、许可、真值、隔离和试跑审核。
- [`harvest/README.md`](harvest/README.md)：原始页面快照、哈希和抓取日志的保存规范。

## 状态纪律

`observed` 只表示已经读取页面或仓库；`verified` 还需要固定版本、可复查定位和许可/归属证据；`ready_for_redesign` 还需要独立数据、真值和 verifier 路线。搜索摘要、二手博客和模型生成文本不能单独把记录升级为 `verified`。

真实性类别沿用项目主仓库：`A` 企业真实实验/项目数据，`B` 企业发布的公共 benchmark，`C` 多企业联盟，`W` 企业公开工作流，`S` 模拟/增强 fixture。

## 推荐收集顺序

先抓官方组织/仓库、官方数据卡和论文 Data Availability，再抓挑战平台、榜单和教程；每个来源同时收集 source URL、固定 commit/tag、访问日期、原始文件哈希、许可证、输入/标签可见性和数据是否能实际下载解析。抓不到隐藏标签时，记录 `blind_or_withheld`，不要用公开排行榜推测标签。
