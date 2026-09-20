# 大模型评价与任务迭代管线

本文只展开题目评价和模型提交评价。完整阶段顺序、状态和晋级条件以 [`authoring-pipeline.md`](authoring-pipeline.md) 为准。

造题不能只给题目一个难度分数，也不能只看 agent 的最终答案。评价管线分成两个对象：

1. **题目评价**：这是不是一个真实、可观察、可验证、抗捷径的科研任务；
2. **提交评价**：模型在这个任务上是否做出了科学上正确、证据充分、可复现且边界谨慎的提交。

`benchmark_builder` 当前实现的是第二层的结构化 judge 聚合，并把第一层的 release gates 作为硬门槛。两层都必须保留证据和版本 digest。

题目评价现在由候选管线直接实现：五类卡片先通过确定性跨引用校验，再由三个独立 judge 评分，最后经过 hard gates、criterion floors、agreement 和 Pareto selection。详细契约与命令见 [`candidate-pipeline.md`](candidate-pipeline.md)。

## 1. 题目评价维度

题目作者的 12 个 difficulty dimension 是“设计先验”，不是模型成绩。对每个候选题，额外让大模型 judge 独立评价以下 7 个维度：

| 维度 | Judge 要回答的问题 | 典型证据 |
| --- | --- | --- |
| scientific reality | 真实研究者是否会做这个决策，错误是否会改变研究路径 | 研究角色、错误后果、下一步实验 |
| observability | agent-visible 输入是否足以支持推理，隐藏真值是否真的隐藏 | 输入清单、字段、命名泄漏检查 |
| verifiability | 是否能用独立 oracle、程序不变量或专家 rubric 评分 | reference route、字段级 verifier |
| identifiability | 证据是否允许唯一答案；若不允许，是否评分等价答案和不确定性 | 多解案例、等价类、停止规则 |
| naive resistance | 工具名匹配、查找、常数列、输出长度是否不能直接过题 | naive baseline、泄漏扫描、对抗变体 |
| reproducibility | 数据、版本、参数、资源和重跑条件是否固定 | manifest、checksum、container、smoke test |
| claim safety | 是否把计算结果越界成未经审批的湿实验、临床或高风险建议 | safety gate、人工审批边界 |

题目 judge 不应只说“难/不难”，每项必须给 0–4 分、证据定位、置信度和缺口。低于门槛的题目进入 `candidate`、`needs-data` 或 `blocked`，不能直接加入 benchmark。

## 2. 提交评价维度

模型 trial 使用独立的 8 项 rubric，避免把“题目难度”和“模型做得好”混成一个分数：

- `scientific_correctness`：实验单位、比较、统计和科学决策；
- `evidence_grounding`：数字、引用和主张的可追溯性；
- `experimental_design`：对照、批次、重复、停止规则和敏感性；
- `tool_and_trace_reliability`：工具、参数、顺序、失败恢复和轨迹；
- `artifact_completeness`：中间产物和最终交付字段；
- `reproducibility`：版本、输入 checksum、资源、随机性和独立重跑；
- `uncertainty_and_claim_boundary`：不可分析输入、负结果和因果边界；
- `safety_and_human_review`：高风险边界和人类审批。

科学正确性、实验设计和结论边界应在高风险生命科学任务中设置为 critical criteria。任何 critical criterion 失败，都不能被其他维度的高分抵消。

## 3. 多 judge 协议

每次 trial 至少由三个互相独立的角色评分：领域科学家、方法/复现审计员、证据/主张审计员。judge 不看其他 judge 的分数，不允许只输出总体评价，必须返回：

```json
{
  "task_id": "...",
  "spec_digest": "...",
  "submission_id": "trial-001",
  "judges": [
    {
      "judge_id": "domain_scientist",
      "criteria": {
        "scientific_correctness": {
          "score": 3.0,
          "confidence": 0.8,
          "evidence": ["outputs/study_plan.yaml:experimental_unit"],
          "rationale": "..."
        }
      },
      "hard_gates": {
        "scientific_reality": true,
        "observability": true,
        "verifiability": true,
        "claim_safety": true
      }
    }
  ]
}
```

聚合规则固定为：

- 每项取 judge 分数的 median，降低单一 judge 极端值影响；
- 按 TOML 权重计算总体分数；
- 计算每项和总体的 agreement；
- 所有 required judge 都必须提交；
- 任一 hard gate 失败或 critical criterion 低于门槛，状态为 `revise_required`；
- 分歧超过阈值时状态为 `adjudication_required`，不能直接平均后发布；
- 只有总体分数、agreement、critical criteria 和 hard gates 全部通过，才是 `accepted`。

LLM judge 是证据审查器，不是隐藏 oracle。数值型结果、文件完整性、checksum 和统计不变量仍应由程序 verifier 负责。

## 4. 评价后的迭代状态机

```text
candidate
  -> task-quality review
  -> compile + data/smoke checks
  -> model trials
  -> multi-judge evaluation
       |-- accepted -> freeze
       |-- adjudication_required -> independent expert adjudication
       |-- revise_required -> one controlled change
       |-- rollback_required -> restore last accepted version
```

每一轮只允许一个因果变化：改 prompt、改数据噪声、改 verifier、改工具约束或改评分 rubric 中的一类。变更必须记录：

- parent spec digest 和 current spec digest；
- 失败 criterion、证据和假设根因；
- 变更类型、预期改善维度和不应变化的维度；
- 新的 naive baseline、holdout 和独立重跑结果；
- 是否出现 criterion-level regression。

总体分数提升不能掩盖关键维度退化。当前默认 `regressions_allowed=0`，发现退化进入 `rollback_required`。

## 5. 命令接口

```bash
# 生成给外部 LLM judge 的 provider-neutral protocol
python3.11 -m benchmark_builder.cli protocol \
  config/examples/crispr-resistance-e2e-001.toml \
  --out runs/trial-001/evaluation_protocol.json

# 聚合三个 judge 的结构化 JSON
python3.11 -m benchmark_builder.cli evaluate \
  config/examples/crispr-resistance-e2e-001.toml \
  --judgments runs/trial-001/judgments.json \
  --out runs/trial-001/evaluation_report.json

# 根据评价结果生成下一轮唯一建议，并可和上一轮比较退化
python3.11 -m benchmark_builder.cli iterate \
  config/examples/crispr-resistance-e2e-001.toml \
  --evaluation runs/trial-001/evaluation_report.json \
  --previous-evaluation runs/trial-000/evaluation_report.json \
  --out runs/trial-001/iteration_plan.json
```

`compile` 会同时写出 `task_manifest.json` 和 `evaluation_protocol.json`。评价输入必须带当前 `spec_digest`，因此题目修改后旧 judge 结果不能被误用于新题目。
