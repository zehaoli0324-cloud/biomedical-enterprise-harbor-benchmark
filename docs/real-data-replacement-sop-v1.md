# Real-data and literature replacement SOP supplement

This supplement operationalizes `Downloads/ten-task-real-data-replacement-plan.md`.
It is a release gate, not evidence that a source has already been downloaded or
that a benchmark has scientific validity.

## Source freeze

For every task, freeze the accession or DOI, project URL, direct download URL,
version or access date, rights statement, file inventory, one SHA-256 per file,
the deterministic transformation steps, and the row/image/frame selection rule.
The source landing page is a provenance pointer, not blanket redistribution
permission. A public paper, metadata table, ground-truth label, image archive or
large trajectory has its own reuse boundary.

The first release-gate task, `eb015-real-source-replacement-gate-001`, makes the
three named sources observable together:

- PMC7006212: use the published MAGeCK workbooks only after workbook-level rights
  and hashes are frozen; published screen rows do not prove single-gene causality.
- BBBC021: metadata, compound and MoA tables are distinct from image pixels; the
  image subset remains blocked until the copyright and selected-file terms are
  reviewed.
- Zenodo 10362368: an archive-level MD5 is not a SHA-256 release manifest; a
  bounded trajectory range and stride must be declared before verifier rebinding.

## Canonical gate

The machine-readable registry is `config/real_data_replacement_registry.json`.
The agent-visible allowlist is `data/release_input_manifest.json` when a task has
one. A source is never `READY_FOR_REVIEW` when rights are unresolved, a SHA-256 is
missing or only an MD5 is available, or the verifier was not rebuilt from the same
snapshot. Missing evidence is a blocker, not an implicit pass.

The canonical blocker order is `rights_review_required`,
`sha256_missing_or_md5_only`, then `verifier_rebind_required`. Keep these states
separate so a later rights decision cannot conceal a stale hash or a moving
verifier. Store raw source metadata, derived snapshots, hidden labels, and trial
artifacts under separate versioned paths; never overwrite a failed or incomplete
trial with a repaired result.

## Scientific boundary

Before packaging, recompute hidden labels and the reference from the frozen public
snapshot, rebuild the verifier, and run independent controls for missing fields,
wrong hash, rights withdrawal, row/image/frame selection, row order and claim
boundary. CRISPR screen associations, BBBC021 metadata/MoA labels, and MD
trajectory convergence audits must not be written as causal, image-measurement, or
force-field proof. The final task state remains `BLOCKED` or `REVIEW_REQUIRED`
until rights, hashes, rebind, fixed-container replay and practitioner review all
pass.

## Transferable difficulty module

Register `provenance_hash_license_rebind` as one primary difficulty module. Its
observable computations are required-field joins, rights classification,
file-level hash checks and verifier-snapshot matching. Its decision flips are:
rights cleared plus a frozen SHA-256 moves a source to `READY_FOR_REVIEW`; an
MD5-only archive, missing rights, or a moving verifier keeps it blocked. Use at
most two secondary modules, `retrieval_public_source_freeze` and
`judgment_claim_boundary_abstention`. Do not count a longer file list, extra
prose, or source-name aliases as new difficulty.

Run contract audit before target-model trial. Record raw delivery, canonical
representation, scientific verifier result, artifact hashes, and unchanged
artifact replay separately. A passing source-audit trial does not upgrade the
underlying real-data replacement task; it only validates the release-gate logic.
