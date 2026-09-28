# Queue-8 Replay Checkpoint

Date: 2026-09-24

The eight immediate replay candidates have passed local verifier tests and SOP preflight. Their current data fingerprints are recorded below for the fixed-container run.

| Task | Data fingerprint | Local gate |
| --- | --- | --- |
| `eb013-cross-context-evidence-portfolio-005` | `1e26664697a2ebb47d8b128b931176579b07a55d4a76c2bd8105cf7275c1a609` | 17 passed; SOP PASS |
| `eb014-sequential-evidence-feedback-002` | `f7f16e333bd7cd9e7a01de46dc7ff5f93ace82a2d0fb620abbc2793f6c73090d` | 3 passed, 1 skipped; SOP PASS |
| `eb010-adaptive-policy-regret-005` | `c93abe4c1179db4cf165cf90493920ddc39f2efa724fc45ab9ab670fb8cbaf50` | 5 passed; SOP PASS |
| `eb010-closed-loop-replay-003` | `9e6377232b8d5609caf7b524f87bbb70048cc4c018b142e8737ce124d14b6035` | 2 passed; SOP PASS |
| `eb013-partial-observation-risk-004` | `18fef18596d864fcc6d9d60faf3e1215b00fb58fd3eb9b513e7a1c9f7f3d6642` | 24 passed; SOP PASS |
| `eb013-shared-setup-routing-003` | `812b116111ab11070b65271ab86e681ca19f9f5f4d0916557f694f2ec59e8c1f` | 18 passed; SOP PASS |
| `eb006-donor-stratified-signal-005` | `6c16d06ff2aaddc8fd7c980129229d33d07c3440f9805d80afc6dd69b896f27a` | 3 passed; SOP PASS |
| `eb006-research-completion-008` | `d4c04c00c671e2940ae1af799b62cd2484d3fdceb8a13cce66114e86845c5d1d` | 3 passed; SOP PASS |

## Infrastructure blocker

The local Docker client is installed, but the Docker API is unavailable (`permission denied` on the Colima socket). Therefore fixed-container replay is not claimed complete in this environment. The queued work is ready to run as soon as the Harbor/Docker runner window is available.

No release status was changed.
