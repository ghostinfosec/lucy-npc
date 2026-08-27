"""Unattended loop + hatch HTTP.

Side effects: network (via engine), disk log, bound TCP port, sleep.
POST is login/logout only. No remote orders.
"""

from __future__ import annotations

import argparse
import hmac
import json
import logging
import os
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from lucy.engines.factory import get_engine
from lucy.engines.live_public import LivePublicEngine
from lucy.envfile import load_dotenv
from lucy.fingerprint import describe
from lucy.metrics import summarize
from lucy.models import Action
from lucy.persona import load_persona
from lucy.planner import next_beat
from lucy.store import EventLog
from lucy.webui import authorized, cookie_header, login_token, static_file

LOOPBACK_HOSTS = frozenset({"127.0.0.1", "::1", "localhost"})
WRITE_PATHS = frozenset({"/login", "/logout"})


def require_status_bind(host: str, token: str) -> None:
    """Refuse a public bind without a token. No I/O."""
    if host not in LOOPBACK_HOSTS and not token:
        raise SystemExit("LAN bind requires LUCY_STATUS_TOKEN — Lucy is not a public API")

log = logging.getLogger("lucy")

STATE = {
    "awake": False,
    "engine": "",
    "persona": "",
    "last": None,
}


def _handler_factory(event_log: EventLog, token: str, fingerprint: dict | None = None):
    fp = fingerprint or {}

    class Handler(BaseHTTPRequestHandler):
        def _auth(self) -> bool:
            return authorized(self.headers, token)

        def _lock(self) -> None:
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("X-Frame-Options", "DENY")
            self.send_header("Referrer-Policy", "no-referrer")
            self.send_header(
                "Content-Security-Policy",
                "default-src 'none'; style-src 'self'; script-src 'self'; "
                "connect-src 'self'; img-src 'self'; base-uri 'none'; form-action 'self'",
            )

        def _json(self, code: int, payload: dict, extra_headers: list[tuple[str, str]] | None = None) -> None:
            body = json.dumps(payload).encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self._lock()
            for key, value in extra_headers or []:
                self.send_header(key, value)
            self.end_headers()
            self.wfile.write(body)

        def _bytes(self, code: int, payload: bytes, content_type: str) -> None:
            self.send_response(code)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(payload)))
            self._lock()
            self.end_headers()
            self.wfile.write(payload)

        def _path(self) -> str:
            return urlparse(self.path).path

        def do_POST(self) -> None:  # noqa: N802
            path = self._path()
            if path not in WRITE_PATHS:
                self._json(405, {"error": "lucy does not take orders over http"})
                return
            length = int(self.headers.get("Content-Length") or 0)
            if length > 4096:
                self._json(413, {"error": "too large"})
                return
            body = self.rfile.read(length) if length else b""
            if path == "/logout":
                self._json(200, {"ok": True}, extra_headers=[("Set-Cookie", cookie_header(token, clear=True))])
                return
            if not token:
                self._json(200, {"ok": True})
                return
            offered = login_token(body)
            if not offered or not hmac.compare_digest(offered, token):
                self._json(401, {"error": "unauthorized"})
                return
            self._json(200, {"ok": True}, extra_headers=[("Set-Cookie", cookie_header(token))])

        def do_GET(self) -> None:  # noqa: N802
            path = self._path()
            if path in {"/", "/index.html"}:
                payload, ctype = static_file("index.html")
                self._bytes(200, payload, ctype)
                return
            if path == "/static/app.css":
                payload, ctype = static_file("app.css")
                self._bytes(200, payload, ctype)
                return
            if path == "/static/hatch.js":
                payload, ctype = static_file("hatch.js")
                self._bytes(200, payload, ctype)
                return
            if not self._auth():
                self._json(401, {"error": "unauthorized"})
                return
            if path in {"/status", "/api/status"}:
                self._json(200, {**STATE, "log": str(event_log.path)})
                return
            if path in {"/events", "/api/events"}:
                self._json(200, {"events": event_log.tail(80)})
                return
            if path == "/api/metrics":
                self._json(200, summarize(event_log.read()))
                return
            if path == "/api/fingerprint":
                self._json(200, fp)
                return
            self._json(404, {"error": "not found"})

        def log_message(self, fmt: str, *args: object) -> None:
            log.debug("http " + fmt, *args)

    return Handler


class AdminServer(ThreadingHTTPServer):
    allow_reuse_address = True


def _serve(event_log: EventLog, host: str, port: int, token: str, fingerprint: dict) -> ThreadingHTTPServer:
    try:
        server = AdminServer((host, port), _handler_factory(event_log, token, fingerprint))
    except OSError as exc:
        if getattr(exc, "errno", None) == 98:
            raise SystemExit(
                f"port {port} already in use — another lucy-daemon is probably still running. "
                f"Stop it (`pkill -f lucy-daemon` or `fuser -k {port}/tcp`) or pass --port 8788"
            ) from exc
        raise
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    log.info("admin http://%s:%s/  status /api/status", host, port)
    return server


def run_loop(
    *,
    persona_path: Path,
    engine_name: str,
    log_dir: Path,
    once: bool,
    host: str,
    port: int,
    token: str,
    ui_only: bool = False,
    force_open: bool = False,
) -> None:
    """Main Lucy loop. Blocks until killed unless once=True. ui_only serves the admin."""
    persona = load_persona(persona_path)
    event_log = EventLog(log_dir)
    STATE.update({"awake": not ui_only, "engine": engine_name, "persona": persona.name})
    fingerprint = describe(persona, engine_name)
    server = _serve(event_log, host, port, token, fingerprint)
    if ui_only:
        log.info("ui-only — no beats, log=%s", event_log.path)
        try:
            threading.Event().wait()
        finally:
            STATE["awake"] = False
            server.shutdown()
        return

    engine = get_engine(engine_name)
    if isinstance(engine, LivePublicEngine):
        engine.start(persona)

    try:
        while True:
            beat = next_beat(persona, force="open" if force_open else None)
            event = engine.run(persona, beat)
            event_log.append(event)
            STATE["last"] = {
                "ts": event.ts,
                "action": event.action.value,
                "url": event.url,
                "ok": event.ok,
            }
            if once:
                break
            if beat.action == Action.SLEEP:
                time.sleep(90)
            elif beat.action == Action.IDLE:
                time.sleep(max(beat.dwell_s, 5))
            else:
                time.sleep(max(2.0, min(beat.dwell_s * 0.25, 12)))
    finally:
        STATE["awake"] = False
        closer = getattr(engine, "close", None)
        if callable(closer):
            closer()
        server.shutdown()


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    root = Path(__file__).resolve().parents[2]
    load_dotenv(root)
    parser = argparse.ArgumentParser(description="Lucy hatch daemon")
    parser.add_argument("--engine", default=os.environ.get("LUCY_ENGINE", "live_public"))
    parser.add_argument(
        "--persona",
        default=os.environ.get("LUCY_PERSONA", str(root / "data/personas/wool.json")),
    )
    parser.add_argument("--log-dir", default=os.environ.get("LUCY_LOG_DIR", str(root / "logs")))
    parser.add_argument("--once", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument(
        "--force-open",
        action="store_true",
        help="Look even outside her hours",
    )
    parser.add_argument("--ui-only", action="store_true", help="Serve the hatch, no looks")
    parser.add_argument("--host", default=os.environ.get("LUCY_STATUS_HOST", "127.0.0.1"))
    parser.add_argument("--port", type=int, default=int(os.environ.get("LUCY_STATUS_PORT", "8787")))
    args = parser.parse_args()
    host = args.host
    token = os.environ.get("LUCY_STATUS_TOKEN", "")
    require_status_bind(host, token)
    run_loop(
        persona_path=Path(args.persona),
        engine_name=args.engine,
        log_dir=Path(args.log_dir),
        once=args.once,
        host=host,
        port=args.port,
        token=token,
        ui_only=args.ui_only,
        force_open=args.force_open,
    )


if __name__ == "__main__":
    main()
