"""Real TLS, no JavaScript. For Pi Zero or as a Playwright fallback.

Side effects: outbound HTTP GET to the beat URL.
"""

from __future__ import annotations

import logging

from lucy.allowlist import AllowlistError, assert_public_url, load_allowlist
from lucy.models import Action, Event, Persona, PlannedBeat
from lucy.persona import DEFAULT_ALLOWLIST
from lucy.store import event_from_beat

log = logging.getLogger("lucy.live_http")


class LiveHttpEngine:
    name = "live_http"

    def __init__(self, timeout_s: float = 20.0) -> None:
        self.timeout_s = timeout_s

    def run(self, persona: Persona, beat: PlannedBeat) -> Event:
        if beat.action in {Action.SLEEP, Action.IDLE, Action.WAKE} or not beat.url:
            return event_from_beat(
                self.name,
                beat.action,
                beat.surface_id,
                beat.url,
                True,
                dwell_s=beat.dwell_s,
                extra={"note": beat.note},
            )
        try:
            spec = load_allowlist(DEFAULT_ALLOWLIST)
            assert_public_url(beat.url, spec)
            import httpx
        except AllowlistError as exc:
            return event_from_beat(
                self.name,
                beat.action,
                beat.surface_id,
                beat.url,
                False,
                error=str(exc),
                dwell_s=beat.dwell_s,
            )
        except ImportError as exc:
            raise RuntimeError("live_http requires httpx. pip install -e '.[live]'") from exc

        headers = {
            "User-Agent": persona.user_agent,
            "Accept-Language": persona.locale,
            "Accept": "text/html,application/xhtml+xml;q=0.9,*/*;q=0.8",
        }
        with httpx.Client(
            headers=headers,
            follow_redirects=True,
            timeout=self.timeout_s,
        ) as client:
            response = client.get(beat.url)
        try:
            assert_public_url(str(response.url), spec)
        except AllowlistError as exc:
            return event_from_beat(
                self.name,
                beat.action,
                beat.surface_id,
                beat.url,
                False,
                error=f"redirect left allowlist: {exc}",
                status=response.status_code,
            )
        title = _guess_title(response.text) if "text" in response.headers.get("content-type", "") else None
        log.info("GET %s -> %s", beat.url, response.status_code)
        return event_from_beat(
            self.name,
            beat.action,
            beat.surface_id,
            str(response.url),
            response.is_success,
            status=response.status_code,
            bytes=len(response.content),
            title=title,
            dwell_s=beat.dwell_s,
            extra={"note": beat.note},
        )


def _guess_title(html: str) -> str | None:
    lower = html.lower()
    start = lower.find("<title>")
    end = lower.find("</title>")
    if start == -1 or end == -1 or end <= start:
        return None
    raw = html[start + 7 : end].strip()
    return " ".join(raw.split())[:180] or None
