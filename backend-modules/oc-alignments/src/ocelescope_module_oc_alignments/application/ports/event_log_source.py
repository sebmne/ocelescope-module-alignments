from typing import Protocol

from ocelescope_module_oc_alignments.domain.models.log import EventLog


class EventLogSource(Protocol):
    """The user's object-centric event logs."""

    def read(self, ocel_id: str) -> EventLog:
        """The log; raises UnknownLog if there is none."""
        ...
