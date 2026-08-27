"""Shared types. No I/O."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class Action(str, Enum):
    WAKE = "wake"
    OPEN = "open"
    SCROLL = "scroll"
    DWELL = "dwell"
    SKIP = "skip"
    IDLE = "idle"
    SLEEP = "sleep"
    LIKE = "like"
    FOLLOW = "follow"
    COMMENT = "comment"
    LOGIN = "login"


STUBBED_ACTIONS = frozenset({Action.LIKE, Action.FOLLOW, Action.COMMENT, Action.LOGIN})


@dataclass(frozen=True)
class Window:
    start_hour: int
    end_hour: int
    surfaces: tuple[str, ...]
    intensity: float  # 0-1, how often she acts inside the window


@dataclass(frozen=True)
class Surface:
    id: str
    url: str
    kind: str


@dataclass(frozen=True)
class Persona:
    name: str
    timezone: str
    locale: str
    user_agent: str
    windows: tuple[Window, ...]
    surfaces: tuple[Surface, ...]
    dwell_seconds: tuple[float, float]
    scroll_px: tuple[int, int]
    viewport_width: int = 412
    viewport_height: int = 915
    device_scale_factor: float = 2.625
    color_scheme: str = "light"


@dataclass
class PlannedBeat:
    action: Action
    surface_id: str | None
    url: str | None
    dwell_s: float
    note: str = ""


@dataclass
class Event:
    ts: str
    action: Action
    engine: str
    surface_id: str | None
    url: str | None
    ok: bool
    status: int | None = None
    bytes: int | None = None
    title: str | None = None
    dwell_s: float | None = None
    error: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)
