"""Circadian planner. Pure besides the clock and RNG."""

from __future__ import annotations

import random
from datetime import datetime
from zoneinfo import ZoneInfo

from lucy.models import Action, Persona, PlannedBeat, Surface


def _surface_map(persona: Persona) -> dict[str, Surface]:
    return {s.id: s for s in persona.surfaces}


def _in_window(hour: int, start: int, end: int) -> bool:
    if start == end:
        return False
    if start < end:
        return start <= hour < end
    return hour >= start or hour < end


def active_window(persona: Persona, now: datetime) -> tuple[int, float, tuple[str, ...]] | None:
    hour = now.hour
    for window in persona.windows:
        if _in_window(hour, window.start_hour, window.end_hour):
            return window.start_hour, window.intensity, window.surfaces
    return None


def dwell_for(persona: Persona, rng: random.Random) -> float:
    lo, hi = persona.dwell_seconds
    # Lognormal-ish: cluster short, allow a long stare.
    u = rng.random() ** 1.7
    return lo + (hi - lo) * u


def next_beat(
    persona: Persona,
    now: datetime | None = None,
    rng: random.Random | None = None,
    force: str | None = None,
) -> PlannedBeat:
    """Pick one beat for this moment. Side-effect free if now/rng provided."""
    rng = rng or random.Random()
    if force in {"open", "1", "true", "yes"}:
        surface = next((s for s in persona.surfaces if s.id == "weather"), persona.surfaces[0])
        return PlannedBeat(
            Action.OPEN,
            surface.id,
            surface.url,
            8.0,
            "forced open (ignore circadian)",
        )
    tz = ZoneInfo(persona.timezone)
    now = now or datetime.now(tz)
    surfaces = _surface_map(persona)
    window = active_window(persona, now)
    if window is None:
        return PlannedBeat(Action.SLEEP, None, None, 0.0, "outside circadian windows")

    _, intensity, surface_ids = window
    if rng.random() > intensity:
        return PlannedBeat(Action.IDLE, None, None, rng.uniform(8, 25), "quiet inside window")

    sid = rng.choice(surface_ids)
    surface = surfaces[sid]
    roll = rng.random()
    dwell = dwell_for(persona, rng)
    if roll < 0.08:
        return PlannedBeat(Action.SKIP, sid, surface.url, min(dwell, 4.0), "thumb slip")
    if roll < 0.18:
        return PlannedBeat(Action.SCROLL, sid, surface.url, dwell, "keep moving")
    return PlannedBeat(Action.OPEN, sid, surface.url, dwell, "ordinary look")
