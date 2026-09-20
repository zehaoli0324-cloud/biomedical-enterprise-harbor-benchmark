# Expected Artifacts

| Artifact | Required fields or checks |
| --- | --- |
| `outputs/analysis_plan.yaml` | question, experimental_unit, contrasts, exclusion_rules, stop_rules |
| `outputs/source_audit.tsv` | normalized DOI, duplicate relationship, evidence level, causal support boundary and locator |
| `outputs/sample_qc.tsv` | biological unit, batch, conflict status, QC action for every sample |
| `outputs/candidate_ranking.tsv` | one row per candidate, decision, transparent score and uncertainty fields |
| `outputs/tool_run_log.tsv` | pinned tool version, checksums, failed export, fallback and final status |
| `outputs/sensitivity_analysis.tsv` | baseline plus alternate weight scheme and interpretation |
| `outputs/claim_ledger.tsv` | claim-to-evidence path, support level, causal status and caveat |
| `outputs/reproducibility_manifest.json` | input checksums, rules/tool versions, resource budget and rerun command |
| `outputs/final_report.md` | decision, evidence summary, failure log, uncertainty, next step and safety boundary |

隐藏参考会检查：输入冲突是否被发现、重复 DOI 是否只计一次、关联证据是否被限制、batch-confounded 候选是否降级、工具失败是否恢复、敏感性分析是否真实反映权重变化，以及最终主张是否超出证据。
