# EB013 Trial Repair Note

日期：2026-09-28  
范围：`eb013-evidence-budget-routing-001`、`eb013-evidence-budget-routing-002`

## 背景

两道题的 2026-09-28 `gpt-5.6-sol` trial 都正常退出并生成了五份产物，但没有通过当前 verifier。复核结论是：001 的核心路线选择正确，失败集中在派生字段和 provenance；002 的自适应策略选择正确，失败集中在 policy replay、TSV 序列化和 provenance。历史 trial 保留原判定，不将其追溯改判为模型科学失败，也不修改 verifier 迎合模型输出。

## 根因

- 两题的 task/instruction 和 quality audit 声明了输出合同，但 `data/output_contract.json` 实体缺失，模型看不到可机器读取的字段、分隔符和 provenance 约束。
- 001 没有明确 `effective_reductions` 的语义：合法但因目标路线未选中的请求，仍应输出自身完整 `covers`；只有 scope、future outcome 或 missing dependency 等内在 blocker 才输出 `{}`。
- 002 没有把不完整 policy 的 `null` 目标值、每个 stage-1 observation 的完整 replay，以及 ASCII TAB/换行要求固定为可检查合同。

## 修复方案

1. 新增两题的 `data/output_contract.json`，声明 required files、exact JSON hash paths、字段清单、TSV columns、等价表示和禁止项。
2. 更新两题 `instruction.md`，要求先读取 output contract，并显式解释上述派生字段、incomplete policy 和真实 TAB 分隔符。
3. 在 `quality/contract_audit.json` 登记 `canonical_contract`。
4. 增加回归测试，确认 output contract 的 hash 清单与 verifier 动态 oracle 实际纳入的 JSON 文件集合一致。
5. 保持 `verifier.py`、hidden reference 和历史 trial 产物不变；修复后的 trial 使用新的 trial ID 和外部输出目录。

## 验收标准

- 两题原有 verifier 测试全部通过。
- 新 target trial：Agent 正常退出、五份产物齐全、runner verifier 结果可复现。
- 若 raw verifier 仍失败，必须区分科学路线错误与交付/表示错误，并保留 unchanged-artifact replay 结果；不得直接修改 verifier。
- 本地 process trial 只作为 calibration evidence；Docker/Harbor fixed-container replay 和 practitioner review 仍是发布门禁。

## Trial protocol

模型：`gpt-5.6-sol`   
Backend：本机 `process` / `process_cwd_only`   
Network：`off_requested`  
Timeout：600 秒  
输出根目录：`/private/tmp/eb013-repaired-trials-20260928`

Trial 结果和 artifact SHA-256 将在本次运行完成后追加到本文档，并同步写入每题 `quality/`。
