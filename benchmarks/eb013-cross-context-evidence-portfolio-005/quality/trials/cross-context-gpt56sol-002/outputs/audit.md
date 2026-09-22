# Audit

Independent-group counts include only records with `quality: "pass"` and `independence: "independent"`. The selected `F1` add supplies independent group G6 for C3, while selected `F4` replaces C2-G2 with quality-reviewed independent group G8. The related F2 replicate is not counted as an independent group.

After applying the selected options, C1 has effects 0.55 and 0.45 (mean 0.50), C2 has 0.50 and 0.41 (mean 0.455), and C3 has 0.48 and 0.44 (mean 0.46). Each context has at least two independent groups, no context contains both threshold-crossing positive and negative effects, and each absolute mean is at least 0.3. Therefore all three contexts are `SUPPORTED` and no pooled shortcut is needed or invalidated.

The follow-up information gain is context-specific: F1 changes C3 from `INSUFFICIENT` (one independent group) to `SUPPORTED`, and F4 changes C2 from `CONFLICTED` to `SUPPORTED` by replacing the negative record. F3 is redundant for an already supported C1, F2 does not increase independent-group count, and F5 leaves the C2 negative record in place and therefore does not resolve its conflict. The selected portfolio costs 2.4, within the budget, and maximizes supported contexts before minimizing conflict, insufficiency, cost, and sorted option IDs.

All decisions are bounded by the claim boundary `context_evidence_only`; they are planning classifications for this synthetic fixture and are not pooled or biological/clinical claims.
