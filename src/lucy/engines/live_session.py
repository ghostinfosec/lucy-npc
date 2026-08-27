"""Logged-in live sessions. Stub.

The art still wants this later: export storage_state.json from YOUR browser,
drop it on the Pi, Lucy continues as you. Not as a stranger. Not as a farm.

v0.1 refuses to run so the hole stays honest.
"""

from __future__ import annotations

from lucy.models import Event, Persona, PlannedBeat


class LiveSessionEngine:
    name = "live_session"

    def run(self, persona: Persona, beat: PlannedBeat) -> Event:
        del persona, beat
        raise NotImplementedError(
            "live_session is a stub. Export Playwright storage_state from your "
            "own browser when you are ready. Lucy will not mint accounts."
        )
