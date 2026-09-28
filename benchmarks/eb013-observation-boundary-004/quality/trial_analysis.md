# EB013-004 Trial Analysis

Trial `observation-boundary-gpt56sol-001`: `RAW_PASS`.

The model passed the frozen contract and scientific checks. This task did not defeat the target in this trial.

18 contract/negative/baseline controls and eight input variants passed before the model trial. The task and verifier were frozen before execution. Raw verdict, artifact hashes and unchanged frozen replay are retained.

Two local process trials (`gpt56sol-v1-001` and `observation-boundary-gpt56sol-001`) produced the same scientific winner and identical structured artifact hashes; both are `RAW_PASS`. This is evidence that the contract is executable, not evidence that the task defeats the target model. The next revision must add one new primary difficulty axis rather than more output fields or schema burden.
