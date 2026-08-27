"""Planner and local engine tests. No live network."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from random import Random
from zoneinfo import ZoneInfo

from lucy.engines.live_session import LiveSessionEngine
from lucy.engines.local import LocalEngine
from lucy.persona import load_persona
from lucy.planner import next_beat
from lucy.store import EventLog

ROOT = Path(__file__).resolve().parents[1]
PERSONA = load_persona(ROOT / "data/personas/wool.json")


def test_persona_has_live_urls() -> None:
    assert all(s.url.startswith("https://") for s in PERSONA.surfaces)


def test_sleep_outside_windows() -> None:
    night = datetime(2026, 8, 26, 3, 0, tzinfo=ZoneInfo(PERSONA.timezone))
    beat = next_beat(PERSONA, now=night, rng=Random(1))
    assert beat.action.value == "sleep"


def test_force_open_at_night() -> None:
    night = datetime(2026, 8, 26, 3, 0, tzinfo=ZoneInfo(PERSONA.timezone))
    beat = next_beat(PERSONA, now=night, rng=Random(1), force="open")
    assert beat.action.value == "open"
    assert beat.url and beat.url.startswith("https://")
    assert "forced" in beat.note


def test_evening_opens_something() -> None:
    evening = datetime(2026, 8, 26, 20, 0, tzinfo=ZoneInfo(PERSONA.timezone))
    actions = {next_beat(PERSONA, now=evening, rng=Random(i)).action.value for i in range(40)}
    assert "sleep" not in actions
    assert actions & {"open", "scroll", "skip", "idle"}


def test_local_engine_and_log(tmp_path: Path) -> None:
    evening = datetime(2026, 8, 26, 20, 0, tzinfo=ZoneInfo(PERSONA.timezone))
    beat = next_beat(PERSONA, now=evening, rng=Random(3))
    event = LocalEngine().run(PERSONA, beat)
    log = EventLog(tmp_path)
    log.append(event)
    rows = log.tail(1)
    assert rows[0]["engine"] == "local"
    assert rows[0]["extra"]["rehearsal"] is True


def test_live_session_stays_a_hole() -> None:
    evening = datetime(2026, 8, 26, 20, 0, tzinfo=ZoneInfo(PERSONA.timezone))
    beat = next_beat(PERSONA, now=evening, rng=Random(3))
    try:
        LiveSessionEngine().run(PERSONA, beat)
        raise AssertionError("live_session must not run in v0.1")
    except NotImplementedError:
        pass
