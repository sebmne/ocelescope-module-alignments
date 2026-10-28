"""Object-centric event logs, cut into process executions and grouped into variants (Liss et
al., Sect. 3: a process execution is a connected component of the graph of events and objects)."""

from datetime import datetime
from typing import Self

from pydantic import Field, model_validator

from ocelescope_module_oc_alignments.domain.models.base import Model


class Event(Model):
    id: str = Field(min_length=1)
    activity: str
    timestamp: datetime
    # sorted, so that equal events compare equal
    objects: tuple[str, ...] = ()


class EventLog(Model):
    """Events in timestamp order (ties by id), with the type of every object."""

    name: str
    events: tuple[Event, ...]
    object_types: dict[str, str]

    @model_validator(mode="after")
    def _ordered_and_typed(self) -> Self:
        order = [(e.timestamp, e.id) for e in self.events]
        if order != sorted(order):
            raise ValueError("The events must be in timestamp order.")
        untyped = {o for e in self.events for o in e.objects} - set(self.object_types)
        if untyped:
            raise ValueError(f"Objects without a type: {', '.join(sorted(untyped)[:5])}")
        return self


class Execution(Model):
    """A process execution: its events in timestamp order and its objects (sorted)."""

    index: int = Field(ge=0)
    events: tuple[str, ...]
    objects: tuple[str, ...]


class ExecutionMapping(Model):
    """How an execution matches its variant's representative: each event and object of the
    representative, to the execution's own. The representative maps onto itself."""

    execution: int = Field(ge=0)
    events: dict[str, str]
    objects: dict[str, str]


class Variant(Model):
    """Executions that are isomorphic: equal up to renaming events and objects, with activities,
    object types and the order of every object's events kept. One alignment serves them all."""

    id: str
    representative: int = Field(ge=0)
    executions: tuple[ExecutionMapping, ...] = Field(min_length=1)

    @property
    def frequency(self) -> int:
        return len(self.executions)
