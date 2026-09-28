# High-Quality Trial Bundle (2026-09-28)

## Included tasks

以下题目有高质量 `gpt-5.6-sol` 完成记录，且保存了可审计的 trial 目录、trajectory/事件文件和文字分析。通过与否不是唯一筛选条件；EB013-001 的最终 verifier 失败历史记录保留，但 repaired trial 已通过，纳入本 bundle。

| task | selected high-quality trial | status | task environment |
|---|---|---|---|
| `eb013-cross-context-evidence-portfolio-005` | `selected4-eb013-gpt56sol-v3-001` | `pass` | absent; process-calibration task |
| `eb013-evidence-budget-routing-001` | `eb013-evidence-budget-routing-001-gpt56sol-20260928-repaired-005` | `pass` | absent; process-calibration task |
| `eb013-evidence-budget-routing-002` | `eb013-evidence-budget-routing-002-gpt56sol-20260928-repaired-002` | `pass` | absent; process-calibration task |
| `eb013-partial-observation-risk-004` | `partial-risk-gpt56sol-001` | `pass` | absent; process-calibration task |
| `eb013-shared-setup-routing-003` | `shared-setup-gpt56sol-002` | `pass` | absent; later adapter early-completion attempt retained as negative history |
| `eb014-sequential-evidence-feedback-002` | `selected4-eb014-gpt56sol-v3-002` | `pass` | present under `environment/` |
| `eb015-real-source-replacement-gate-001` | `selected4-eb015-gpt56sol-v3-001` | `pass_after_contract_replay` | present under `environment/` |

## Bundle contents

`dist/high-quality-gpt56sol-trials-20260928.tar.gz` contains each full task package (`instruction`, verifier/tests, data, quality cards), all available task-level `environment/` files, every stored `quality/trials/` trajectory and event log, target evidence, trial analysis, and the runtime adapters used to interpret the runs. The archive has 689 payload files and is verified by its embedded manifest; SHA-256 is in `dist/high-quality-gpt56sol-trials-20260928.tar.gz.sha256`.

The five EB013 task packages do not currently have a task-specific `environment/` directory because their successful trials were local process calibration runs. The bundle records that absence explicitly instead of fabricating a Docker environment. EB014 and EB015 include their existing environment files.

## Earlier GPT-5.5 trials

The repository has one explicit historical GPT-5.5 trial: `literature-screening-m1-001`, documented in `docs/trial-calibration-001.md`. It is not immediately trialable from this checkout: the current package is `CONTRACT_ONLY` and lacks `verifier_only/reference.json`, `quality/sop_card.json`, baseline/control records, source freeze and output-contract files. It should not be included in the high-quality bundle until those package gates are restored.

The `codex_gpt55.py` filename in many GPT-5.6 records is the adapter name, not evidence that those runs used GPT-5.5; the model field and trial manifest are the authoritative model identifiers.

## Release boundary

This is an internal calibration/evidence bundle. It is not a Harbor release bundle. Fixed-container replay, source/license checks where applicable, and practitioner review remain release gates.
