# Audit

## Current evidence

Only `P-EFFECT` is supported. `O-1` is current, in the registered primary-cohort scope, and has effect 0.50, exceeding the 0.20 threshold. `P-REPRO` is unknown: `O-3` is archived, while `O-2` and `O-4` are both in independence group `G-B1`, so they provide one eligible independent positive group rather than the quorum of two. The archived bridge observation, wrong-population bridge observation, and future intervention observation are retained in the ledger but excluded with their specific reasons. Primary-cohort evidence therefore does not authorize either target-population claim.

## Policy and stopping

The minimax policy starts with `A-REPLICATE` (cost 2). A consistent result creates a second independent positive reproduction group and permits `A-BRIDGE` (cost 2); either bridge outcome resolves the transport claim. An inconsistent replication refutes `P-REPRO`, which refutes the weighted association and transport claims under the registry rule, so the path stops and holds. The policy's worst terminal resolved weight is 5, its worst cost is 4, and it uses at most two actions. Holding is always available and is used after terminal outcomes; the causal action is never selected because its bridge and reproduction dependencies must be supported at the moment of selection.

## Rejected shortcuts and boundaries

`A-CHEAP-DUP` was rejected because its independence group is the existing `G-B1`; a positive result cannot satisfy the reproduction quorum. Archived, future, or other-population sources cannot be promoted by source count, and the hypothetical `feedback.json` catalogue is not current evidence. A refuted premise is recorded as a refutation of dependent registered claims only; it is not an assertion of the opposite biology or causality. The causal claim remains unresolved on positive paths because no intervention action is run.

This is a deterministic synthetic replay, not experimental proof. Human review is required before any real study or claim communication, including checking source identity and independence, measurement validity, estimands, causal design, population transport assumptions, ethics, feasibility, and whether the registry and thresholds remain appropriate. The automated artifacts do not replace that scientific and governance review.
