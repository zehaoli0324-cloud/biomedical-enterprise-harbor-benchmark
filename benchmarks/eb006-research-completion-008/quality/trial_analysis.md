# EB006-008 Trial Analysis

## Result

The repaired bounded-replay task was run with `gpt-5.6-sol` using a 1200-second
shared completion budget and a 1260-second outer runner timeout. Two earlier
launches were infrastructure failures and are excluded from difficulty claims:
one used a relative adapter path and one could not initialize the Codex
app-server under restricted process permissions.

The authorized run `gpt56sol-gated-v1-005` completed one submission in 501.638604
seconds. The public completion gate accepted all four artifacts after two
identical clean replays and one reversed-row replay. The independent verifier
also passed, including its altered-measurement replay.

## Scientific Result

| Decision | Model | Oracle |
| --- | --- | --- |
| Nominal donor-balanced | `C43` | `C43` |
| Observation-row pooled diagnostic | `C28` | `C28` |
| Leave-one-donor-out robust | `C17` | `C17` |

The model delivered 24 unit effects, 30 base/omission checks, six pooled
diagnostics and three candidate summaries with the four registered reason codes.
It preserved the analytical-triage claim boundary and human-review requirement.

## Difficulty Conclusion

This is valid evidence that the completion gate and reconciliation contract are
operational and that the target model can solve this instance. It is not evidence
that the model was defeated. The reusable difficulty modules are
`judgment_influence_reconciliation`, `noise_pooled_stratified_adversary` and
`bounded_replay_delivery`. Human review, isolated container replay and a held-out
model remain NOT_RUN.
