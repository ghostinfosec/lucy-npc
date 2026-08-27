"""Metric rollups. No network."""

from pathlib import Path

from lucy.fingerprint import describe
from lucy.metrics import summarize
from lucy.persona import load_persona


def test_summarize_counts_hosts_and_http() -> None:
    events = [
        {
            "action": "open",
            "ok": True,
            "url": "https://weather.com/today",
            "bytes": 100,
            "extra": {"http_requests": 8, "http_bytes": 100, "harvest_hits": 3, "harvest": [{"host": "stats.g.doubleclick.net", "vendor": "Google", "kind": "ad", "count": 3}]},
        },
        {
            "action": "open",
            "ok": False,
            "url": "https://en.wikipedia.org/wiki/X",
            "extra": {"http_requests": 2},
        },
        {"action": "sleep", "ok": True, "url": None},
    ]
    out = summarize(events)
    assert out["beats"] == 3
    assert out["ok"] == 2
    assert out["fail"] == 1
    assert out["http_requests"] == 10
    assert out["harvest_hits"] == 3
    assert out["vendors"][0]["vendor"] == "Google"
    assert len(out["vendors"]) <= 10
    assert len(out["broker_hosts"]) <= 10
    assert out["hosts"][0]["host"] in {"weather.com", "en.wikipedia.org"}
    assert out["live_capture"] is True
    assert "10 fetches" in out["unit"]
    assert out["last_open"]["url"] == "https://en.wikipedia.org/wiki/X"
    assert out["last_open"]["harvest"] == []


def test_fingerprint_live_http_is_not_a_phone() -> None:
    persona = load_persona(Path(__file__).resolve().parents[1] / "data/personas/wool.json")
    live = describe(persona, "live_public")
    http = describe(persona, "live_http")
    assert "mobile" in live["presents_as"].lower() or "Chrome" in live["presents_as"]
    assert "not a phone" in http["presents_as"].lower()
    assert "JA3" in live["fingerprint_and_fraud"]
