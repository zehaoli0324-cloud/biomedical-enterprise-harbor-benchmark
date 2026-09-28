# Selected Four v3 Optimization And Packaging

Date: 2026-09-24  
Target model: `gpt-5.6-sol`

## Packaged Snapshot

`eb006-research-completion-011` is stored as a deterministic calibrated internal snapshot:

- Archive: `dist/eb006-research-completion-011-calibrated-20260924.tar.gz`
- SHA-256: `87ec1ca8bf8ac5041bceb9529097ec1962e2aed88013716724ae1e2047d295c0`
- Payload: 51 files; trial history, caches, bytecode, and generated outputs are excluded.
- Formal release remains blocked by fixed-container replay, practitioner review, and real-data replacement.

## Current-Version Trials

| Task | Version | Effective result | What was exercised | Target defeated |
|---|---:|---|---|---:|
| `eb013-cross-context-evidence-portfolio-005` | 1.2.0 | Raw pass | Executable planner plus two schema-preserving held-out replays | No |
| `eb014-sequential-evidence-feedback-002` | 2.0.0 | Raw pass | Ten observation-dependent rounds, exact 12-unit budget, explicit stop and bounded claims | No |
| `eb015-real-source-replacement-gate-001` | 2.0.0 | Pass after contract replay | Executable auditor plus two rights/hash/rebind replays | No |

The first EB014 v3 attempt is excluded. The model had submitted the accepted round-10 stop action, but the adapter killed finalization because old final files already existed. The adapter now requires the final-artifact fingerprint to change; the retry passed end to end.

EB015's raw verifier rejected row ordering and per-source URL objects that the public contract explicitly allowed. The original, unchanged submission passes the corrected verifier, including both held-out replays. This is not model-defeat evidence.

## Verification

- Combined tests: `51 passed, 3 skipped`.
- Four-task dynamic check: PASS.
- EB013, EB014, and EB015 enterprise SOP structural preflights: PASS.
- Harbor controls: EB014 and EB015 Oracle reward `1.0`; no-op reward `0.0`.
- EB006 archive digest matches its sidecar.

## Remaining Work

- EB013: fixed-container replay, additional held-out target trials, practitioner review.
- EB014: fixed-container replay, trajectory analysis, practitioner review.
- EB015: source-rights review, file-level SHA-256 freeze, verifier rebind, fixed-container replay, practitioner review.

The optimized tasks are more general and less susceptible to static copying, but the target model still solved them. The next difficulty increase should use multiple hidden scenario families and require one submitted policy to generalize across them. It should not add unsupported subquestions or enlarge the abstention surface.
