# Queue-14 Individual Packaging

Fourteen unique task packages were built under `dist/queue14-20260924/`. Each task has its own `.tar.gz` archive and `.sha256` sidecar.

The archives exclude trial history, `quality/trials/`, `quality/container_replays/`, caches, bytecode, and generated `outputs/`. All 14 sidecars verify, and a second scan found no excluded paths.

The newly repaired `eb013-evidence-budget-routing-002` is included. No trial was rerun during packaging.

The directory is the handoff set for the next Harbor/trial window.
