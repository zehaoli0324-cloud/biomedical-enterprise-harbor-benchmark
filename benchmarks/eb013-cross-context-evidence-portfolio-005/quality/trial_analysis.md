# Trial analysis

## cross-context-gpt56sol-001

The model selected `F1,F4` under the 2.4 budget, classified all three contexts as
`SUPPORTED`, preserved the C2 conflict before follow-up, and produced the expected
portfolio and context tables. The frozen verifier returned only:

`provenance: wrong or missing hash`

The four SHA-256 values were correct, but the model placed them at the top level of
`provenance.json` instead of nesting them under `input_sha256`. This is a contract
format failure (`RAW_FAIL_CONTRACT`), not a scientific decision failure. The raw
artifacts are preserved under `quality/trials/cross-context-gpt56sol-001/`.

The task was versioned to 1.0.1 and the instruction now includes a literal JSON
shape for the nested checksum object. A new trial is required before release.

## cross-context-gpt56sol-002

The revised trial replay status is `PASS`.
