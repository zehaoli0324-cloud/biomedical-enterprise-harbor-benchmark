# Decision-critical measurement prioritization

Choose one additional measurement to request before the next experiment batch. Rank measurement options using only the frozen current optimization state. This task selects a measurement request; it does not select the next experiment batch, decide whether the program should stop, or claim that a policy replay improved outcomes.

Eligibility is conjunctive. A measurement is eligible only when current_outcome_status is missing, assay_feasible is true, uses_future_outcome is false, and cost is no greater than max_cost in rules.json. Report every option, including ineligible options. Use these exclusion reasons in this order when applicable: outcome_already_observed, assay_infeasible, future_outcome_leakage, over_budget. Join multiple reasons with a semicolon.

For each option calculate:

- raw_information_gain = current_uncertainty * decision_sensitivity * expected_variance_reduction
- redundancy_penalty = raw_information_gain * abs(correlation_with_existing)
- net_information_value = (raw_information_gain - redundancy_penalty) / cost

Round reported numeric values to six decimal places using decimal round-half-up. Rank eligible options by descending net_information_value, breaking exact ties by measurement_id in ascending lexical order. Ineligible options have a blank rank. Select the rank-1 measurement. The formula_id is decision-information-value-v1.

Write exactly these files under outputs/:

- outputs/measurement_priority.tsv with columns measurement_id, candidate_id, eligible, exclusion_reason, raw_information_gain, redundancy_penalty, net_information_value, and rank. Encode eligible as true or false.
- outputs/information_value_audit.json with selected_measurement_id, eligible_count, max_cost, rules_version, formula_id, input_sha256 keyed by measurement_options.csv and rules.json, and claim_boundary containing experimental_improvement_established: false and human_review_required: true.
- outputs/approval_request.md naming the selected measurement, the uncertainty addressed, the feasibility and future-outcome leakage review, the redundancy assessment, and the required human review. State that the ranking is a planning aid and is not evidence of experimental improvement.
