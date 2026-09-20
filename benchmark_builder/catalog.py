from __future__ import annotations

import json
from pathlib import Path
from typing import Any


DEFAULT_CATALOG = Path(__file__).resolve().parents[1] / "config" / "module_catalog.json"


def load_catalog(path: str | Path | None = None) -> dict[str, Any]:
    catalog_path = Path(path) if path else DEFAULT_CATALOG
    with catalog_path.open(encoding="utf-8") as handle:
        return json.load(handle)


def index_modules(catalog: dict[str, Any]) -> dict[str, dict[str, Any]]:
    indexed: dict[str, dict[str, Any]] = {}
    for module in catalog.get("modules", []):
        module_id = module.get("id")
        if not module_id or module_id in indexed:
            raise ValueError(f"Module ids must be unique and non-empty: {module_id!r}")
        indexed[module_id] = module
    return indexed

