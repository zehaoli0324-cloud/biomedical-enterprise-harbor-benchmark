# Agent Task

你是负责候选靶点优先级判断的科研数据分析师。你必须在完全离线的环境中读取 `data/`，审计输入，完成一个可复核的多阶段分析，并把所有文件写入 `outputs/`。

这不是让你凭关键词选出一个候选。你必须先检查数据类型、字段、重复、缺失、批次和工具契约，再进行证据整合。输入中故意存在冲突和失败注入：发现问题后要记录、降级或停止受影响分支，不能静默修正或猜测不可见信息。

## 必须遵守的边界

- 先阅读 `data/project_brief.md` 和 `data/constraints.yaml`。
- 不使用网络，不假设缺失的全文、方法或实验结果。
- sample/read 不是独立生物重复；必须显式写出实验单位。
- 对 normalized DOI 重复只保留一个证据源，同时记录 duplicate relationship。
- 只有关联证据的来源可以作为 context，不能支持 causal claim。
- 第一条工具 export 会产生空的 partial output；必须记录 failed export 并使用已登记的离线 fallback。
- 缺失值、批次混杂和 QC 失败必须进入 uncertainty 或 hold 路径。
- 可以给出计算优先级，但不得生成临床建议或可直接执行的 wet-lab protocol（湿实验操作规程）。

## 必须交付的输出

所有文件都必须放在 `outputs/`：

- `analysis_plan.yaml`
- `source_audit.tsv`
- `sample_qc.tsv`
- `candidate_ranking.tsv`
- `tool_run_log.tsv`
- `sensitivity_analysis.tsv`
- `claim_ledger.tsv`
- `reproducibility_manifest.json`
- `final_report.md`

每个文件的字段契约见 `task.yaml`。`candidate_ranking.tsv` 至少要让审计员看出为什么一个候选 go、一个候选 hold、一个候选 no-go、一个候选 uncertain。不要用单一分数掩盖风险或证据缺失。

## 决策要求

1. 先完成输入 schema 和 provenance 检查。
2. 识别文献重复、metadata 冲突、关联证据和不能确认的来源。
3. 识别 swapped batch label、生物重复和缺失测量；不要把冲突输入改写成干净数据。
4. 根据预注册权重计算透明的候选排序，并说明缺失值和风险如何影响排序。
5. 记录工具版本、调用顺序、输入输出 checksum、失败 export 和 fallback。
6. 至少运行一个 alternate weight sensitivity scenario，并说明 top candidate 或决策是否变化。
7. 用 claim ledger 把每个主张连接到证据和限制条件，最后在报告中写清 uncertainty、human review 和安全边界。
