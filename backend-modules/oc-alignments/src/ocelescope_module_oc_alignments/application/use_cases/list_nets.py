from ocelescope_module_oc_alignments.application.ports.net_source import NetSource
from ocelescope_module_oc_alignments.domain.models.net import NetSummary


class ListNets:
    def __init__(self, *, nets: NetSource) -> None:
        self._nets = nets

    def execute(self) -> tuple[NetSummary, ...]:
        return self._nets.list()

    def resource_type(self) -> str:
        """The resource type of the nets (Ocelescope's Petri nets), for a resource picker."""
        return self._nets.resource_type()
