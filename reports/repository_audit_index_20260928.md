# Repository Audit Index

Audit snapshot: 2026-09-28  
Repository: `biomedical-enterprise-harbor-benchmark`  
Scope: latest local benchmark, quality, replay, packaging, and release-gate work

## How To Read This Snapshot

This index is the entry point for auditing the current repository snapshot. It separates:

- **formal release scope**: the 32 task packages listed in `config/task_scope.v1.json`;
- **versioned candidate scope**: additional task packages committed for auditability but still listed under `candidate_only_scope`;
- **evidence artifacts**: quality cards, trial records, replay records, audit reports, package manifests, and SHA-256 sidecars;
- **release gates**: checks that must pass before Harbor publication, even when local tests or target-model trials pass.

`PASS` in a preflight report means that the package may proceed to target-model trial. It does not mean that the task is release-ready. Release status, source status, review status, and replay status remain separate.

## Authoritative Entry Points

| Purpose | File |
|---|---|
| Repository overview and task lineage | `README.md` |
| Enterprise Harbor SOP | `docs/enterprise-harbor-sop-v1.1.md` |
| SOP checker | `scripts/check_enterprise_harbor_sop.py` |
| Task optimization queue | `reports/task_optimization_plan_2026-09-24.md` |
| Quality completeness summary | `reports/quality_completeness_scan_2026-09-24.md` |
| Task standardization audit | `reports/task-standardization-20260924.json` |
| Evidence-surface and abstention audit | `reports/evidence_surface_abstention_audit_2026-09-24.md` |
| Abstention variant gate | `reports/abstention_variant_gate_2026-09-24.md` |
| Per-task repair ledger | `reports/per_task_repair_plans_2026-09-24.md` |
| Fast replay queue | `reports/queue8_replay_checkpoint_2026-09-24.md` and `reports/queue10_fast_gate_check_2026-09-24.md` |
| Packaging inventory | `reports/queue14_packaging_2026-09-24.md` |
| Cross-repository lineage audit | `reports/cross_repo_dedup_audit_2026-09-24.md` |

## Current Counts

These counts intentionally use different denominators:

- Formal release scope: **32** task packages.
- Versioned working-tree scope: **46** task packages.
- Candidate-only additions: **14** packages; they are not formal release tasks until promoted.
- Standardization audit: **46** packages scanned, all with non-empty data and no syntax errors in the recorded scan; `crispr-resistance-e2e-001` remains the one package without a verifier and reference.
- Evidence maps: **11** `claim_evidence_map.tsv` files are present locally.
- Source manifests: **3** `source_manifest.json` files are present locally.
- Frozen source manifests: **0** `source_freeze_manifest.json` files are present locally.
- Named scientific reviews: **0** `scientific_review.json` files are present locally.

The missing source-freeze and scientific-review counts are release blockers, not reasons to discard the calibration evidence.

## Queue Classification

### Immediate fixed-container replay queue

The eight tasks in `reports/queue10_fast_gate_check_2026-09-24.md` have runnable focused tests and structural SOP rechecks recorded:

`eb013-cross-context-evidence-portfolio-005`, `eb014-sequential-evidence-feedback-002`, `eb010-adaptive-policy-regret-005`, `eb010-closed-loop-replay-003`, `eb013-partial-observation-risk-004`, `eb013-shared-setup-routing-003`, `eb006-donor-stratified-signal-005`, and `eb006-research-completion-008`.

The queue is not a release list. Fixed-container replay, durable input/output hashes, and practitioner review remain open.

### Separate repair queue

- `eb015-real-source-replacement-gate-001`: source-rights review, file-level hash freeze, verifier rebind, and a runnable test-entry record.
- `eb006-research-completion-011`: clean target rerun and test-entry repair; the prior scientific mismatch remains recorded.
- Six expanded routing/uncertainty tasks: run mutation controls, four abstention variants, and current-version target calibration before promotion.
- `crispr-resistance-e2e-001`: add verifier/reference and licensed/frozen inputs, or narrow the task to a contract-review task.
- `literature-screening-m1-001` and `research-workflow-stress-test-001`: resolve placeholder/missing DOI and source classification before scientific promotion.

## Release Gate Interpretation

The latest local evidence supports the following statement:

> The repository is an internal synthetic/calibration benchmark snapshot with substantial author-side quality evidence. It is not yet a Harbor release candidate.

Open release gates include fixed-container replay, source rights and byte-level freeze, verifier rebinding where source data changes, independent scientific review, practitioner review, held-out target trials where required, and auditable abstention scoring.

No report in this snapshot should be interpreted as evidence of clinical validity, experimental truth, or target-model defeat unless its report explicitly states that claim and the corresponding release gates are complete.

## Audit Commands

```bash
python3 scripts/check_enterprise_harbor_sop.py benchmarks/<task-id> \
  --output reports/<task-id>-enterprise-sop-preflight.json
python3 scripts/check_task_standardization.py
python3 -m pytest -q
git diff --check
```

For fixed-container work, use the queue reports and preserve the task data fingerprint, container image digest, verifier result, and archive SHA-256 together. Do not overwrite older trial records when a task version or data fingerprint changes.
