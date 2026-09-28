# EB006-007 Gated Trial Analysis

Trial `gpt56sol-gated-v1-002` used `gpt-5.6-sol` after the public
`reason_codes` contract repair.

The model correctly reconstructed the intended three-way result and found a real
implementation issue during its own work: omission scenarios used inconsistent
labels. It corrected the analysis logic and re-ran the numerical checks. The
expected scientific tuple remained nominal `C43`, pooled `C28`, robust `C17`.

The run nevertheless timed out after the 840-second shared adapter budget. The
agent event log then showed repeated network reconnection errors. The final
completion gate could not accept the submission because `analysis.py` was in the
workspace root rather than the required `outputs/` directory; no scientific
verdict can be inferred from that delivery failure. This is classified as
`TIMEOUT_DELIVERY_FAIL`, not `SCIENTIFIC_FAIL` and not target-model defeat.

This follow-up exposes two operational requirements for future gated trials:

1. The runner must validate output paths before launching a long replay and report
   missing output paths directly; model-created root files are not silently moved.
2. Network reconnect/error events must be surfaced as infrastructure state and
   should not consume the entire research budget without a clear terminal record.

The first trial's contract failure and this versioned replay remain separate. No
trial has yet produced valid evidence that this task defeats the target model.
Container isolation, held-out models and human scientific review remain NOT_RUN.
