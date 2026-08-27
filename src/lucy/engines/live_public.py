"""Playwright Chromium against the live public internet.

This is the default Pi engine. Side effects: launches a browser, hits real URLs,
scrolls, dwells. Phone viewport. Packets leave the machine.
"""

from __future__ import annotations

import logging
import time

from lucy.allowlist import assert_public_url, load_allowlist
from lucy.engines.youtube import follow_search, is_results_url
from lucy.fingerprint import chromium_context_kwargs, chromium_launch_kwargs
from lucy.harvest import HarvestWatch
from lucy.models import Action, Event, Persona, PlannedBeat
from lucy.persona import DEFAULT_ALLOWLIST
from lucy.store import event_from_beat

log = logging.getLogger("lucy.live_public")


class LivePublicEngine:
    name = "live_public"

    def __init__(self, headless: bool = True) -> None:
        self.headless = headless
        self._playwright = None
        self._browser = None
        self._context = None

    def start(self, persona: Persona) -> None:
        """Launch Chromium. Side effect: local browser process."""
        try:
            from playwright.sync_api import sync_playwright
        except ImportError as exc:
            raise RuntimeError(
                "live_public requires Playwright. pip install -e '.[live]' && playwright install chromium"
            ) from exc
        self._playwright = sync_playwright().start()
        self._browser = self._playwright.chromium.launch(**chromium_launch_kwargs(self.headless))
        self._context = self._browser.new_context(**chromium_context_kwargs(persona))
        log.info(
            "chromium up, mobile viewport %sx%s",
            persona.viewport_width,
            persona.viewport_height,
        )

    def close(self) -> None:
        """Tear down browser. Side effect: kills child process."""
        if self._context:
            self._context.close()
        if self._browser:
            self._browser.close()
        if self._playwright:
            self._playwright.stop()
        self._context = self._browser = self._playwright = None

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
        if self._context is None:
            self.start(persona)
        assert self._context is not None
        assert beat.url is not None
        page = self._context.new_page()
        http_requests = 0
        http_bytes = 0
        watch = HarvestWatch(beat.url)

        def _on_request(request: object) -> None:
            nonlocal http_requests
            http_requests += 1
            url = getattr(request, "url", "") or ""
            rtype = getattr(request, "resource_type", "") or ""
            watch.see(url, str(rtype))

        def _on_response(response: object) -> None:
            nonlocal http_bytes
            headers = getattr(response, "headers", {}) or {}
            raw = headers.get("content-length") or headers.get("Content-Length")
            if raw:
                try:
                    http_bytes += int(raw)
                except ValueError:
                    return

        page.on("request", _on_request)
        page.on("response", _on_response)
        try:
            spec = load_allowlist(DEFAULT_ALLOWLIST)
            assert_public_url(beat.url, spec)
            response = page.goto(beat.url, wait_until="domcontentloaded", timeout=25_000)
            if is_results_url(beat.url):
                follow_search(page, spec)
            else:
                assert_public_url(page.url, spec)
            status = response.status if response else None
            if beat.action in {Action.OPEN, Action.SCROLL, Action.DWELL, Action.SKIP}:
                delta = max(persona.scroll_px[0], 240)
                page.mouse.wheel(0, delta)
                time.sleep(min(max(beat.dwell_s, 0.4), 40.0))
                if beat.action == Action.SCROLL:
                    page.mouse.wheel(0, delta * 2)
            title = page.title()
            url = page.url
            harvest = watch.extra()
            log.info(
                "%s %s -> %s reqs=%s harvest=%s",
                beat.action.value,
                beat.url,
                status,
                http_requests,
                harvest["harvest_hits"],
            )
            return event_from_beat(
                self.name,
                beat.action,
                beat.surface_id,
                url,
                bool(status and 200 <= status < 400),
                status=status,
                bytes=http_bytes or None,
                title=title[:180] if title else None,
                dwell_s=beat.dwell_s,
                extra={
                    "note": beat.note,
                    "http_requests": http_requests,
                    "http_bytes": http_bytes,
                    **harvest,
                },
            )
        except Exception as exc:  # noqa: BLE001 — log and keep the daemon alive
            log.warning("live beat failed: %s", exc)
            return event_from_beat(
                self.name,
                beat.action,
                beat.surface_id,
                beat.url,
                False,
                error=str(exc)[:300],
                dwell_s=beat.dwell_s,
            )
        finally:
            page.close()
