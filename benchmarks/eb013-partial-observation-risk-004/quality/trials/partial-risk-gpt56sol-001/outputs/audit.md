# Audit

Evidence was resolved independently for every catalog action using only snapshots published on or before the decision date of 2026-09-22. A revision 1 active snapshot was selected for A, C, and D. B selected revision 2 (2026-09-15), which supersedes revision 1. E selected revision 2 (2026-09-20) and is withdrawn, so E is disabled without fallback. F has no snapshot at or before the decision date and is unavailable. The evidence-resolution `usable` flag reflects this evidence status and does not depend on probe capabilities.

The selected probe is P2. Its observable labels induce the executable policy `a -> B`, `b -> A`, `c -> B`, and `d -> C`; worlds sharing a label therefore receive the same action. The policy uses the `basic` and `select` setup families, with setup cost 1.5. Probe cost is 0.8, so the upfront commitment is 2.3. Per-world total costs are 3.1 in W1 and W4, 3.5 in W2 and W3, and 3.2 in W5 and W6; the worst cost is 3.5 and all budgets are satisfied.

Using the selected evidence, losses by world are 0.10, 0.22, 0.22, 0.18, 0.11, and 0.12 for W1 through W6. For each probability model, mean loss is probability-weighted. CVaR uses exactly the worst 0.4 probability mass, taking fractional mass at the boundary when needed: nominal mean/CVaR are 0.1565/0.215, shift are 0.1475/0.1975, and rare are 0.156/0.205. Thus robust CVaR is 0.215 and worst mean loss is 0.1565.

The best feasible alternatives by probe are P0 (all labels use A; robust CVaR 0.22, worst mean 0.22, worst cost 2.2) and P1 (`a -> B`, `b -> C`, `c -> A`, `d -> C`; robust CVaR 0.22, worst mean 0.158, worst cost 3.6). P2 improves first on robust CVaR, then on worst mean loss, so it wins the lexicographic objective; no targeted action is needed.
