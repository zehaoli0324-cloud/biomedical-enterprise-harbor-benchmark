# Real-source replacement release gate audit

Decision date: 2026-09-22. This is a source audit only, not a scientific claim (`source_audit_only_not_scientific_claim`). All nine required freeze fields were checked for each registered source. No source is selected for release.

## Decisions

- `SRC-CRISPR-PMC7006212` is `BLOCKED_RIGHTS`. Its rights status is not an allowed status, its file-level SHA-256 is `PENDING_DOWNLOAD`, and verifier rebinding is required. Its published-screen claim boundary is `published_screen_rows_do_not_prove_single_gene_causality`.
- `SRC-BBBC021-V1` is `BLOCKED_RIGHTS`. Its rights status is not an allowed status, its file-level SHA-256 is `PENDING_DOWNLOAD`, and verifier rebinding is required. Its metadata/MoA claim boundary is `metadata_and_moa_labels_do_not_validate_image_measurements`.
- `SRC-ZENODO-10362368` is `BLOCKED_RIGHTS`. Its rights status is not an allowed status, its file-level value is `MD5_ONLY:...` rather than a release SHA-256, and verifier rebinding is required. Its trajectory claim boundary is `trajectory_convergence_audit_does_not_establish_force_field_validity`.

The first blocker is rights review for every source, so the hash and verifier blockers remain recorded but do not change the release status. `selected_sources` is therefore empty and all three source IDs remain in `blocked_sources` in source-file order.

Source pages are research entrances rather than a blanket redistribution license. Published rows, metadata, and trajectory records remain bounded by their source-specific claim boundaries. This audit does not prove a gene, an image measurement, or a force field. No real-data result is released until the source hash, rights decision, and verifier snapshot agree.

## Next actions

The next actions are a release plan, not completed downloads or experiments:

1. `request_rights_and_freeze_crispr_workbook`
2. `request_bbbc_terms_and_freeze_metadata_hash`
3. `download_zenodo_subset_and_record_sha256`
4. `rebind_verifiers_from_same_snapshot`
