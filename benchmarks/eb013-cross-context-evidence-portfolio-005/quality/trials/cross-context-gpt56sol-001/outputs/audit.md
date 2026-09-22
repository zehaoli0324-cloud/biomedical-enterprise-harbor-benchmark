# Audit

The baseline was evaluated separately for C1, C2, and C3. An evidence row
contributes to the independent-group count only when `quality` is `pass` and
`independence` is `independent`; therefore the related C3 replicate in F2 does
not increase C3's count. Replacement F4 removes C2-G2 before the replacement
row is evaluated, while add options leave existing records in place.

With F1 and F4 selected, C1 has two positive independent effects (0.55, 0.45),
C2 has two positive independent effects (0.50, 0.41), and C3 has two positive
independent effects (0.48, 0.44). Each context therefore meets the minimum of
two groups and has an absolute mean at least 0.3, with no positive/negative
threshold conflict. All three decisions are `SUPPORTED`; no context is
`CONFLICTED`, so no pooled-shortcut invalidation is required.

The selected portfolio costs 1.0 + 1.4 = 2.4, within the budget. It maximizes
supported contexts (three), then minimizes conflicts and insufficiency (zero
each). F1 supplies the missing independent C3 evidence, and F4 resolves the
C2 conflict through quality-reviewed replacement. F2 is related only, F3 is
redundant for an already-supported C1, and F5 adds a positive C2 row without
removing the negative row, so none improves the objective within the budget.

The resulting claim is bounded to context-stratified evidence classification
only (`context_evidence_only`). It is a planning fixture, not a biological or
clinical claim, and human review remains required.
