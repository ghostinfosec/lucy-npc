"""Surface allowlist. The live browser is a confused deputy by design.

Side effect of load_allowlist: reads JSON from disk.
Network fetch must call assert_public_url first.
"""

from __future__ import annotations

import ipaddress
import json
from functools import lru_cache
from pathlib import Path
from urllib.parse import urlparse


class AllowlistError(ValueError):
    pass


@lru_cache(maxsize=4)
def load_allowlist(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _host_blocked(host: str, spec: dict) -> bool:
    host = host.lower().rstrip(".")
    if host in spec.get("block_literals", []):
        return True
    try:
        ip = ipaddress.ip_address(host)
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_multicast:
            return True
    except ValueError:
        pass
    return False


def assert_public_url(url: str, spec: dict) -> None:
    """Raise AllowlistError if Lucy must not fetch this URL."""
    parsed = urlparse(url)
    if spec.get("https_only", True) and parsed.scheme != "https":
        raise AllowlistError(f"refusing non-https url: {url}")
    host = (parsed.hostname or "").lower()
    if not host:
        raise AllowlistError("url has no host")
    if _host_blocked(host, spec):
        raise AllowlistError(f"refusing blocked host: {host}")
    allowed = {h.lower() for h in spec.get("hosts", [])}
    if host not in allowed:
        raise AllowlistError(f"host not on allowlist: {host}")
