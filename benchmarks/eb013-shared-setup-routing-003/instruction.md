# Prospective evidence routing with shared setup commitments

You plan follow-up assays for a synthetic translational review. All parameters are hypothetical planning values, not experimentally established reductions. Use only data/rules.json, data/requests.json and data/output_contract.json. No previous task or external schema is needed.

Select exactly one stage-1 request and commit to one stage-2 action for every outcome declared by that request. Only one outcome will occur. However, all setup families used anywhere in the policy must be prepared BEFORE observing that outcome. Pay each distinct family setup cost once, even if several branches reuse it. Do not pay only the observed branch's setup; do not add the execution costs of mutually exclusive branches.

An action is legal only when status=current, future_outcome=false, available_at <= decision_date, the observation is allowed, and ALL dependency_ids are satisfied by the chosen stage-1 request. An empty dependency list is satisfied. No other prerequisites are available. Apply the same temporal/status gates to stage-1 requests.

For each uncertainty axis, sum the maximum covers value in each correlation_group across the stage-1 and stage-2 requests. Residual = max(0, initial_uncertainty - that sum - stage1.outcomes[observation].get(axis,0)). Each axis must satisfy its OWN critical_threshold in every branch.

Let S be the sum of setup_costs for the UNION of families across the entire policy. Require stage1.cost <= stage1_budget, stage1.cost + S <= commitment_budget, and stage1.cost + S + max(stage2 execution cost) <= total_budget. Per-state cost includes stage1.cost + S + that state's execution cost. Only policies satisfying every budget and every per-axis threshold are eligible.

Among eligible policies minimize, in order: (1) maximum critical residual across all states and axes, (2) worst-case total cost, (3) S, (4) stage-1 ID lexically, (5) stage-2 action IDs in lexically sorted observation order. If none is eligible, request_information. Comparing each branch independently is insufficient for the shared preparation decision.

Write the following five files. A machine-readable field inventory is in data/output_contract.json. JSON object and row order are irrelevant. Numeric tolerance is 1e-6; finite numeric strings are accepted. Extra explanatory JSON keys are allowed. Required key names below are explicit; no undocumented schema inheritance is required.

- outputs/plan.json: selected fields stage1_request_id (string), stage2_policy (object mapping every observation to an action ID), setup_families (unique string array), setup_cost, worst_case_cost, worst_case_max_critical_residual (numbers). Also policies: one record for EVERY stage-1 input, with stage1_request_id and best_policy. best_policy is null if that stage-1 request has no eligible mapping; otherwise it contains those same six selected fields plus eligible=true for its best eligible policy. You need not output every Cartesian-product candidate.
- outputs/decision.json: the same six selected fields, plus decision="execute_adaptive_route", human_review_required=true, claim_boundary="planning_only". If no eligible policy exists, use decision="request_information", stage1_request_id=null, stage2_policy={}, setup_families=[], and null for all three numeric selected fields in BOTH JSON files; still enumerate all stage-1 records in plan.policies.
- outputs/route.tsv: literal tab-separated header observation, stage2_request_id, residual_uncertainty, cost, eligible. One row per observation of the SELECTED policy, no duplicate or extra states. residual_uncertainty is a JSON object containing every axis; cost is the per-state total cost above; eligible is true/false. Write a header only if there is no eligible policy. TSV quoting follows the usual csv module rules.
- outputs/provenance.json: input_sha256 mapping for ALL THREE JSON files under data/, including output_contract.json itself; use data-relative or data/-prefixed paths. Also rules_version from rules.json, network="off", deterministic=true. Missing or conflicting hashes fail.
- outputs/audit.md: a nonempty explanation of the prospective setup commitment, shared-family accounting, rejected alternatives, and human review boundary. Prose has no keyword or phrase matching requirement; claim permission is checked through decision.json.

The result authorizes a planning recommendation for human review only. It does not authorize experiments or establish scientific efficacy.
