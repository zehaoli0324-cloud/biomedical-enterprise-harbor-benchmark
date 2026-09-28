# Adaptive multi-round task design v1

## Goal

Make repeated model interactions scientifically necessary without rewarding
empty retries or imposing a round count as a scoring proxy. A complete first
submission must be impossible because later obligations depend on observations
that do not exist at task start.

## Mechanism

The pilot task uses a staged evidence graph:

1. audit measurement quality and pairing before estimating the primary effect;
2. expose context, replication and negative-control evidence only after the
   primary result has been observed;
3. activate conditional follow-ups from the returned outcomes;
4. require a final robustness synthesis after all activated branches resolve;
5. accept `stop` only when the trusted controller has observed every active
   requirement.

Each accepted response includes a state token derived from a hidden chain seed,
the previous token and the observed outcome. The next request must return that
token. This binds requests to the actual observation sequence and prevents a
prewritten future trajectory from satisfying the protocol.

The frozen pilot scenario activates eleven evidence actions followed by `stop`.
The adapter processes at most one request per model interaction and reserves a
separate finalization turn, so the expected valid path has at least thirteen
model interactions. This path length is a consequence of the evidence graph,
not a `minimum_rounds` scoring rule.

## Completion boundary

The public completion gate receives trusted controller state. Agent-authored
logs alone cannot establish that actions occurred. An early final answer, a
fabricated feedback history or an early `stop` is returned with public missing
requirement IDs. Hidden scientific correctness remains separate and is never
fed back as repair guidance.

## Calibration

Report accepted actions, explicit model turns, completion returns, wall time and
scientific score separately. A short valid path is accepted if another frozen
scenario genuinely resolves earlier. More than 40 turns remains a trajectory
target for larger projects, not a correctness requirement for this pilot.
