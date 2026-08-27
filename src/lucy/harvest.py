"""Classify outbound browser requests as ad/broker harvest.

Sees destinations Lucy's Chromium phoned. Does not decrypt bodies, cookies,
or server-side stitching. Query strings are never stored.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from urllib.parse import urlparse

DEFAULT_TRACKERS = Path(__file__).resolve().parents[2] / "data" / "trackers.json"

MULTI_PART_TLDS = frozenset(
    {
        "co.uk",
        "org.uk",
        "ac.uk",
        "gov.uk",
        "co.jp",
        "ne.jp",
        "com.au",
        "net.au",
        "co.nz",
        "com.br",
    }
)


def registrable(host: str) -> str:
    """Cheap eTLD+1. No I/O. Not a full PSL."""
    host = host.lower().rstrip(".")
    if host.startswith("www."):
        host = host[4:]
    parts = host.split(".")
    if len(parts) < 2:
        return host
    last_two = ".".join(parts[-2:])
    if last_two in MULTI_PART_TLDS and len(parts) >= 3:
        return ".".join(parts[-3:])
    return last_two


def _suffix_hit(host: str, suffix: str) -> bool:
    host = host.lower().rstrip(".")
    suffix = suffix.lower().rstrip(".")
    return host == suffix or host.endswith("." + suffix)


@lru_cache(maxsize=4)
def load_catalog(path: str | None = None) -> dict:
    """Read tracker suffixes. Side effect: disk."""
    target = Path(path) if path else DEFAULT_TRACKERS
    return json.loads(target.read_text(encoding="utf-8"))


def classify_host(host: str, page_host: str, catalog: dict) -> dict | None:
    """Return a harvest hit if this host is a known tracker and not the page. No I/O."""
    host = (host or "").lower().rstrip(".")
    page = (page_host or "").lower().rstrip(".")
    if not host:
        return None
    if any(_suffix_hit(host, sfx) for sfx in catalog.get("ignore_suffixes", [])):
        return None
    if page and registrable(host) == registrable(page):
        return None
    for row in catalog.get("trackers", []):
        suffix = str(row.get("suffix") or "")
        if suffix and _suffix_hit(host, suffix):
            return {
                "host": host,
                "vendor": str(row.get("vendor") or "unknown"),
                "kind": str(row.get("kind") or "ad"),
            }
    return None


class HarvestWatch:
    """Accumulate tracker destinations for one page load. No network of its own."""

    def __init__(self, page_url: str, catalog: dict | None = None) -> None:
        parsed = urlparse(page_url)
        self.page_host = (parsed.hostname or "").lower()
        self.catalog = catalog if catalog is not None else load_catalog()
        self._hits: dict[str, dict] = {}
        self.beacons = 0

    def see(self, url: str, resource_type: str = "") -> None:
        """Note one browser request. Drops query strings."""
        host = (urlparse(url).hostname or "").lower()
        rtype = (resource_type or "").lower()
        if rtype in {"ping", "beacon"}:
            self.beacons += 1
        hit = classify_host(host, self.page_host, self.catalog)
        if hit is None:
            return
        existing = self._hits.get(hit["host"])
        if existing:
            existing["count"] += 1
            return
        self._hits[hit["host"]] = {
            "host": hit["host"],
            "vendor": hit["vendor"],
            "kind": hit["kind"],
            "count": 1,
        }

    def extra(self, limit: int = 16) -> dict:
        rows = sorted(self._hits.values(), key=lambda row: (-row["count"], row["host"]))[:limit]
        return {
            "harvest_hits": sum(row["count"] for row in self._hits.values()),
            "harvest": rows,
            "beacons": self.beacons,
        }
