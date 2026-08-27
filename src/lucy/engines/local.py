"""CI engine. No network. Same planner, fake body."""

from __future__ import annotations

from lucy.models import Action, Event, Persona, PlannedBeat
from lucy.store import event_from_beat


class LocalEngine:
    name = "local"

    def run(self, persona: Persona, beat: PlannedBeat) -> Event:
        del persona
        if beat.action in {Action.SLEEP, Action.IDLE, Action.WAKE}:
            return event_from_beat(
                self.name,
                beat.action,
                beat.surface_id,
                beat.url,
                True,
                dwell_s=beat.dwell_s,
                extra={"note": beat.note, "rehearsal": True},
            )
        title = f"[local] {beat.surface_id or 'none'}"
        return event_from_beat(
            self.name,
            beat.action,
            beat.surface_id,
            beat.url,
            True,
            status=200,
            bytes=0,
            title=title,
            dwell_s=beat.dwell_s,
            extra={"note": beat.note, "rehearsal": True},
        )
