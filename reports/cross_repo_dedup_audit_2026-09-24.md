# Cross-repository deduplication audit (2026-09-24)

这是静态题目重合审计，不是科学等价性证明。当前仓库只按 Git 跟踪的正式题包统计；工作树候选题不混入正式题数。

- 当前仓库正式题包：**32**
- 扫描外部本地仓库：**3**
- 外部 task package：**261**
- 同一规范化 ID 的题族仓库组合：**6**
- 直接重复/同一题族待复核组合：**4**
- 高重合待人工复核：**0**

## 扫描仓库

- `/Users/zehaoli0324/harbor-science-bench-factory`
- `/Users/zehaoli0324/research-benchmark`
- `/Users/zehaoli0324/skill-scenario-to-benchmark`
- `/Users/zehaoli0324/work/BioBenchFactory`

## 同一题族/直接重复候选（按仓库归并）

| 当前题目 | 外部仓库 | 外部版本/路径数 | 最佳外部题目 | 最高 score | 判定 |
|---|---|---:|---|---:|---|
| `research-workflow-stress-test-001` | `skill-scenario-to-benchmark` | 18 | `research-workflow-stress-test-001` | 0.9053 | `SAME_LINEAGE_REVIEW` |
| `literature-screening-m1-001` | `research-benchmark` | 2 | `literature-screening-m1-001` | 0.9007 | `SAME_LINEAGE_REVIEW` |
| `crispr-resistance-e2e-001` | `skill-scenario-to-benchmark` | 20 | `crispr-resistance-e2e-001` | 0.8432 | `SAME_LINEAGE_REVIEW` |
| `literature-screening-m1-001` | `skill-scenario-to-benchmark` | 18 | `literature-screening-m1-001` | 0.8298 | `SAME_LINEAGE_REVIEW` |

同一规范化 ID 但文本相似度不足 0.65 的组合仍保留在 JSON 的 `same_lineage_groups`，需要确认是否只是旧版本或残留副本。

## 每道正式题最高重合项

| 当前题目 | 外部仓库 | 外部题目 | 判定 | score |
|---|---|---|---|---:|
| `literature-screening-m1-001` | `skill-scenario-to-benchmark` | `literature-claim-audit-m1-003` | `SHARED_PATTERN_ONLY` | 0.4134 |
| `literature-screening-m1-001` | `skill-scenario-to-benchmark` | `literature-claim-audit-m1-003` | `SHARED_PATTERN_ONLY` | 0.4000 |
| `literature-screening-m1-001` | `skill-scenario-to-benchmark` | `literature-claim-audit-m1-003` | `LOW_OVERLAP` | 0.3977 |
| `eb010-closed-loop-ambiguity-004` | `research-benchmark` | `niche-extrapolation-l4-trial-006` | `LOW_OVERLAP` | 0.3880 |
| `eb010-closed-loop-ambiguity-004` | `skill-scenario-to-benchmark` | `niche-extrapolation-l4-trial-006` | `LOW_OVERLAP` | 0.3871 |
| `eb010-closed-loop-ambiguity-004` | `skill-scenario-to-benchmark` | `niche-extrapolation-l4-trial-005` | `LOW_OVERLAP` | 0.3863 |
| `eb010-closed-loop-ambiguity-004` | `research-benchmark` | `niche-extrapolation-l4-trial-004` | `LOW_OVERLAP` | 0.3857 |
| `eb010-closed-loop-ambiguity-004` | `research-benchmark` | `niche-extrapolation-l4-trial-005` | `LOW_OVERLAP` | 0.3853 |
| `eb014-sequential-evidence-feedback-002` | `research-benchmark` | `crispr-screen-hit-robustness-source-v2` | `LOW_OVERLAP` | 0.3539 |
| `eb014-sequential-evidence-feedback-002` | `research-benchmark` | `crispr-screen-hit-robustness-source-v3` | `LOW_OVERLAP` | 0.3379 |
| `eb012-cross-handoff-audit-001` | `skill-scenario-to-benchmark` | `crispr-screen-hit-robustness-l4-contract-001` | `LOW_OVERLAP` | 0.3317 |
| `eb012-cross-handoff-audit-001` | `skill-scenario-to-benchmark` | `crispr-screen-hit-robustness-l4-contract-001` | `LOW_OVERLAP` | 0.3317 |
| `eb012-cross-handoff-audit-001` | `skill-scenario-to-benchmark` | `md-replica-convergence-l4-contract-001` | `LOW_OVERLAP` | 0.3295 |
| `eb012-cross-handoff-audit-001` | `skill-scenario-to-benchmark` | `md-replica-convergence-l4-contract-001` | `LOW_OVERLAP` | 0.3295 |
| `eb013-shared-setup-routing-003` | `skill-scenario-to-benchmark` | `literature-screening-m1-001` | `LOW_OVERLAP` | 0.3231 |
| `eb012-cross-handoff-audit-001` | `skill-scenario-to-benchmark` | `microscopy-replicate-l4-contract-001` | `LOW_OVERLAP` | 0.3219 |
| `eb013-shared-setup-routing-003` | `skill-scenario-to-benchmark` | `literature-screening-m1-001` | `LOW_OVERLAP` | 0.3174 |
| `eb013-shared-setup-routing-003` | `skill-scenario-to-benchmark` | `literature-screening-m1-001` | `LOW_OVERLAP` | 0.3172 |
| `literature-screening-m1-001` | `research-benchmark` | `research-workflow-stress-test-001` | `LOW_OVERLAP` | 0.3165 |
| `eb013-shared-setup-routing-003` | `research-benchmark` | `literature-screening-m1-001` | `LOW_OVERLAP` | 0.3143 |
| `eb006-signal-noise-004` | `skill-scenario-to-benchmark` | `perturbseq-interaction-001` | `LOW_OVERLAP` | 0.3111 |
| `eb010-adaptive-policy-regret-005` | `research-benchmark` | `crispr-screen-hit-robustness-l5-trace-001` | `LOW_OVERLAP` | 0.3079 |
| `eb012-cross-stage-chain-002` | `skill-scenario-to-benchmark` | `resistance-program-audit-e2e-001` | `LOW_OVERLAP` | 0.3071 |
| `eb010-adaptive-policy-regret-005` | `research-benchmark` | `crispr-screen-hit-robustness-l9-adaptive-001` | `LOW_OVERLAP` | 0.3068 |
| `eb014-sequential-evidence-feedback-002` | `skill-scenario-to-benchmark` | `literature-claim-audit-m1-003` | `LOW_OVERLAP` | 0.3037 |
| `literature-screening-m1-001` | `research-benchmark` | `crispr-screen-hit-robustness-source-v2` | `LOW_OVERLAP` | 0.3023 |
| `eb014-sequential-evidence-feedback-002` | `skill-scenario-to-benchmark` | `ambient-rna-001` | `LOW_OVERLAP` | 0.3011 |
| `eb013-evidence-budget-routing-002` | `skill-scenario-to-benchmark` | `resistance-program-audit-e2e-001` | `LOW_OVERLAP` | 0.3010 |
| `eb014-sequential-evidence-feedback-002` | `skill-scenario-to-benchmark` | `glycan-msms-001` | `LOW_OVERLAP` | 0.2972 |
| `eb013-evidence-budget-routing-002` | `skill-scenario-to-benchmark` | `glycan-msms-001` | `LOW_OVERLAP` | 0.2906 |
| `eb010-adaptive-policy-regret-005` | `research-benchmark` | `microscopy-replicate-l5-trace-001` | `LOW_OVERLAP` | 0.2899 |
| `eb006-signal-noise-004` | `skill-scenario-to-benchmark` | `experimental-design-m2-001` | `LOW_OVERLAP` | 0.2856 |
| `eb012-cross-stage-chain-002` | `skill-scenario-to-benchmark` | `literature-claim-audit-m1-003` | `LOW_OVERLAP` | 0.2837 |
| `eb004-adtte-censoring-002` | `research-benchmark` | `literature-screening-m1-001` | `LOW_OVERLAP` | 0.2831 |
| `eb012-cross-stage-chain-002` | `research-benchmark` | `crispr-screen-hit-robustness-source-v6` | `LOW_OVERLAP` | 0.2827 |
| `eb012-cross-stage-chain-002` | `skill-scenario-to-benchmark` | `ambient-rna-001` | `LOW_OVERLAP` | 0.2822 |
| `eb010-adaptive-policy-regret-005` | `research-benchmark` | `microscopy-replicate-l9-adaptive-001` | `LOW_OVERLAP` | 0.2819 |
| `eb001-split-leakage-001` | `skill-scenario-to-benchmark` | `ambient-rna-001` | `LOW_OVERLAP` | 0.2795 |
| `eb003-replay-provenance-004` | `research-benchmark` | `crispr-screen-hit-robustness-source-v3` | `LOW_OVERLAP` | 0.2785 |
| `eb004-adtte-censoring-002` | `skill-scenario-to-benchmark` | `literature-screening-m1-001` | `LOW_OVERLAP` | 0.2785 |
| `eb008-stock-route-001` | `research-benchmark` | `crispr-screen-hit-robustness-source-v6` | `LOW_OVERLAP` | 0.2767 |
| `biogen-adme-audit-001` | `skill-scenario-to-benchmark` | `ambient-rna-001` | `LOW_OVERLAP` | 0.2749 |
| `eb008-stock-route-001` | `research-benchmark` | `md-replica-convergence-l4-contract-001` | `LOW_OVERLAP` | 0.2746 |
| `eb012-cross-stage-chain-002` | `skill-scenario-to-benchmark` | `md-replica-convergence-l4-contract-001` | `LOW_OVERLAP` | 0.2741 |
| `eb005-normalization-hierarchy-003` | `skill-scenario-to-benchmark` | `md-replica-convergence-l4-contract-001` | `LOW_OVERLAP` | 0.2739 |
| `eb005-normalization-hierarchy-003` | `skill-scenario-to-benchmark` | `md-replica-convergence-l4-contract-001` | `LOW_OVERLAP` | 0.2739 |
| `eb008-route-portfolio-002` | `research-benchmark` | `crispr-screen-hit-robustness-source-v2` | `LOW_OVERLAP` | 0.2732 |
| `eb004-adtte-censoring-002` | `skill-scenario-to-benchmark` | `literature-screening-m1-001` | `LOW_OVERLAP` | 0.2698 |
| `eb013-shared-setup-routing-003` | `research-benchmark` | `research-workflow-stress-test-001` | `LOW_OVERLAP` | 0.2693 |
| `eb013-evidence-budget-routing-002` | `research-benchmark` | `crispr-resistance-e2e-001` | `LOW_OVERLAP` | 0.2684 |
| `biogen-adme-audit-001` | `research-benchmark` | `microscopy-replicate-l4-contract-001` | `LOW_OVERLAP` | 0.2682 |
| `eb004-adtte-censoring-002` | `skill-scenario-to-benchmark` | `literature-screening-m1-001` | `LOW_OVERLAP` | 0.2667 |
| `eb013-cross-context-evidence-portfolio-005` | `skill-scenario-to-benchmark` | `resistance-program-audit-e2e-001` | `LOW_OVERLAP` | 0.2664 |
| `eb013-evidence-budget-routing-002` | `skill-scenario-to-benchmark` | `literature-screening-m1-001` | `LOW_OVERLAP` | 0.2657 |
| `eb013-evidence-budget-routing-002` | `skill-scenario-to-benchmark` | `literature-screening-m1-001` | `LOW_OVERLAP` | 0.2644 |
| `eb011-measurement-request-005` | `skill-scenario-to-benchmark` | `resistance-program-audit-e2e-001` | `LOW_OVERLAP` | 0.2641 |
| `eb008-route-portfolio-002` | `skill-scenario-to-benchmark` | `resistance-program-audit-e2e-001` | `LOW_OVERLAP` | 0.2640 |
| `eb011-measurement-request-005` | `research-benchmark` | `md-replica-convergence-l4-contract-001` | `LOW_OVERLAP` | 0.2640 |
| `biogen-adme-audit-001` | `skill-scenario-to-benchmark` | `experimental-design-m2-001` | `LOW_OVERLAP` | 0.2626 |
| `eb011-measurement-request-005` | `research-benchmark` | `literature-screening-m1-001` | `LOW_OVERLAP` | 0.2594 |
| `eb003-recovery-chain-005` | `skill-scenario-to-benchmark` | `niche-extrapolation-l4-trial-005` | `LOW_OVERLAP` | 0.2587 |
| `eb003-recovery-chain-005` | `research-benchmark` | `niche-extrapolation-l4-trial-005` | `LOW_OVERLAP` | 0.2586 |
| `eb010-next-batch-002` | `research-benchmark` | `niche-extrapolation-l4-trial-005` | `LOW_OVERLAP` | 0.2581 |
| `eb010-next-batch-002` | `skill-scenario-to-benchmark` | `niche-extrapolation-l4-trial-005` | `LOW_OVERLAP` | 0.2580 |
| `eb010-closed-loop-replay-003` | `research-benchmark` | `crispr-resistance-e2e-001` | `LOW_OVERLAP` | 0.2574 |
| `eb011-measurement-request-005` | `research-benchmark` | `crispr-screen-hit-robustness-source-v5` | `LOW_OVERLAP` | 0.2573 |
| `eb003-recovery-chain-005` | `skill-scenario-to-benchmark` | `niche-extrapolation-l4-trial-006` | `LOW_OVERLAP` | 0.2572 |
| `eb003-recovery-chain-005` | `research-benchmark` | `niche-extrapolation-l4-trial-004` | `LOW_OVERLAP` | 0.2571 |
| `eb003-recovery-chain-005` | `research-benchmark` | `niche-extrapolation-l4-trial-006` | `LOW_OVERLAP` | 0.2567 |
| `eb005-normalization-hierarchy-003` | `research-benchmark` | `niche-extrapolation-l4-trial-005` | `LOW_OVERLAP` | 0.2566 |
| `eb010-measurement-value-004` | `research-benchmark` | `l1000-moa-inference-001` | `LOW_OVERLAP` | 0.2562 |
| `eb011-measurement-request-005` | `research-benchmark` | `crispr-screen-hit-robustness-source-v4` | `LOW_OVERLAP` | 0.2561 |
| `eb010-next-batch-002` | `research-benchmark` | `niche-extrapolation-l4-trial-006` | `LOW_OVERLAP` | 0.2560 |
| `eb010-next-batch-002` | `research-benchmark` | `niche-extrapolation-l4-trial-004` | `LOW_OVERLAP` | 0.2557 |
| `eb003-failure-recovery-003` | `research-benchmark` | `l1000-moa-inference-001` | `LOW_OVERLAP` | 0.2556 |
| `eb005-normalization-hierarchy-003` | `skill-scenario-to-benchmark` | `niche-extrapolation-l4-trial-005` | `LOW_OVERLAP` | 0.2555 |
| `eb010-next-batch-002` | `skill-scenario-to-benchmark` | `niche-extrapolation-l4-trial-006` | `LOW_OVERLAP` | 0.2555 |
| `eb001-split-leakage-001` | `research-benchmark` | `md-replica-convergence-l4-contract-001` | `LOW_OVERLAP` | 0.2549 |
| `eb010-adaptive-policy-regret-005` | `skill-scenario-to-benchmark` | `perturbseq-interaction-001` | `LOW_OVERLAP` | 0.2547 |
| `biogen-adme-audit-001` | `research-benchmark` | `research-workflow-stress-test-001` | `LOW_OVERLAP` | 0.2545 |
| `eb009-diversity-coverage-004` | `research-benchmark` | `crispr-screen-hit-robustness-l9-adaptive-001` | `LOW_OVERLAP` | 0.2544 |
| `eb005-normalization-hierarchy-003` | `research-benchmark` | `niche-extrapolation-l4-trial-006` | `LOW_OVERLAP` | 0.2541 |
| `biogen-adme-audit-001` | `research-benchmark` | `microscopy-replicate-l5-trace-001` | `LOW_OVERLAP` | 0.2533 |
| `eb003-replay-provenance-004` | `research-benchmark` | `crispr-screen-hit-robustness-source-v5` | `LOW_OVERLAP` | 0.2524 |
| `eb009-diversity-coverage-004` | `research-benchmark` | `crispr-screen-hit-robustness-l5-trace-001` | `LOW_OVERLAP` | 0.2518 |
| `eb010-measurement-value-004` | `research-benchmark` | `crispr-screen-hit-robustness-source-v2` | `LOW_OVERLAP` | 0.2517 |
| `eb003-replay-provenance-004` | `research-benchmark` | `crispr-screen-hit-robustness-source-v6` | `LOW_OVERLAP` | 0.2514 |
| `eb006-signal-noise-004` | `skill-scenario-to-benchmark` | `niche-extrapolation-l4-trial-006` | `LOW_OVERLAP` | 0.2512 |
| `eb006-signal-noise-004` | `research-benchmark` | `niche-extrapolation-l4-trial-006` | `LOW_OVERLAP` | 0.2500 |
| `eb001-split-leakage-001` | `skill-scenario-to-benchmark` | `literature-claim-audit-m1-003` | `LOW_OVERLAP` | 0.2498 |
| `eb008-stock-route-001` | `research-benchmark` | `literature-screening-m1-001` | `LOW_OVERLAP` | 0.2496 |
| `eb003-replay-provenance-004` | `skill-scenario-to-benchmark` | `microscopy-replicate-l4-contract-001` | `LOW_OVERLAP` | 0.2495 |
| `eb003-replay-provenance-004` | `skill-scenario-to-benchmark` | `microscopy-replicate-l4-contract-001` | `LOW_OVERLAP` | 0.2495 |
| `admiral-adsl-derivation-001` | `research-benchmark` | `crispr-screen-hit-robustness-source-v6` | `LOW_OVERLAP` | 0.2493 |
| `crispr-resistance-e2e-001` | `research-benchmark` | `crispr-screen-hit-robustness-source-v2` | `LOW_OVERLAP` | 0.2488 |
| `eb013-partial-observation-risk-004` | `skill-scenario-to-benchmark` | `niche-extrapolation-l4-trial-006` | `LOW_OVERLAP` | 0.2486 |
| `eb006-signal-noise-004` | `skill-scenario-to-benchmark` | `niche-extrapolation-l4-trial-002` | `LOW_OVERLAP` | 0.2485 |
| `eb013-partial-observation-risk-004` | `research-benchmark` | `niche-extrapolation-l4-trial-006` | `LOW_OVERLAP` | 0.2481 |
| `eb010-distributional-policy-stress-006` | `research-benchmark` | `microscopy-replicate-l9-adaptive-001` | `LOW_OVERLAP` | 0.2479 |
| `eb004-adtte-censoring-002` | `skill-scenario-to-benchmark` | `experimental-design-m2-001` | `LOW_OVERLAP` | 0.2478 |
| `eb010-closed-loop-replay-003` | `skill-scenario-to-benchmark` | `niche-extrapolation-l4-trial-006` | `LOW_OVERLAP` | 0.2476 |
| `eb008-stock-route-001` | `skill-scenario-to-benchmark` | `literature-screening-m1-001` | `LOW_OVERLAP` | 0.2473 |
| `eb010-closed-loop-replay-003` | `research-benchmark` | `niche-extrapolation-l4-trial-002` | `LOW_OVERLAP` | 0.2470 |
| `eb010-closed-loop-replay-003` | `research-benchmark` | `niche-extrapolation-l4-trial-006` | `LOW_OVERLAP` | 0.2469 |
| `eb010-closed-loop-replay-003` | `research-benchmark` | `niche-extrapolation-l4-trial-004` | `LOW_OVERLAP` | 0.2468 |
| `admiral-adsl-derivation-001` | `skill-scenario-to-benchmark` | `microscopy-replicate-l4-contract-001` | `LOW_OVERLAP` | 0.2452 |
| `admiral-adsl-derivation-001` | `skill-scenario-to-benchmark` | `microscopy-replicate-l4-contract-001` | `LOW_OVERLAP` | 0.2452 |
| `eb008-stock-route-001` | `research-benchmark` | `md-replica-convergence-l5-trace-001` | `LOW_OVERLAP` | 0.2452 |
| `eb001-split-leakage-001` | `skill-scenario-to-benchmark` | `resistance-program-audit-e2e-001` | `LOW_OVERLAP` | 0.2449 |
| `eb010-distributional-policy-stress-006` | `research-benchmark` | `microscopy-replicate-l5-trace-001` | `LOW_OVERLAP` | 0.2443 |
| `eb013-partial-observation-risk-004` | `skill-scenario-to-benchmark` | `niche-extrapolation-l4-trial-005` | `LOW_OVERLAP` | 0.2441 |
| `eb001-split-leakage-001` | `skill-scenario-to-benchmark` | `microscopy-replicate-l4-contract-001` | `LOW_OVERLAP` | 0.2437 |
| `eb013-partial-observation-risk-004` | `research-benchmark` | `crispr-resistance-e2e-001` | `LOW_OVERLAP` | 0.2437 |
| `eb013-partial-observation-risk-004` | `research-benchmark` | `niche-extrapolation-l4-trial-005` | `LOW_OVERLAP` | 0.2433 |
| `eb010-measurement-value-004` | `research-benchmark` | `crispr-screen-hit-robustness-l4-contract-001` | `LOW_OVERLAP` | 0.2419 |
| `eb013-cross-context-evidence-portfolio-005` | `skill-scenario-to-benchmark` | `experimental-design-m2-001` | `LOW_OVERLAP` | 0.2384 |
| `admiral-adsl-derivation-001` | `skill-scenario-to-benchmark` | `experimental-design-m2-001` | `LOW_OVERLAP` | 0.2379 |
| `eb013-cross-context-evidence-portfolio-005` | `skill-scenario-to-benchmark` | `literature-screening-m1-001` | `LOW_OVERLAP` | 0.2368 |
| `eb010-next-batch-001` | `skill-scenario-to-benchmark` | `experimental-design-m2-001` | `LOW_OVERLAP` | 0.2355 |
| `eb009-diversity-coverage-004` | `skill-scenario-to-benchmark` | `glycan-msms-001` | `LOW_OVERLAP` | 0.2350 |
| `eb005-batch-normalization-002` | `skill-scenario-to-benchmark` | `ambient-rna-001` | `LOW_OVERLAP` | 0.2345 |
| `eb010-measurement-value-004` | `research-benchmark` | `crispr-screen-hit-robustness-source-v5` | `LOW_OVERLAP` | 0.2342 |
| `eb010-measurement-value-004` | `research-benchmark` | `microscopy-replicate-l5-trace-001` | `LOW_OVERLAP` | 0.2339 |
| `eb008-route-portfolio-002` | `research-benchmark` | `crispr-screen-hit-robustness-source-v3` | `LOW_OVERLAP` | 0.2337 |
| `eb013-cross-context-evidence-portfolio-005` | `research-benchmark` | `literature-screening-m1-001` | `LOW_OVERLAP` | 0.2336 |
| `admiral-adsl-derivation-001` | `research-benchmark` | `research-workflow-stress-test-001` | `LOW_OVERLAP` | 0.2324 |
| `eb010-next-batch-001` | `skill-scenario-to-benchmark` | `glycan-msms-001` | `LOW_OVERLAP` | 0.2322 |
| `eb013-cross-context-evidence-portfolio-005` | `skill-scenario-to-benchmark` | `literature-screening-m1-001` | `LOW_OVERLAP` | 0.2321 |
| `eb008-route-portfolio-002` | `research-benchmark` | `research-workflow-stress-test-001` | `LOW_OVERLAP` | 0.2316 |
| `eb010-distributional-policy-stress-006` | `skill-scenario-to-benchmark` | `ambient-rna-001` | `LOW_OVERLAP` | 0.2285 |
| `eb010-next-batch-001` | `research-benchmark` | `crispr-screen-hit-robustness-source-v2` | `LOW_OVERLAP` | 0.2281 |
| `eb010-next-batch-001` | `research-benchmark` | `crispr-screen-hit-robustness-source-v5` | `LOW_OVERLAP` | 0.2275 |
| `eb005-batch-normalization-002` | `skill-scenario-to-benchmark` | `resistance-program-audit-e2e-001` | `LOW_OVERLAP` | 0.2247 |
| `eb005-batch-normalization-002` | `research-benchmark` | `research-workflow-stress-test-001` | `LOW_OVERLAP` | 0.2218 |
| `eb010-distributional-policy-stress-006` | `research-benchmark` | `crispr-screen-hit-robustness-l9-adaptive-001` | `LOW_OVERLAP` | 0.2214 |
| `eb008-route-portfolio-002` | `skill-scenario-to-benchmark` | `experimental-design-m2-001` | `LOW_OVERLAP` | 0.2207 |
| `crispr-resistance-e2e-001` | `research-benchmark` | `literature-screening-m1-001` | `LOW_OVERLAP` | 0.2203 |
| `eb010-next-batch-001` | `research-benchmark` | `crispr-screen-hit-robustness-source-v4` | `LOW_OVERLAP` | 0.2196 |
| `eb009-diversity-coverage-004` | `research-benchmark` | `l1000-moa-inference-001` | `LOW_OVERLAP` | 0.2193 |
| `eb010-distributional-policy-stress-006` | `research-benchmark` | `crispr-resistance-e2e-001` | `LOW_OVERLAP` | 0.2189 |
| `eb003-failure-recovery-003` | `research-benchmark` | `crispr-screen-hit-robustness-source-v4` | `LOW_OVERLAP` | 0.2173 |
| `eb005-batch-normalization-002` | `skill-scenario-to-benchmark` | `glycan-msms-001` | `LOW_OVERLAP` | 0.2142 |
| `eb003-failure-recovery-003` | `research-benchmark` | `crispr-resistance-e2e-001` | `LOW_OVERLAP` | 0.2131 |
| `eb003-failure-recovery-003` | `research-benchmark` | `crispr-screen-hit-robustness-source-v5` | `LOW_OVERLAP` | 0.2130 |
| `crispr-resistance-e2e-001` | `research-benchmark` | `crispr-screen-hit-robustness-source-v4` | `LOW_OVERLAP` | 0.2129 |
| `crispr-resistance-e2e-001` | `skill-scenario-to-benchmark` | `literature-screening-m1-001` | `LOW_OVERLAP` | 0.2124 |
| `eb005-batch-normalization-002` | `research-benchmark` | `crispr-screen-hit-robustness-source-v4` | `LOW_OVERLAP` | 0.2124 |
| `crispr-resistance-e2e-001` | `research-benchmark` | `crispr-screen-hit-robustness-source-v5` | `LOW_OVERLAP` | 0.2112 |
| `eb009-diversity-coverage-004` | `research-benchmark` | `md-replica-convergence-l5-trace-001` | `LOW_OVERLAP` | 0.2110 |
| `eb003-failure-recovery-003` | `research-benchmark` | `crispr-screen-hit-robustness-l5-trace-001` | `LOW_OVERLAP` | 0.2068 |
| `eb015-real-source-replacement-gate-001` | `skill-scenario-to-benchmark` | `crispr-screen-hit-robustness-l4-contract-001` | `LOW_OVERLAP` | 0.1879 |
| `eb015-real-source-replacement-gate-001` | `skill-scenario-to-benchmark` | `crispr-screen-hit-robustness-l4-contract-001` | `LOW_OVERLAP` | 0.1879 |
| `eb015-real-source-replacement-gate-001` | `skill-scenario-to-benchmark` | `literature-screening-m1-001` | `LOW_OVERLAP` | 0.1750 |
| `eb015-real-source-replacement-gate-001` | `skill-scenario-to-benchmark` | `literature-screening-m1-001` | `LOW_OVERLAP` | 0.1726 |
| `eb015-real-source-replacement-gate-001` | `skill-scenario-to-benchmark` | `literature-screening-m1-001` | `LOW_OVERLAP` | 0.1724 |
| `research-workflow-stress-test-001` | `skill-scenario-to-benchmark` | `crispr-resistance-e2e-001` | `LOW_OVERLAP` | 0.1637 |
| `research-workflow-stress-test-001` | `skill-scenario-to-benchmark` | `crispr-resistance-e2e-001` | `LOW_OVERLAP` | 0.1318 |
| `research-workflow-stress-test-001` | `skill-scenario-to-benchmark` | `crispr-resistance-e2e-001` | `LOW_OVERLAP` | 0.1312 |
| `research-workflow-stress-test-001` | `research-benchmark` | `literature-screening-m1-001` | `LOW_OVERLAP` | 0.0933 |
| `research-workflow-stress-test-001` | `skill-scenario-to-benchmark` | `literature-screening-m1-001` | `LOW_OVERLAP` | 0.0840 |

## 判读规则与限制

- `SAME_LINEAGE_ID_MATCH`：规范化 task id 相同，先视为同一题族；报告按外部仓库归并版本副本。
- `DIRECT_DUPLICATE_CANDIDATE`：题目标题或综合文本高度一致，需要人工确认是否同一题的版本迁移。
- `HIGH_OVERLAP_REVIEW`：语义和结构高度接近，但不能仅凭静态文本判定重复。
- `SHARED_PATTERN_ONLY`：可能共享 workflow、失败模式或设计模块，不计作重复题。
- 同名题若是同一题的不同仓库版本，应保留 lineage、版本、来源和 reference 差异记录；不能把它们当作独立题累计数量。
- 本报告没有访问网络，也没有比较隐藏 verifier/reference truth；正式去重决定仍需人工科学审阅。

原始比较分类计数：`{'SAME_LINEAGE_ID_MATCH': 62, 'SHARED_PATTERN_ONLY': 2, 'LOW_OVERLAP': 8288}`
