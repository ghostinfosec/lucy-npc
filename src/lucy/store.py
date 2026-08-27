"""JSONL event log. Side effects: append-only writes under log dir."""

from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

from lucy.models import Action, Event


class EventLog:
    def __init__(self, directory: Path) -> None:
        self.directory = directory
        self.directory.mkdir(parents=True, exist_ok=True)
        self.path = self.directory / "lucy.jsonl"

    def append(self, event: Event) -> None:
        payload = asdict(event)
        payload["action"] = event.action.value
        line = json.dumps(payload, ensure_ascii=False)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(line + "\n")

    def tail(self, n: int = 40) -> list[dict]:
        return self.read(max_lines=n)[-n:]

    def read(self, max_lines: int = 8000) -> list[dict]:
        """Newest-capped JSONL read. Side effect: reads the log file."""
        if not self.path.exists():
            return []
        lines = self.path.read_text(encoding="utf-8").splitlines()
        out: list[dict] = []
        for line in lines[-max_lines:]:
            if line.strip():
                out.append(json.loads(line))
        return out


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def event_from_beat(
    engine: str,
    action: Action,
    surface_id: str | None,
    url: str | None,
    ok: bool,
    **kwargs: object,
) -> Event:
    return Event(
        ts=utc_now(),
        action=action,
        engine=engine,
        surface_id=surface_id,
        url=url,
        ok=ok,
        status=kwargs.get("status"),  # type: ignore[arg-type]
        bytes=kwargs.get("bytes"),  # type: ignore[arg-type]
        title=kwargs.get("title"),  # type: ignore[arg-type]
        dwell_s=kwargs.get("dwell_s"),  # type: ignore[arg-type]
        error=kwargs.get("error"),  # type: ignore[arg-type]
        extra=dict(kwargs.get("extra") or {}),  # type: ignore[arg-type]
    )
