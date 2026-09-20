# Expected Artifacts

本文件定义 verifier 检查的交付接口。它不包含隐藏参考排序、注入标签或最终答案。

## 必需文件

| 文件 | 最低检查 |
| --- | --- |
| `outputs/study_plan.yaml` | 有问题、假设、实验单位、比较关系、排除规则和停止标准 |
| `outputs/evidence_table.tsv` | 每行有 source、claim、support status、locator 和 limitation |
| `outputs/screen_results.tsv` | 有效应量、FDR、重复一致性、批次处理和 QC 状态 |
| `outputs/rna_mechanism.tsv` | 有 contrast、log2FC、FDR、pathway 和 interpretation |
| `outputs/target_ranking.tsv` | 排名同时保留各证据维度、风险和不确定性 |
| `outputs/guide_candidates.tsv` | 有序列、PAM、位点、评分、脱靶类别和约束状态 |
| `outputs/editing_validation.tsv` | 有可用 reads、编辑率、frameshift、QC 和局限 |
| `outputs/claim_ledger.tsv` | 每个关键主张对应 source path、数值和支持等级 |
| `outputs/workflow_bundle/` | 有 workflow、环境锁定、运行日志和输入 checksum |
| `outputs/final_report.md` | 有最终决策、证据摘要、失败记录、不确定性和下一步实验 |

## Verifier 重点

1. 文件和字段完整性：缺失交付物不能用自然语言补偿。
2. 实验单位：报告是否明确生物重复、技术重复、well/cell/read 的层级。
3. 统计边界：是否处理批次、对照、比较方向和多重检验。
4. 证据追溯：引用是否存在并支持对应主张，定位是否可复核。
5. 跨产物一致性：排名、图、表、正文和日志中的数字是否一致。
6. 不确定性：不可分析样本、低质量编辑 reads 和冲突文献是否被标记。
7. 重跑条件：版本、参数、随机种子和输入 checksum 是否足以复现。

## 不应评分为成功的输出

- 只有一个最终候选基因，没有中间证据。
- 只有工具日志，没有科学决策和结论边界。
- 把高分 guide 当作已验证 guide。
- 把 screen 或表达关联直接写成因果机制。
- 用空表、常数分数或批量复制文本填充必需字段。
