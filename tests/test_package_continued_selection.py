import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("continued_package", ROOT / "scripts/package_continued_selection.py")
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def test_selected_bundle_manifest_is_fail_closed():
    files = MODULE.build_files()
    manifest = json.loads(files["manifest.json"])
    assert manifest["tasks"] == [
        "eb015-real-source-replacement-gate-001",
        "eb014-sequential-evidence-feedback-002",
        "eb006-research-completion-011",
    ]
    assert manifest["release_status"] == "BLOCKED"
    assert "real-data replacement" in manifest["release_blockers"]
    assert all(item["sha256"] and item["size"] >= 0 for item in manifest["files"].values())
