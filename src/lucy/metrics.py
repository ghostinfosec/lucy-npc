"""Summaries over the JSONL body log. Reads files. No network."""

from __future__ import annotations

from collections import Counter
from urllib.parse import urlparse


def summarize(events: list[dict], limit_hosts: int = 24) -> dict:
    """Roll up beats, hosts, and HTTP resource counters. No I/O."""
    hosts: Counter[str] = Counter()
    actions: Counter[str] = Counter()
    ok = 0
    fail = 0
    http_requests = 0
    http_bytes = 0
    harvest_hits = 0
    beacons = 0
    vendors: Counter[str] = Counter()
    kinds: Counter[str] = Counter()
    broker_hosts: Counter[str] = Counter()
    engines: Counter[str] = Counter()
    last_open: dict | None = None
    for event in events:
        engine = str(event.get("engine") or "")
        if engine:
            engines[engine] += 1
        actions[str(event.get("action") or "")] += 1
        if event.get("action") == "open" and event.get("url"):
            last_open = event
        if event.get("ok"):
            ok += 1
        else:
            fail += 1
        extra = event.get("extra") or {}
        http_requests += int(extra.get("http_requests") or 0)
        http_bytes += int(event.get("bytes") or extra.get("http_bytes") or 0)
        harvest_hits += int(extra.get("harvest_hits") or 0)
        beacons += int(extra.get("beacons") or 0)
        for hit in extra.get("harvest") or []:
            if not isinstance(hit, dict):
                continue
            vendor = str(hit.get("vendor") or "unknown")
            vendors[vendor] += int(hit.get("count") or 1)
            kinds[str(hit.get("kind") or "ad")] += int(hit.get("count") or 1)
            host = str(hit.get("host") or "")
            if host:
                broker_hosts[host] += int(hit.get("count") or 1)
        url = event.get("url")
        if url:
            host = urlparse(str(url)).hostname
            if host:
                hosts[host] += 1
    live_capture = http_requests > 0 or any(name.startswith("live") for name in engines)
    if live_capture:
        unit = f"{http_requests} fetches. {harvest_hits} taken."
    elif events:
        unit = "No fetches yet."
    else:
        unit = "No looks yet."
    return {
        "beats": len(events),
        "ok": ok,
        "fail": fail,
        "http_requests": http_requests,
        "http_bytes": http_bytes,
        "hosts": [{"host": name, "beats": count} for name, count in hosts.most_common(limit_hosts)],
        "actions": dict(actions),
        "harvest_hits": harvest_hits,
        "beacons": beacons,
        "vendors": [{"vendor": name, "hits": count} for name, count in vendors.most_common(10)],
        "kinds": dict(kinds),
        "broker_hosts": [
            {"host": name, "hits": count} for name, count in broker_hosts.most_common(10)
        ],
        "unit": unit,
        "engines": dict(engines),
        "live_capture": live_capture,
        "last_open": (
            {
                "ts": last_open.get("ts"),
                "url": last_open.get("url"),
                "engine": last_open.get("engine"),
                "http_requests": int((last_open.get("extra") or {}).get("http_requests") or 0),
                "harvest_hits": int((last_open.get("extra") or {}).get("harvest_hits") or 0),
                "http_bytes": int(
                    last_open.get("bytes")
                    or (last_open.get("extra") or {}).get("http_bytes")
                    or 0
                ),
                "harvest": [
                    hit
                    for hit in ((last_open.get("extra") or {}).get("harvest") or [])
                    if isinstance(hit, dict)
                ],
            }
            if last_open
            else None
        ),
    }
