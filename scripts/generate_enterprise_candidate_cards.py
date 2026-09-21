#!/usr/bin/env python3
"""Generate differentiated enterprise candidate-set cards from the source registry.

The profiles are intentionally authored, not inferred from company names. Each
benchmark gets three distinct decision contracts. The generator validates that
the candidates differ in semantic axes and have observable failure/hand-off
contracts before writing deterministic JSON cards.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path


GENERATOR_VERSION = "enterprise-candidate-cards.v1"


def _candidate(
    candidate_id: str,
    decision: str,
    unit: str,
    handoff: str,
    consequence: str,
    axes: list[str],
    failures: list[str],
    artifacts: list[str],
    difficulty: str,
    claim_boundary: str,
) -> dict:
    return {
        "candidate_id": candidate_id,
        "decision": decision,
        "independent_unit": unit,
        "handoff": handoff,
        "error_consequence": consequence,
        "semantic_axes": axes,
        "failure_injections": failures,
        "required_artifacts": artifacts,
        "gpt_difficulty_mechanism": difficulty,
        "shortcut_probes": [
            "company-name or tool-name matching",
            "constant recommendation or always-abstain",
            "copying public benchmark labels or leaderboard answers",
        ],
        "claim_boundary": claim_boundary,
        "selection_status": "PENDING",
    }


PROFILES: dict[str, dict] = {
    "EB001": {
        "workflow_id": "WF-ADME-BLIND",
        "enterprise_role": "DMPK_or_computational_chemist",
        "candidates": [
            _candidate("eb001-split-leakage-001", "Is the molecule split leakage-free at the structure/scaffold level before comparing ADME models?", "molecule and canonical structure", "curated_split->prediction", "leakage inflates apparent model quality and misdirects compound selection", ["split_and_unit", "failure_mode", "evaluation_contract"], ["duplicate structure under different IDs", "scaffold overlap across train/test", "salt or stereochemistry normalization conflict"], ["split_audit.csv", "structure_identity_report.json", "readiness_decision.md"], "entity identity must be resolved before metrics are trusted; a fluent model can otherwise report correct arithmetic on the wrong split", "A split audit cannot establish in vivo efficacy or clinical utility."),
            _candidate("eb001-endpoint-harmonization-002", "Are six ADME endpoints comparable after units, missingness, and assay-version checks?", "molecule-endpoint measurement", "measurement_table->curated_split", "unit or assay drift creates false endpoint rankings and invalid multi-task comparisons", ["business_decision", "data_visibility", "claim_boundary"], ["mixed endpoint units", "missing labels not missing at random", "assay version conflict"], ["endpoint_dictionary.json", "measurement_qc.tsv", "uncertainty_queue.tsv"], "the agent must separate analyzable rows from comparable rows and abstain per endpoint rather than emit one global score", "Harmonized measurements support data readiness only, not biological validity."),
            _candidate("eb001-applicability-triage-003", "Which held-out compounds are sufficiently in-domain for a model-assisted ADME review, and which require human or experimental follow-up?", "held-out compound", "prediction->uncertainty_and_candidate_review", "out-of-domain compounds can be over-prioritized despite favorable aggregate metrics", ["business_decision", "stopping_rule", "handoff"], ["scaffold novelty", "high uncertainty with high predicted rank", "conflicting endpoint signals"], ["applicability_report.json", "candidate_review.tsv", "claim_ledger.tsv"], "ranking, uncertainty, and applicability must be reconciled; the highest prediction is not automatically the next compound", "Applicability review is a prioritization signal, not an efficacy or safety claim."),
        ],
    },
    "EB002": {
        "workflow_id": "WF-ADME-BLIND",
        "enterprise_role": "DMPK_or_computational_chemist",
        "candidates": [
            _candidate("eb002-blind-calibration-001", "Can a model produce a calibrated prospective ADMET submission while preserving blind-test and split provenance?", "molecule across project-time split", "public_training->blind_prediction", "leakage or label peeking invalidates prospective lead decisions", ["data_visibility", "split_and_unit", "claim_boundary"], ["blind labels accidentally exposed", "time split replaced by random split", "prediction file misaligned to compound IDs"], ["submission.csv", "blind_split_manifest.json", "calibration_report.md"], "the agent must reason under hidden labels and prove identifier alignment without optimizing to a visible answer", "Blind challenge performance is not a clinical or in vivo efficacy conclusion."),
            _candidate("eb002-multitask-missingness-002", "Which endpoints can be jointly modeled under structured missingness, and where should the workflow abstain?", "molecule-endpoint pair", "training_matrix->endpoint_review", "improper imputation changes endpoint trade-offs and wastes assay budget", ["scientific_decision", "failure_mode", "stopping_rule"], ["endpoint-specific missingness", "negative values encoded as missing", "task weighting masks weak endpoints"], ["missingness_audit.tsv", "per_endpoint_metrics.json", "abstention_queue.tsv"], "a model must separate missing-label handling from prediction quality and preserve per-endpoint uncertainty", "Predicted ADMET values do not establish measured safety or exposure."),
            _candidate("eb002-prospective-analog-003", "Which analogs merit the next assay round after uncertainty, chemical novelty, and endpoint risk are reconciled?", "analog series", "prediction->experimental_candidate_review", "proxy-optimal analogs can consume assay capacity while hiding selectivity or liability risk", ["business_decision", "handoff", "evaluation_contract"], ["high score with counter-screen liability", "series-level duplicate", "uncertainty ranking reversal"], ["analog_priority.tsv", "uncertainty_report.json", "human_review_queue.md"], "the decision is a constrained portfolio choice, not a leaderboard sort; equivalent candidates and hold decisions must be represented", "The output recommends assay priority only and does not claim activity in vivo."),
        ],
    },
    "EB003": {
        "workflow_id": "WF-COMPBIO-TASK",
        "enterprise_role": "bioinformatics_or_research_analyst",
        "candidates": [
            _candidate("eb003-input-contract-001", "Are the multimodal inputs, identifiers, references, and tool versions sufficient to start the analysis?", "sample/task input bundle", "raw_files->validated_inputs", "wrong mapping or reference version produces an irreproducible and scientifically invalid artifact", ["enterprise_context", "failure_mode", "reproducibility"], ["sample-sheet mismatch", "unsupported file schema", "reference/tool unavailable offline"], ["input_manifest.json", "schema_audit.json", "start_or_stop_report.md"], "the model must stop early when a prerequisite fails and preserve a minimal information request instead of fabricating results", "Input validation does not establish a biological finding."),
            _candidate("eb003-claim-ledger-002", "Which claims are supported by the produced computational artifact, and which require downgrade or human review?", "claim linked to result artifact", "analysis->claim_ledger", "a plausible figure can be misread as causal or clinical evidence", ["claim_boundary", "visible_evidence", "handoff"], ["association-only output", "figure/table mismatch", "missing provenance locator"], ["claim_ledger.tsv", "evidence_table.tsv", "final_report.md"], "evidence locators, uncertainty, and claim language must stay synchronized across artifacts", "A computational result is not automatically causal, clinical, or experimentally confirmed."),
            _candidate("eb003-failure-recovery-003", "After one tool branch fails or returns partial output, can the analyst recover without silently changing the scientific question?", "analysis branch and artifact state", "analysis->execution_log->claim_ledger", "silent fallback or parameter drift makes later results incomparable and unauditable", ["tool_call_complexity", "stateful_dependency", "failure_mode"], ["partial output", "version/interface drift", "resource timeout"], ["execution_log.jsonl", "failure_recovery.md", "rerun_manifest.json"], "the agent must preserve failed state, choose an equivalent route or stop, and prove that downstream claims use the recovered branch", "A recovered computational branch still requires scientific and human review."),
            _candidate("eb003-replay-provenance-004", "Can a delivered computational artifact be replayed from its recorded provenance and environment after handoff?", "analysis artifact and execution manifest", "analysis->reproduction_review", "an untraceable artifact can be accepted despite hidden version, checksum, or nondeterminism drift", ["reproducibility", "evidence_reconciliation", "evaluation_contract"], ["missing input checksum", "package or reference drift", "nondeterministic rerun", "artifact-manifest mismatch"], ["replay_manifest.json", "provenance_diff.tsv", "handoff_replay_report.md"], "the model must reconcile artifact claims with hashes, versions, and rerun outputs and route unexplained differences to review", "A successful replay supports computational reproducibility only; it does not validate the biological interpretation."),
        ],
    },
    "EB004": {
        "workflow_id": "WF-ADAM-DERIVATION",
        "enterprise_role": "statistical_programmer",
        "candidates": [
            _candidate("eb004-adsl-population-001", "Can subject-level treatment dates and ITT/SAFFL/PPROTFL flags be derived under frozen study rules?", "subject", "SDTM->ADSL_or_ADTTE", "wrong population membership or treatment dates changes the estimand", ["business_decision", "split_and_unit", "failure_mode"], ["screen failure", "no exposure", "missing end date", "cutoff capping"], ["adsl.csv", "derivation_trace.csv", "audit_report.json"], "one-to-many exposure rows must be reconciled to subject-level flags while preserving rule provenance and hold conditions", "The derivation is a synthetic data-quality handoff, not a clinical conclusion."),
            _candidate("eb004-adtte-censoring-002", "Which subject-level event and censoring dates are valid for a prespecified ADTTE endpoint?", "subject-parameter-event record", "ADSL->ADTTE->table_or_analysis", "incorrect censoring changes the survival estimand and downstream table", ["scientific_decision", "evaluation_contract", "claim_boundary"], ["event date after cutoff", "partial date", "competing event", "missing follow-up"], ["adtte.csv", "event_trace.csv", "censoring_audit.json"], "the model must distinguish endpoint rules from generic date arithmetic and route ambiguous records to review", "An ADTTE derivation does not establish treatment benefit or regulatory validity."),
            _candidate("eb004-rule-mutation-003", "Does a derivation implementation obey the declared SDTM-to-ADaM rules under adversarial edge-case mutations?", "subject-rule assertion", "derivation_code->review_record", "a plausible table can pass superficial review while violating a study rule", ["failure_mode", "evaluation_contract", "tool_and_trace_reliability"], ["mutated arm code", "reordered exposure rows", "missing source row", "rule version drift"], ["rule_matrix.csv", "counterexample_report.json", "rerun_manifest.json"], "the agent must distinguish equivalent implementations from silent rule changes and identify the earliest failing assertion", "Rule conformance is not evidence of sponsor data quality or clinical analysis validity."),
        ],
    },
    "EB005": {
        "workflow_id": "WF-PHENOMICS-PROFILE",
        "enterprise_role": "image_analysis_or_phenomics_scientist",
        "candidates": [
            _candidate("eb005-plate-leakage-001", "Does a plate/compound split support honest phenotype retrieval without replicate leakage?", "well/plate and perturbation identity", "images_and_metadata->profiles", "plate leakage inflates retrieval and makes morphology claims non-transferable", ["split_and_unit", "failure_mode", "evaluation_contract"], ["same compound across train/test", "well-level split used for compound-level claim", "control wells duplicated"], ["split_manifest.json", "metadata_join_audit.tsv", "holdout_metrics.json"], "the agent must choose the independent unit before computing similarity and detect leakage hidden by well-level sample counts", "Retrieval performance does not prove target mechanism or therapeutic efficacy."),
            _candidate("eb005-batch-normalization-002", "Which normalization and replicate aggregation choices remove batch effects without erasing a real phenotype?", "plate-level replicate aggregate", "profiles->batch_diagnostics", "over-correction can erase biology while under-correction creates false hits", ["method_choice", "failure_mode", "stopping_rule"], ["batch confounding", "control drift", "replicate imbalance"], ["normalization_comparison.tsv", "batch_report.json", "sensitivity_summary.md"], "the model must compare plausible preprocessing branches and report conclusions that change under normalization", "Batch correction supports analytical robustness, not mechanism confirmation."),
            _candidate("eb005-mechanism-retrieval-003", "Which phenotype-similar perturbations are safe to pass to mechanism review, and what remains unproven?", "compound/perturbation profile", "profiles->retrieval_or_DTI_rank", "morphological similarity can be overinterpreted as a target relationship", ["business_decision", "claim_boundary", "handoff"], ["similarity driven by toxicity", "unseen cell state", "weak annotation evidence"], ["retrieval_rank.tsv", "evidence_boundary.json", "human_review_queue.md"], "ranking must be separated from causal interpretation and linked to metadata and uncertainty", "Morphological similarity is not proof of target mechanism or clinical efficacy."),
        ],
    },
    "EB006": {
        "workflow_id": "WF-PHENOMICS-PROFILE",
        "enterprise_role": "image_analysis_or_phenomics_scientist",
        "candidates": [
            _candidate("eb006-unseen-perturbation-001", "Do learned representations generalize to unseen perturbations rather than memorizing plate or compound identity?", "unseen perturbation", "images_and_metadata->zero_shot_prediction", "memorization creates false confidence in novel target or drug prioritization", ["split_and_unit", "data_visibility", "evaluation_contract"], ["perturbation overlap", "plate batch shortcut", "label leakage in embeddings"], ["holdout_manifest.json", "zero_shot_metrics.json", "representation_audit.md"], "the model must reason about entity-level holdout and distinguish representation quality from benchmark leakage", "Zero-shot phenotype prediction is not target validation or therapeutic efficacy."),
            _candidate("eb006-metadata-confounding-002", "Can batch and metadata confounding be separated from a putative drug-target interaction signal?", "plate/compound perturbation", "profiles->batch_diagnostics", "confounding can produce a false mechanism assignment and waste follow-up work", ["scientific_judgment", "failure_mode", "claim_boundary"], ["batch aligned with treatment", "missing plate metadata", "control imbalance"], ["metadata_conflict_report.json", "batch_sensitivity.tsv", "claim_ledger.tsv"], "the agent must identify non-identifiability and downgrade the mechanism claim instead of selecting a preferred story", "A batch-adjusted association is not causal target evidence."),
            _candidate("eb006-dti-priority-003", "Which drug-target links merit orthogonal review after phenotype ranking, uncertainty, and annotation quality are combined?", "drug-target link", "profiles->DTI_rank->human_review", "high-ranked links with weak annotation may misdirect expensive validation", ["business_decision", "handoff", "uncertainty"], ["ranking instability", "annotation conflict", "out-of-domain cell state"], ["dti_priority.tsv", "uncertainty_report.json", "review_decision.md"], "the decision is a multi-evidence triage, not a single metric sort; abstention must be available", "A ranked link is a hypothesis for review, not a confirmed mechanism."),
            _candidate("eb006-signal-noise-004", "Does a perturbation-level phenotype signal survive nuisance and plate-noise checks before it is passed to profile review?", "perturbation-level signal estimate with plate replicates", "images_and_metadata->signal_noise_diagnostics->profile_review", "technical variation can be mistaken for a biological hit and consume follow-up capacity", ["method_choice", "data_multimodal_join", "stopping_rule"], ["plate-correlated treatment", "control drift", "replicate imbalance", "missing control wells"], ["signal_noise_report.json", "replicate_diagnostics.tsv", "profile_review_gate.md"], "the model must compare raw and nuisance-adjusted signal, preserve replicate-level provenance, and hold when the biological effect is not identifiable", "A residual phenotype signal supports analytical triage only; it does not establish mechanism, target engagement, or efficacy."),
        ],
    },
    "EB007": {
        "workflow_id": "WF-FEP-AUDIT",
        "enterprise_role": "computational_chemist",
        "candidates": [
            _candidate("eb007-ligand-mapping-001", "Are protein, ligand, atom mapping, and reference-state choices valid before comparing relative free-energy predictions?", "protein-ligand edge", "system_manifest->FEP_analysis", "mapping errors make RMSE and rank comparisons scientifically meaningless", ["data_multimodal_join", "failure_mode", "reproducibility"], ["ligand identity mismatch", "atom-map inconsistency", "reference edge disconnected"], ["system_manifest.json", "mapping_audit.tsv", "invalid_edge_report.md"], "the agent must validate system identity and graph connectivity before trusting numerical metrics", "A valid system manifest does not establish binding or efficacy."),
            _candidate("eb007-outlier-sensitivity-002", "Does the FEP ranking remain defensible after outlier and uncertainty sensitivity analysis?", "ligand series and edge set", "prediction->error_and_outlier_review", "one unstable edge can reverse compound prioritization", ["method_choice", "uncertainty", "stopping_rule"], ["outlier dominates RMSE", "sparse edge graph", "replicate disagreement"], ["error_distribution.json", "sensitivity_table.tsv", "outlier_review.md"], "the model must separate metric improvement from decision stability and report rank reversals", "Error/rank stability is not a measured binding or clinical claim."),
            _candidate("eb007-prospective-ranking-003", "Which ligand changes are sufficiently supported for human review under a fixed FEP budget?", "prospective ligand candidate", "ranking->medicinal_chemistry_review", "proxy-optimal ranking can consume synthesis capacity while hiding uncertainty", ["business_decision", "handoff", "claim_boundary"], ["high score with unstable edge", "novel chemistry outside reference set", "budget conflict"], ["candidate_rank.tsv", "uncertainty_report.json", "approval_gate.md"], "the task requires a bounded go/hold/review decision and cannot be solved by sorting predicted values", "A computational ranking is not experimental affinity or developability evidence."),
        ],
    },
    "EB008": {
        "workflow_id": "WF-ROUTE-AND-DESIGN",
        "enterprise_role": "medicinal_chemist_or_design_scientist",
        "candidates": [
            _candidate("eb008-stock-route-001", "Which retrosynthesis routes satisfy target structure, stock inventory, reaction validity, and search-budget constraints?", "target molecule and route", "target_and_constraints->search->structure_validation", "an invalid or unavailable route wastes chemistry review time", ["business_decision", "failure_mode", "evaluation_contract"], ["stock violation", "invalid reaction template", "route duplicate", "budget truncation"], ["route_table.tsv", "stock_compliance.json", "route_review.md"], "route existence, stock compliance, and structural validity are separate gates; the best score is not automatically usable", "A computational route is not proof of experimental synthesizability."),
            _candidate("eb008-route-evidence-002", "Which route claims are supported by explicit reaction and structure checks, and which require chemist review?", "route step and evidence item", "search->structure_validation->human_review", "unsupported route confidence can lead to infeasible synthesis planning", ["claim_boundary", "visible_evidence", "handoff"], ["missing reaction evidence", "ambiguous stereochemistry", "model score mistaken for feasibility"], ["route_evidence.tsv", "claim_ledger.tsv", "human_review_queue.md"], "the model must align each route claim to checks and maintain uncertainty when the public workflow does not prove feasibility", "Route evidence is computational and does not establish laboratory success."),
            _candidate("eb008-search-recovery-003", "After search exhaustion or a failed policy/filter branch, can the workflow recover without relaxing constraints silently?", "search branch and route state", "search->failure_log->human_review", "silent constraint relaxation can produce unsafe or unusable candidates", ["tool_call_complexity", "stateful_dependency", "safety"], ["empty output", "policy-model version drift", "timeout", "fallback changes stock set"], ["search_log.jsonl", "failure_recovery.md", "constraint_diff.json"], "the model must preserve failed state and explicitly request approval before any constraint change", "Recovery does not make a route experimentally validated."),
        ],
    },
    "EB009": {
        "workflow_id": "WF-ROUTE-AND-DESIGN",
        "enterprise_role": "medicinal_chemist_or_design_scientist",
        "candidates": [
            _candidate("eb009-constraint-generation-001", "Which generated molecules satisfy scaffold, validity, uniqueness, and fixed property constraints?", "generated molecule", "configuration->candidate_set->human_review", "invalid or duplicate candidates waste design and synthesis review", ["business_decision", "failure_mode", "evaluation_contract"], ["invalid SMILES", "scaffold violation", "duplicate collapse", "property constraint mismatch"], ["candidate_set.smi", "constraint_report.tsv", "generation_manifest.json"], "the model must verify each constraint independently instead of trusting aggregate reward", "Constraint satisfaction is not evidence of biological activity."),
            _candidate("eb009-proxy-robustness-002", "Does candidate prioritization remain stable when proxy weights, seeds, or model uncertainty change?", "candidate set and scoring configuration", "generation->sensitivity_review", "proxy gaming can select molecules that look good only under one scoring recipe", ["method_choice", "uncertainty", "stopping_rule"], ["weight sensitivity", "seed instability", "component score conflict"], ["sensitivity_matrix.tsv", "score_breakdown.json", "robustness_report.md"], "the agent must distinguish objective score from decision stability and identify when no candidate is robust", "Proxy robustness does not establish activity, selectivity, or safety."),
            _candidate("eb009-novelty-review-003", "Which generated candidates are novel enough and sufficiently evidenced for medicinal-chemistry review?", "scaffold/candidate family", "candidate_set->novelty_audit->human_review", "novelty or IP-like claims based on a limited reference set can misdirect review", ["enterprise_context", "claim_boundary", "handoff"], ["reference-set leakage", "near-duplicate scaffold", "unsupported novelty claim"], ["novelty_audit.tsv", "similarity_evidence.json", "approval_gate.md"], "the model must separate computed similarity from legal or commercial novelty and retain a review gate", "Computed novelty is not freedom-to-operate or clinical value."),
            _candidate("eb009-diversity-coverage-004", "Does the generated candidate set cover the intended scaffold and chemical space before synthesis review?", "candidate set and scaffold cluster", "generation->diversity_audit->human_review", "mode collapse or representation errors can waste synthesis capacity on near-duplicates", ["data_multimodal_join", "evaluation_contract", "coverage"], ["scaffold collapse", "near-duplicate cluster", "invalid structure representation", "sampling budget skew"], ["diversity_matrix.tsv", "scaffold_cluster_report.json", "coverage_review_gate.md"], "the model must distinguish objective score from chemical-space coverage and hold when diversity cannot be measured reliably", "Computed diversity supports portfolio triage only; it does not establish activity or developability."),
        ],
    },
    "EB010": {
        "workflow_id": "WF-BAYBE-CLOSED-LOOP",
        "enterprise_role": "experimental_design_scientist",
        "candidates": [
            _candidate("eb010-next-batch-001", "Which next experiment batch is valid under search-space, material, and budget constraints?", "candidate experiment", "completed_experiments->next_batch", "invalid or infeasible batches waste scarce experimental capacity", ["business_decision", "failure_mode", "evaluation_contract"], ["constraint violation", "duplicate experiment", "material budget overflow"], ["next_batch.csv", "constraint_check.json", "selection_rationale.md"], "the model must produce a legal batch and explain trade-offs rather than maximize a proxy alone", "A selected batch is a planning recommendation, not an experimental result."),
            _candidate("eb010-stop-uncertainty-002", "Should the closed loop continue, stop, or request more information given uncertainty and observed improvement?", "optimization state and candidate batch", "batch_result->uncertainty->stop_or_continue", "continuing after a non-identifiable or exhausted loop wastes experiments", ["stopping_rule", "uncertainty", "handoff"], ["uncertainty collapse", "plateau hidden by noise", "missing outcome", "model disagreement"], ["stop_rule_report.json", "uncertainty_table.tsv", "human_review.md"], "the model must justify a stop/continue/review action using stateful evidence and allow abstention", "A simulated objective is not proof of real-world improvement."),
            _candidate("eb010-closed-loop-replay-003", "Does a proposed next-batch policy remain budget-compliant and decision-stable across a fixed simulated replay?", "closed-loop trajectory", "policy->simulated_replay->approval", "a policy that wins one replay while violating budget or changing under seed noise is not deployable", ["evaluation_contract", "reproducibility", "stateful_dependency"], ["seed sensitivity", "budget drift", "action leakage from future outcomes"], ["replay_log.jsonl", "budget_audit.json", "policy_review.md"], "the model must preserve temporal causality and compare policy value with legal and reproducible execution", "Replay performance does not establish laboratory or commercial benefit."),
            _candidate("eb010-measurement-value-004", "Which additional measurement should be requested before the next experiment batch to reduce decision-critical uncertainty?", "candidate measurement request and optimization state", "optimization_state->measurement_request->next_batch", "redundant or infeasible measurements consume budget without resolving the decision bottleneck", ["scientific_decision", "data_visibility", "evidence_reconciliation"], ["correlated uncertainty", "missing outcome", "assay infeasibility", "future-outcome leakage"], ["measurement_priority.tsv", "information_value_audit.json", "approval_request.md"], "the model must link each measurement request to a current uncertainty and avoid using future outcomes when estimating information value", "An information-value ranking is a planning aid, not evidence of experimental improvement."),
        ],
    },
    "EB011": {
        "workflow_id": "WF-FEP-AUDIT",
        "enterprise_role": "computational_chemist_or_method_auditor",
        "candidates": [
            _candidate("eb011-reproduction-manifest-001", "Can reported FEP results be reproduced from a fixed protein-ligand-system manifest and pinned configuration?", "protein-ligand system", "system_manifest->reproduction", "untracked system or configuration drift makes published errors unauditable", ["reproducibility", "data_visibility", "failure_mode"], ["missing system file", "parameter drift", "reference mismatch", "non-deterministic rerun"], ["reproduction_manifest.json", "rerun_results.tsv", "difference_report.md"], "the agent must separate rerun failure from scientific disagreement and preserve input hashes", "Reproduction status does not validate the underlying biological claim."),
            _candidate("eb011-method-attribution-002", "Which error differences are attributable to system selection, method configuration, or evaluation metric?", "method-system-metric tuple", "results->error_attribution->review", "misattributing an error source leads to the wrong method or dataset change", ["method_choice", "evidence_reconciliation", "evaluation_contract"], ["metric disagreement", "system subset confounding", "outlier dominance"], ["error_attribution.tsv", "subset_sensitivity.json", "method_review.md"], "the model must reason across linked results and avoid declaring a winner from one aggregate metric", "Benchmark error attribution is not a claim of prospective binding performance."),
            _candidate("eb011-outlier-claim-003", "Which systems require human review before a benchmark result is used to support a method or project decision?", "outlier system and reported claim", "error_distribution->human_review", "unreviewed outliers can distort method choice and downstream project confidence", ["business_decision", "claim_boundary", "handoff"], ["unstable outlier", "missing experimental context", "system-level rank reversal"], ["outlier_queue.tsv", "claim_ledger.tsv", "approval_gate.md"], "the model must route unresolved cases to review rather than optimize the headline score", "A benchmark outlier review does not establish clinical or commercial value."),
        ],
    },
    "EB012": {
        "workflow_id": "WF-ADME-BLIND",
        "enterprise_role": "DMPK_or_computational_chemist",
        "candidates": [
            _candidate("eb012-phased-blind-001", "Can prospective PXR potency predictions remain calibrated across phased blind releases without label leakage?", "analog series across phase split", "training_phase->blind_prediction->phase_update", "leakage or phase mixing invalidates lead-optimization decisions", ["data_visibility", "split_and_unit", "reproducibility"], ["phase label leakage", "analog identity collision", "submission schema mismatch"], ["phase_manifest.json", "blind_predictions.csv", "calibration_update.md"], "the model must maintain state across phases, preserve hidden-label boundaries, and update uncertainty without retroactive answers", "Blind potency prediction is not measured efficacy or clinical safety."),
            _candidate("eb012-potency-selectivity-002", "Which analogs balance PXR potency with counter-screen selectivity and uncertainty for follow-up?", "analog and endpoint pair", "prediction->selectivity_review", "optimizing potency alone can increase off-target liability and waste assay budget", ["business_decision", "failure_mode", "claim_boundary"], ["potency/selectivity trade-off", "missing counter-screen", "rank instability"], ["tradeoff_table.tsv", "uncertainty_report.json", "candidate_review.md"], "the agent must reason over competing endpoints and expose Pareto or hold cases instead of one scalar ranking", "Predicted potency/selectivity is a prioritization signal, not an experimental result."),
            _candidate("eb012-analog-expansion-003", "Should the next analog expansion proceed, pause, or request new measurements based on blind predictions and evidence coverage?", "analog series and evidence state", "phase_update->experimental_candidate_review", "premature expansion consumes chemistry and assay capacity under weak evidence", ["stopping_rule", "handoff", "evidence_quality"], ["sparse series coverage", "uncertainty concentration", "counter-screen contradiction"], ["expansion_decision.json", "evidence_coverage.tsv", "human_review_queue.md"], "the model must make a bounded proceed/pause/review decision with explicit missing information", "An expansion decision does not establish in vivo efficacy or clinical utility."),
        ],
    },
}


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def _validate_profiles(registry: list[dict]) -> None:
    registry_ids = {row.get("benchmark_id") for row in registry}
    missing = sorted(set(PROFILES) - registry_ids)
    if missing:
        raise ValueError(f"profiles reference unknown benchmark IDs: {missing}")
    all_ids: set[str] = set()
    for benchmark_id, profile in PROFILES.items():
        candidates = profile.get("candidates", [])
        if not 3 <= len(candidates) <= 5:
            raise ValueError(f"{benchmark_id} must have 3-5 candidates")
        fingerprints: set[tuple[str, str, str]] = set()
        axis_sets: list[set[str]] = []
        for candidate in candidates:
            candidate_id = candidate["candidate_id"]
            if candidate_id in all_ids:
                raise ValueError(f"duplicate candidate_id: {candidate_id}")
            all_ids.add(candidate_id)
            if len(candidate["semantic_axes"]) < 3:
                raise ValueError(f"{candidate_id} needs at least 3 semantic axes")
            if not candidate["failure_injections"] or not candidate["required_artifacts"]:
                raise ValueError(f"{candidate_id} needs failure injections and artifacts")
            fingerprint = (
                candidate["decision"].lower(),
                candidate["independent_unit"].lower(),
                candidate["handoff"].lower(),
            )
            if fingerprint in fingerprints:
                raise ValueError(f"surface-duplicate candidate in {benchmark_id}: {candidate_id}")
            fingerprints.add(fingerprint)
            axis_sets.append(set(candidate["semantic_axes"]))
        for index, left in enumerate(axis_sets):
            for right in axis_sets[index + 1 :]:
                if len(left.symmetric_difference(right)) < 2:
                    raise ValueError(f"candidates in {benchmark_id} differ on fewer than two semantic axes")


def generate(root: Path, out: Path) -> dict:
    registry_path = root / "knowledge_base/registry/enterprise_benchmarks.jsonl"
    registry = [json.loads(line) for line in registry_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    _validate_profiles(registry)
    registry_by_id = {row["benchmark_id"]: row for row in registry}
    out.mkdir(parents=True, exist_ok=True)
    cards: list[dict] = []
    for benchmark_id in sorted(PROFILES):
        profile = PROFILES[benchmark_id]
        source = registry_by_id[benchmark_id]
        card = {
            "schema_version": "enterprise_candidate_set_card.v1",
            "candidate_set_id": f"CSET-{benchmark_id}-SCALED-V1",
            "source_benchmark_id": benchmark_id,
            "workflow_id": profile["workflow_id"],
            "source_name": source["name"],
            "enterprise_role": profile["enterprise_role"],
            "candidates": profile["candidates"],
            "deduplication_axes": ["decision", "independent_unit", "error_consequence", "handoff", "semantic_axes"],
            "selection_gate": {
                "minimum_candidates": 3,
                "maximum_candidates": 5,
                "require_two_semantic_differences": True,
                "require_enterprise_value_card": True,
                "require_independent_review": True,
                "require_positive_negative_invariance_controls": True,
            },
            "source_evidence": {
                "registry_record": "knowledge_base/registry/enterprise_benchmarks.jsonl",
                "workflow_record": "knowledge_base/registry/workflows.jsonl",
                "evidence_status": source.get("evidence_status", "observed"),
                "authenticity_class": source.get("authenticity_class", "S"),
                "license_status": source.get("license_status", "verify_pending"),
            },
            "status": "DRAFT",
        }
        path = out / f"{benchmark_id}-{_slug(source['name'])}-candidate-set.json"
        path.write_text(json.dumps(card, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        cards.append({"benchmark_id": benchmark_id, "path": str(path.relative_to(root)), "candidate_count": len(profile["candidates"]), "sha256": digest})
    manifest = {
        "schema_version": "enterprise_candidate_matrix.v1",
        "generator": GENERATOR_VERSION,
        "source_registry": "knowledge_base/registry/enterprise_benchmarks.jsonl",
        "workflow_registry": "knowledge_base/registry/workflows.jsonl",
        "benchmark_count": len(cards),
        "candidate_count": sum(item["candidate_count"] for item in cards),
        "semantic_deduplication": {"minimum_candidates_per_benchmark": 3, "minimum_symmetric_axis_difference": 2},
        "status": "DRAFT",
        "cards": cards,
    }
    (out / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--out", type=Path, default=Path("candidate_pools/enterprise-v1"))
    args = parser.parse_args()
    manifest = generate(args.root.resolve(), (args.root / args.out).resolve())
    print(f"generated {manifest['benchmark_count']} candidate cards with {manifest['candidate_count']} candidates")
    print(f"semantic deduplication: {manifest['semantic_deduplication']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
