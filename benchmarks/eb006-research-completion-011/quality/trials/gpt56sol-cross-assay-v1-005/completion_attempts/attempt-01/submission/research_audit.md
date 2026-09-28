# Research audit

The registered paired estimand averages each donor's treatment-minus-control effect with equal donor weight; technical replicates are averaged within donor. The pooled diagnostic instead averages all eligible rows and therefore weights donors by replicate count. Independent assay A/B effects are donor-balanced separately and are not treated as additional donors.

Coverage: all 24 registered unit effects, 30 base/leave-one-donor-out checks, six pooled states, and six assay concordance states were recomputed from PASS, non-empty observations. Missing paired evidence is retained as missing rather than imputed.

Nominal selection was C43; pooled selection was C28. The robust paired candidate was C17 after all omission scenarios. The pooled and nominal rankings therefore differ, and the nominal winner fails robustness under at least one omission scenario.

Technical-replicate composition changes the pooled estimand because some donor/state pairs contribute more rows than others; donor D1 is especially influential for C28. C43 late has missing D4 treatment evidence, so that donor/state remains incomplete in paired sensitivity checks.

Assay states supported: C17|early, C43|early, C43|late. Contradictory assay states: C17|late, C28|early, C28|late. Because at least one registered assay state is contradictory, assay concordance does not permit selection of the otherwise robust candidate.

Conclusion boundary: this is analytical triage only, not a mechanism or efficacy claim. Human review is required before any follow-up.
