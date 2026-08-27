"""The hatch. Cookie auth. GET data, login/logout only writes."""

from __future__ import annotations

import hashlib
import hmac
from http.cookies import SimpleCookie
from pathlib import Path
from urllib.parse import parse_qs

COOKIE = "lucy_session"
STATIC = Path(__file__).resolve().parent / "static"


def session_value(token: str) -> str:
    """HMAC of the status token. No I/O."""
    return hmac.new(token.encode("utf-8"), b"lucy-webui-v1", hashlib.sha256).hexdigest()


def authorized(headers: dict[str, str], token: str) -> bool:
    """Bearer or session cookie. Empty token = loopback trust. No I/O."""
    if not token:
        return True
    sent = headers.get("Authorization") or headers.get("authorization") or ""
    if sent == f"Bearer {token}":
        return True
    raw = headers.get("Cookie") or headers.get("cookie") or ""
    jar = SimpleCookie()
    try:
        jar.load(raw)
    except Exception:  # noqa: BLE001 — malformed cookie is unauthenticated
        return False
    morsel = jar.get(COOKIE)
    if morsel is None:
        return False
    return hmac.compare_digest(morsel.value, session_value(token))


def login_token(body: bytes) -> str:
    """Parse application/x-www-form-urlencoded or JSON-ish token=. No I/O."""
    parsed = parse_qs(body.decode("utf-8", errors="replace"), keep_blank_values=False)
    for key in ("token", "password", "LUCY_STATUS_TOKEN"):
        values = parsed.get(key)
        if values:
            return values[0]
    return ""


def cookie_header(token: str, *, clear: bool = False) -> str:
    if clear or not token:
        return f"{COOKIE}=; Path=/; HttpOnly; SameSite=Strict; Max-Age=0"
    return (
        f"{COOKIE}={session_value(token)}; Path=/; HttpOnly; SameSite=Strict; Max-Age=86400"
    )


def static_file(name: str) -> tuple[bytes, str]:
    """Read a bundled UI file. Side effect: disk read."""
    path = (STATIC / name).resolve()
    if path.parent != STATIC or not path.is_file():
        raise FileNotFoundError(name)
    data = path.read_bytes()
    types = {
        ".html": "text/html; charset=utf-8",
        ".css": "text/css; charset=utf-8",
        ".js": "text/javascript; charset=utf-8",
        ".svg": "image/svg+xml",
    }
    return data, types.get(path.suffix, "application/octet-stream")
