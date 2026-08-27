"""YouTube search → first watch → play. No I/O except the Playwright page passed in."""

from __future__ import annotations

from typing import Any
from urllib.parse import urlparse

from lucy.allowlist import assert_public_url

_FIRST_WATCH_JS = """() => {
  const sels = [
    'ytm-media-item a[href*="/watch"]',
    'ytm-video-with-context-renderer a[href*="/watch"]',
    'ytd-video-renderer a[href*="/watch?v="]',
    'a[href*="/watch?v="]',
  ];
  for (const s of sels) {
    const a = document.querySelector(s);
    if (a && a.href && a.href.includes("/watch")) return a.href;
  }
  return "";
}"""


def is_results_url(url: str) -> bool:
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()
    path = (parsed.path or "").rstrip("/")
    return host.endswith("youtube.com") and path.endswith("/results")


def _consent(page: Any) -> None:
    """YouTube cookie wall only. Not a captive portal."""
    for frame in page.frames:
        btn = frame.get_by_role("button", name="Accept all", exact=False)
        try:
            if btn.count() and btn.first.is_visible():
                btn.first.click(timeout=2_500, force=True)
                page.wait_for_load_state("domcontentloaded")
                return
        except Exception:  # noqa: BLE001 — banner may be a decoy
            continue


def _first_watch_url(page: Any) -> str:
    page.wait_for_selector('a[href*="/watch"]', timeout=12_000)
    href = page.evaluate(_FIRST_WATCH_JS)
    if not href:
        raise RuntimeError("no watch result on the search page")
    return str(href)


def _try_play(page: Any) -> None:
    page.locator("video").first.wait_for(state="attached", timeout=10_000)
    paused = page.evaluate(
        "() => { const v = document.querySelector('video'); return !v || v.paused; }"
    )
    if not paused:
        return
    for sel in (".ytp-large-play-button", "button.ytp-play-button", "video"):
        loc = page.locator(sel).first
        try:
            if loc.count():
                loc.click(timeout=2_000, force=True)
                return
        except Exception:  # noqa: BLE001
            continue


def follow_search(page: Any, spec: dict) -> None:
    """From /results, consent if needed, open the first /watch, try to play.

    Mobile YouTube puts a thumbnail over the <a>; clicking the link times out.
    Take the href and go there.
    """
    _consent(page)
    assert_public_url(page.url, spec)
    target = _first_watch_url(page)
    assert_public_url(target, spec)
    page.goto(target, wait_until="domcontentloaded", timeout=25_000)
    _consent(page)
    assert_public_url(page.url, spec)
    _try_play(page)
