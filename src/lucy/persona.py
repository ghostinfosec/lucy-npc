"""Load persona JSON. Side effect: reads a file from disk."""

from __future__ import annotations

import json
from pathlib import Path

from lucy.allowlist import assert_public_url, load_allowlist
from lucy.models import Persona, Surface, Window

DEFAULT_ALLOWLIST = Path(__file__).resolve().parents[2] / "data" / "allowlist.json"


def load_persona(path: Path, allowlist_path: Path | None = None) -> Persona:
    """Read and validate a persona file. Raises ValueError on missing keys."""
    raw = json.loads(path.read_text(encoding="utf-8"))
    spec = load_allowlist(allowlist_path or DEFAULT_ALLOWLIST)
    windows = tuple(
        Window(
            start_hour=int(w["start_hour"]),
            end_hour=int(w["end_hour"]),
            surfaces=tuple(w["surfaces"]),
            intensity=float(w["intensity"]),
        )
        for w in raw["windows"]
    )
    surfaces = []
    for item in raw["surfaces"]:
        assert_public_url(item["url"], spec)
        surfaces.append(Surface(id=item["id"], url=item["url"], kind=item["kind"]))
    dwell = raw["dwell_seconds"]
    scroll = raw["scroll_px"]
    return Persona(
        name=str(raw["name"]),
        timezone=str(raw["timezone"]),
        locale=str(raw["locale"]),
        user_agent=str(raw["user_agent"]),
        windows=windows,
        surfaces=tuple(surfaces),
        dwell_seconds=(float(dwell[0]), float(dwell[1])),
        scroll_px=(int(scroll[0]), int(scroll[1])),
        viewport_width=int(raw.get("viewport_width", 412)),
        viewport_height=int(raw.get("viewport_height", 915)),
        device_scale_factor=float(raw.get("device_scale_factor", 2.625)),
        color_scheme=str(raw.get("color_scheme", "light")),
    )
