# EB006-009 Trial Analysis

## Result

`gpt56sol-cross-assay-v1-001` ran for 1101.24 seconds. The model produced all
four required artifacts, and the public completion gate accepted them after clean
replays. The final verifier rejected the submission.

## What the model did

The model independently implemented donor-balanced, pooled, leave-one-donor-out
and assay-specific calculations. It reached the intended scientific hold:
nominal `C43`, pooled `C28`, robust `C17`, but no selected candidate because
cross-assay evidence was not sufficient.

## Why this is not valid defeat evidence

The verifier expected assay `effect_range` to mean the absolute difference between
assay A and assay B means, while the public contract did not define that field
explicitly. The provenance rule said “all inputs” but did not enumerate the new
`assay_observations.csv`; the model therefore omitted that hash. Finally, the
contract described prior reasons without publishing a closed reason-code set, so
the model used semantic synonyms. These are contract/representation defects, not
an unambiguous scientific error.

Classification: `RAW_FAIL_CONTRACT_AMBIGUITY`. The next version must publish the
exact effect-range formula, enumerate every input file in provenance, and close
the reason-code vocabulary, then replay unchanged scientific intent before any
further difficulty escalation.
