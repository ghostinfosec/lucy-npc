"""Status HTTP and bind rules. Loopback only. No live network."""

from __future__ import annotations

import json
from http.client import HTTPConnection
from http.server import ThreadingHTTPServer
from pathlib import Path
from threading import Thread

import pytest

from lucy.daemon import _handler_factory, require_status_bind
from lucy.store import EventLog


def test_lan_bind_without_token_fails() -> None:
    with pytest.raises(SystemExit, match="LUCY_STATUS_TOKEN"):
        require_status_bind("0.0.0.0", "")


def test_loopback_without_token_ok() -> None:
    require_status_bind("127.0.0.1", "")


def test_status_get_and_post_rejected(tmp_path: Path) -> None:
    log = EventLog(tmp_path)
    server = ThreadingHTTPServer(("127.0.0.1", 0), _handler_factory(log, "secret"))
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address[:2]
    try:
        denied = HTTPConnection(host, port, timeout=2)
        denied.request("GET", "/status")
        assert denied.getresponse().status == 401
        denied.close()

        ok = HTTPConnection(host, port, timeout=2)
        ok.request("GET", "/status", headers={"Authorization": "Bearer secret"})
        response = ok.getresponse()
        assert response.status == 200
        assert response.getheader("X-Content-Type-Options") == "nosniff"
        payload = json.loads(response.read().decode("utf-8"))
        assert "engine" in payload
        ok.close()

        post = HTTPConnection(host, port, timeout=2)
        post.request("POST", "/status", headers={"Authorization": "Bearer secret"})
        assert post.getresponse().status == 405
        post.close()
    finally:
        server.shutdown()
