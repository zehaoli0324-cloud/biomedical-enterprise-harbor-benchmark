# Agent task

You are a statistical programmer deriving a PFS-like ADTTE parameter for a downstream time-to-event table. The public pharmaverse admiral project is only the workflow reference. All files are synthetic and must not be described as sponsor patient data or as evidence of treatment benefit.

Apply `data/rules.json` literally to `dm.csv`, `events.csv`, and `followup.csv`. Use the subject as the independent unit. Select the earliest exact-date qualifying event under the declared priority, apply the cutoff, censor valid event-free subjects, and route partial dates or absent follow-up to review.

Do not turn month-only dates into invented days, do not count post-cutoff events, and do not silently replace missing follow-up. Write all required artifacts under `outputs/`: `outputs/adtte.csv`, `outputs/event_trace.csv`, `outputs/censoring_audit.json`, and `outputs/run_manifest.json`. Preserve event and censoring evidence in `outputs/event_trace.csv`, record checksums in `outputs/run_manifest.json`, and include a claim boundary stating that the fixture is synthetic, not sponsor data, and not efficacy evidence.

The derivation supports a rule audit and handoff decision only. It does not establish efficacy, safety, an estimand for an actual trial, or regulatory compliance.
