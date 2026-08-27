"""Local admin UI: cookie login, metrics, no C2."""

from __future__ import annotations

import json
from http.client import HTTPConnection
from http.server import ThreadingHTTPServer
from pathlib import Path
from threading import Thread

from lucy.daemon import _handler_factory
from lucy.store import EventLog
from lucy.webui import COOKIE, session_value


def _start(tmp_path: Path, token: str = "secret") -> tuple[ThreadingHTTPServer, str, int]:
    log = EventLog(tmp_path)
    log.path.write_text(
        json.dumps(
            {
                "ts": "2026-08-26T11:07:12Z",
                "action": "open",
                "url": "https://weather.com/",
                "ok": True,
                "bytes": 44000,
                "extra": {"http_requests": 12, "http_bytes": 44000},
            }
        )
        + "\n",
        encoding="utf-8",
    )
    fp = {"presents_as": "mobile Chrome", "engine": "local"}
    server = ThreadingHTTPServer(("127.0.0.1", 0), _handler_factory(log, token, fp))
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address[:2]
    return server, host, port


def test_root_is_public_login(tmp_path: Path) -> None:
    server, host, port = _start(tmp_path)
    try:
        conn = HTTPConnection(host, port, timeout=2)
        conn.request("GET", "/")
        response = conn.getresponse()
        assert response.status == 200
        body = response.read().decode("utf-8")
        assert "Lucy" in body
        assert "/static/hatch.js" in body
        assert "All looks" in body
        assert response.getheader("X-Frame-Options") == "DENY"
        conn.close()

        js = HTTPConnection(host, port, timeout=2)
        js.request("GET", "/static/hatch.js")
        script = js.getresponse()
        assert script.status == 200
        js.close()
    finally:
        server.shutdown()


def test_metrics_need_auth_then_cookie(tmp_path: Path) -> None:
    server, host, port = _start(tmp_path)
    try:
        denied = HTTPConnection(host, port, timeout=2)
        denied.request("GET", "/api/metrics")
        assert denied.getresponse().status == 401
        denied.close()

        login = HTTPConnection(host, port, timeout=2)
        login.request(
            "POST",
            "/login",
            body="token=secret",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        got = login.getresponse()
        assert got.status == 200
        cookie = got.getheader("Set-Cookie") or ""
        assert COOKIE in cookie
        login.close()

        ok = HTTPConnection(host, port, timeout=2)
        ok.request("GET", "/api/metrics", headers={"Cookie": f"{COOKIE}={session_value('secret')}"})
        response = ok.getresponse()
        assert response.status == 200
        payload = json.loads(response.read().decode("utf-8"))
        assert payload["beats"] == 1
        assert payload["http_requests"] == 12
        assert "12 fetches" in payload["unit"]
        assert payload["live_capture"] is True
        ok.close()

        wake = HTTPConnection(host, port, timeout=2)
        wake.request("POST", "/api/control", headers={"Cookie": f"{COOKIE}={session_value('secret')}"})
        assert wake.getresponse().status == 405
        wake.close()
    finally:
        server.shutdown()
