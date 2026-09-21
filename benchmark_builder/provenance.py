from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from urllib.parse import urlparse
from typing import Any


def registry_digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _url(value: Any) -> bool:
    if not isinstance(value, str) or not value.strip():
        return False
    p = urlparse(value.strip())
    return (p.scheme in {"http", "https", "ftp"} and bool(p.netloc)) or bool(re.fullmatch(r"(?:https?://doi\.org/)?10\.\d{4,9}/\S+", value.strip(), re.I))


def validate_registry(path: str | Path) -> dict[str, Any]:
    path = Path(path)
    errors: list[str] = []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return {"status": "FAIL", "errors": [f"invalid_json:{type(exc).__name__}"]}
    if not isinstance(payload, dict):
        return {"status": "FAIL", "errors": ["registry_root_must_be_object"]}
    if payload.get("schema_version") != "public_data_literature_registry.v1":
        errors.append("invalid_schema_version")
    policy = payload.get("policy")
    required_policy = (
        "scientific_data_must_be_public_or_derived_from_public",
        "synthetic_fixture_allowed_only_for_engineering_tests",
        "untracked_stitching_forbidden",
        "formula_and_method_citation_required",
    )
    if not isinstance(policy, dict):
        errors.append("missing_policy")
    else:
        for key in required_policy:
            if policy.get(key) is not True:
                errors.append(f"policy_not_enabled:{key}")
    for name, identifier, required in (("sources", "source_id", ("accession", "project_url", "download_url", "citation_urls")), ("claims", "claim_id", ("claim_text", "citation_urls")), ("formula_methods", "formula_id", ("expression", "citation_urls"))):
        items = payload.get(name)
        if not isinstance(items, list) or not items:
            errors.append(f"empty_{name}")
            continue
        seen: set[str] = set()
        for i, item in enumerate(items):
            prefix = f"{name}[{i}]"
            if not isinstance(item, dict):
                errors.append(f"{prefix}:not_object"); continue
            value = item.get(identifier)
            if not isinstance(value, str) or not value.strip() or value in seen:
                errors.append(f"{prefix}:invalid_or_duplicate_{identifier}")
            seen.add(value if isinstance(value, str) else "")
            for field in required:
                if field not in item or item[field] in (None, "", []):
                    errors.append(f"{prefix}:missing_{field}")
            if "citation_urls" in item and (not isinstance(item["citation_urls"], list) or not item["citation_urls"] or not all(_url(v) for v in item["citation_urls"])):
                errors.append(f"{prefix}:invalid_citation_urls")
            if name == "sources" and not _url(item.get("project_url")):
                errors.append(f"{prefix}:invalid_project_url")
            if name == "sources" and not _url(item.get("download_url")):
                errors.append(f"{prefix}:invalid_download_url")
    return {"status": "PASS" if not errors else "FAIL", "source_count": len(payload.get("sources", [])), "claim_count": len(payload.get("claims", [])), "formula_count": len(payload.get("formula_methods", [])), "registry_sha256": registry_digest(path), "errors": errors}
