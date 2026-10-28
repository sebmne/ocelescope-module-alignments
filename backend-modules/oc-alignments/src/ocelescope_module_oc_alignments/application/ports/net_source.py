from typing import Protocol

from ocelescope_module_oc_alignments.domain.models.net import NetSummary, ObjectCentricNet


class NetSource(Protocol):
    """The user's object-centric Petri nets."""

    def list(self) -> tuple[NetSummary, ...]:
        """All of them, also those that cannot be aligned with (with the problem)."""
        ...

    def resource_type(self) -> str:
        """The resource type the nets are stored as, to pick them among the user's resources."""
        ...

    def get(self, net_id: str) -> tuple[str, ObjectCentricNet]:
        """The name and the net; raises UnknownNet if there is none, InvalidNet if it cannot be aligned with."""
        ...
