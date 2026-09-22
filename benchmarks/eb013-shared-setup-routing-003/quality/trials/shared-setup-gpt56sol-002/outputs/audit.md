# Prospective route audit

The selected planning route starts with stage-1 request `P01`. Before any outcome is observed, the policy commits to the three branch actions `M01` (`high`), `M05` (`low`), and `M08` (`mid`). Their setup families are the union `{F1, F3}`, so the preparation cost is paid once as `2.0 + 2.0 = 4.0`, even though only one branch will execute. The branch execution costs are then added only for the realized outcome; the resulting per-state totals are 6.5, 6.8, and 6.8.

All three selected branches meet both axis thresholds. The selected route has worst-case critical residual 0.23 and worst-case total cost 6.8. The best eligible route for `P02` is `M03/M06/M09`, with residual 0.25 and cost 5.1; `P03` has no eligible complete mapping. Routes that looked cheaper on execution alone were rejected when their shared setup union or branch residuals were evaluated, and mutually exclusive execution costs were not added together.

This is a prospective planning recommendation only. `human_review_required` is true and the claim boundary is `planning_only`; the output does not authorize experiments or establish scientific efficacy.
