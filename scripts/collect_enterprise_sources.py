#!/usr/bin/env python3
"""Fetch small official source pages into an auditable, dependency-free harvest."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import html
import json
import re
import urllib.error
import urllib.request
from pathlib import Path


COLLECTOR_VERSION = "0.1.0"


def _text_from_html(body: bytes) -> tuple[str | None, list[str], str]:
    decoded = body.decode("utf-8", errors="replace")
    title_match = re.search(r"<title[^>]*>(.*?)</title>", decoded, flags=re.I | re.S)
    title = re.sub(r"\s+", " ", html.unescape(title_match.group(1))).strip() if title_match else None
    headings = []
    for match in re.finditer(r"<h[1-3][^>]*>(.*?)</h[1-3]>", decoded, flags=re.I | re.S):
        value = re.sub(r"<[^>]+>", " ", match.group(1))
        value = re.sub(r"\s+", " ", html.unescape(value)).strip()
        if value:
            headings.append(value[:240])
    cleaned = re.sub(r"<script[^>]*>.*?</script>|<style[^>]*>.*?</style>", " ", decoded, flags=re.I | re.S)
    cleaned = re.sub(r"<[^>]+>", " ", cleaned)
    text = re.sub(r"\s+", " ", html.unescape(cleaned)).strip()
    return title, headings[:40], text[:8000]


def fetch(seed: dict, timeout: float, max_bytes: int) -> dict:
    now = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()
    request = urllib.request.Request(seed["url"], headers={"User-Agent": "biomedical-enterprise-harbor-benchmark/0.1 source-harvester"})
    result = {"source_id": seed["source_id"], "url": seed["url"], "retrieved_at": now, "seed": seed}
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = response.read(max_bytes + 1)
            result["http_status"] = getattr(response, "status", None)
            result["content_type"] = response.headers.get("Content-Type")
            result["truncated"] = len(body) > max_bytes
            body = body[:max_bytes]
        result["content_sha256"] = hashlib.sha256(body).hexdigest()
        result["bytes"] = len(body)
        content_type = result.get("content_type") or ""
        if "html" in content_type or seed["url"].endswith(("/", ".html", ".htm")):
            title, headings, text = _text_from_html(body)
        else:
            decoded = body.decode("utf-8", errors="replace")
            title = None
            headings = []
            text = decoded[:8000]
        result.update({"extraction_status": "ok", "title": title, "headings": headings, "text_excerpt": text})
    except (OSError, urllib.error.URLError, TimeoutError) as exc:
        result.update({"extraction_status": "error", "error": str(exc)})
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", type=Path, default=Path("knowledge_base/seeds/official_sources.json"))
    parser.add_argument("--out", type=Path, default=Path("knowledge_base/harvest"))
    parser.add_argument("--timeout", type=float, default=20.0)
    parser.add_argument("--max-bytes", type=int, default=2_000_000)
    args = parser.parse_args()
    seeds = json.loads(args.seeds.read_text(encoding="utf-8"))
    if not isinstance(seeds, list):
        raise SystemExit("seed file must contain a JSON array")
    raw_dir = args.out / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    manifest = args.out / "manifest.jsonl"
    seed_sha256 = hashlib.sha256(args.seeds.read_bytes()).hexdigest()
    with manifest.open("a", encoding="utf-8") as handle:
        for seed in seeds:
            result = fetch(seed, args.timeout, args.max_bytes)
            (raw_dir / f"{seed['source_id']}.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            manifest_row = {key: result.get(key) for key in ("source_id", "url", "retrieved_at", "http_status", "bytes", "content_sha256", "extraction_status", "error")}
            manifest_row.update({"collector_version": COLLECTOR_VERSION, "seed_sha256": seed_sha256})
            handle.write(json.dumps(manifest_row, ensure_ascii=False) + "\n")
            print(f"{seed['source_id']}: {result['extraction_status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
