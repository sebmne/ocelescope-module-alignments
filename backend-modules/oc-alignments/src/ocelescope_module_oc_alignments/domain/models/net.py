"""Accepting object-centric Petri nets (van der Aalst, Berti), as Liss et al. align against them."""

from typing import Self

from pydantic import Field, model_validator

from ocelescope_module_oc_alignments.domain.exceptions import InvalidNet
from ocelescope_module_oc_alignments.domain.models.base import Model


class NetPlace(Model):
    """A place holds objects of one type. Initially, an initial place holds every object of its
    type; at the end, every final place must hold every object of its type."""

    id: str = Field(min_length=1)
    object_type: str = Field(min_length=1)
    initial: bool = False
    final: bool = False


class NetTransition(Model):
    id: str = Field(min_length=1)
    # None for a silent transition
    label: str | None = None

    @property
    def silent(self) -> bool:
        return self.label is None


class NetArc(Model):
    """A normal arc moves one object of its place's type, a variable arc any number."""

    source: str
    target: str
    variable: bool = False


class ObjectCentricNet(Model):
    places: tuple[NetPlace, ...]
    transitions: tuple[NetTransition, ...]
    arcs: tuple[NetArc, ...]

    @model_validator(mode="after")
    def _well_formed(self) -> Self:
        places = {p.id: p for p in self.places}
        transitions = {t.id: t for t in self.transitions}
        if len(places) + len(transitions) != len(self.places) + len(self.transitions):
            raise InvalidNet("Place and transition ids must be unique.")
        if places.keys() & transitions.keys():
            raise InvalidNet("A place and a transition share an id.")
        for arc in self.arcs:
            place_to_transition = arc.source in places and arc.target in transitions
            transition_to_place = arc.source in transitions and arc.target in places
            if not (place_to_transition or transition_to_place):
                raise InvalidNet(f"The arc {arc.source} → {arc.target} must connect a place and a transition.")
        for transition in self.transitions:
            consumed = {places[a.source].object_type for a in self.arcs if a.target == transition.id}
            produced = {places[a.target].object_type for a in self.arcs if a.source == transition.id}
            if produced - consumed:
                raise InvalidNet(
                    f"The transition {transition.label or transition.id} produces objects of the types "
                    f"{', '.join(sorted(produced - consumed))} without consuming any: objects start in "
                    "initial places."
                )
        return self

    @property
    def object_types(self) -> tuple[str, ...]:
        return tuple(sorted({p.object_type for p in self.places}))

    @property
    def labels(self) -> frozenset[str]:
        return frozenset(t.label for t in self.transitions if t.label is not None)


class NetSummary(Model):
    """An object-centric Petri net as it is listed: its name and size, and why it cannot be
    aligned with, if it cannot."""

    id: str
    name: str
    places: int
    transitions: int
    object_types: tuple[str, ...]
    problem: str | None = None

    @classmethod
    def of(cls, net_id: str, name: str, net: ObjectCentricNet) -> Self:
        return cls(
            id=net_id,
            name=name,
            places=len(net.places),
            transitions=len(net.transitions),
            object_types=net.object_types,
        )
