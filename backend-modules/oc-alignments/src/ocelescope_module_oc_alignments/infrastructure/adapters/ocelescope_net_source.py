from ocelescope import PetriNet
from ocelescope.resource.default.petri_net import ArcType
from ocelescope_backend.app.internal.exceptions import NotFound
from ocelescope_backend.app.internal.session import Session
from pydantic import ValidationError

from ocelescope_module_oc_alignments.domain.exceptions import InvalidNet, UnknownNet
from ocelescope_module_oc_alignments.domain.models.net import (
    NetArc,
    NetPlace,
    NetSummary,
    NetTransition,
    ObjectCentricNet,
)


class OcelescopeNetSource:
    """The object-centric Petri nets among the session's resources (Ocelescope's `PetriNet`,
    e.g. discovered by its inductive miner)."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def list(self) -> tuple[NetSummary, ...]:
        summaries = []
        for resource in self._session.list_resources():
            if resource.schema_hash != PetriNet.get_schema_hash():
                continue
            try:
                net = self._load(resource.id)
            except Exception as error:  # one unreadable resource must not hide the others
                summaries.append(_unusable(resource.id, resource.name, None, f"It cannot be read: {error}"))
                continue
            try:
                summaries.append(NetSummary.of(resource.id, resource.name, _to_net(net)))
            except InvalidNet as error:
                summaries.append(_unusable(resource.id, resource.name, net, str(error)))
        return tuple(summaries)

    def resource_type(self) -> str:
        return PetriNet.get_schema_hash()

    def get(self, net_id: str) -> tuple[str, ObjectCentricNet]:
        net = self._load(net_id)
        return self._session.get_resource(net_id).name, _to_net(net)

    def _load(self, net_id: str) -> PetriNet:
        try:
            stored = self._session.get_resource(net_id)
        except NotFound as error:
            raise UnknownNet(net_id) from error
        if stored.schema_hash != PetriNet.get_schema_hash():
            raise UnknownNet(net_id)
        return self._session.load_resource(net_id, PetriNet)


def _unusable(net_id: str, name: str, net: PetriNet | None, problem: str) -> NetSummary:
    return NetSummary(
        id=net_id,
        name=name,
        places=len(net.places) if net else 0,
        transitions=len(net.transitions) if net else 0,
        object_types=tuple(sorted({p.object_type for p in net.places})) if net else (),
        problem=problem,
    )


def _to_net(net: PetriNet) -> ObjectCentricNet:
    heavy = [a for a in net.arcs if a.weight != 1]
    if heavy:
        raise InvalidNet(
            f"The arc {heavy[0].source} → {heavy[0].target} has weight {heavy[0].weight}; arcs move one object."
        )
    try:
        return ObjectCentricNet(
            places=tuple(
                NetPlace(
                    id=p.name,
                    object_type=p.object_type,
                    initial=net.initial_marking.get(p.name, 0) > 0,
                    final=net.final_marking.get(p.name, 0) > 0,
                )
                for p in net.places
            ),
            transitions=tuple(NetTransition(id=t.name, label=t.label) for t in net.transitions),
            arcs=tuple(NetArc(source=a.source, target=a.target, variable=a.type == ArcType.VARIABLE) for a in net.arcs),
        )
    except ValidationError as error:
        raise InvalidNet(str(error)) from error
