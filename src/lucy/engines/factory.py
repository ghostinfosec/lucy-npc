"""Pick an engine by name."""

from __future__ import annotations

from lucy.engines.live_http import LiveHttpEngine
from lucy.engines.live_public import LivePublicEngine
from lucy.engines.live_session import LiveSessionEngine
from lucy.engines.local import LocalEngine


def get_engine(name: str):
    mapping = {
        "local": LocalEngine,
        "live_http": LiveHttpEngine,
        "live_public": LivePublicEngine,
        "live_session": LiveSessionEngine,
    }
    if name not in mapping:
        raise ValueError(f"unknown engine {name!r}. try: {', '.join(mapping)}")
    return mapping[name]()
