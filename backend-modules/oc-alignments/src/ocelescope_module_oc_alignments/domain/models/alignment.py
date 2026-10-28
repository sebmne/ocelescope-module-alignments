"""Object-centric alignments (Liss et al., Def. 9-11): moves that pair the events of a process
execution with the firings of a run of the net."""

from typing import Literal, Self

from pydantic import computed_field, model_validator

from ocelescope_module_oc_alignments.domain.models.base import Model

MoveKind = Literal["sync", "log", "model"]

# Liss et al. charge a silent model move a small ε, so that runs do not grow without need. Costs
# are kept in thousandths of an object, so ε is exact.
UNIT = 1000
EPSILON = 1


class Move(Model):
    """A synchronous move pairs an event with a firing, a log move has only the event, a model
    move only the firing. Its objects are those of the event or of the firing's binding."""

    kind: MoveKind
    event: str | None = None
    activity: str | None = None
    transition: str | None = None
    # the transition's label; None for a silent one
    label: str | None = None
    objects: tuple[str, ...] = ()
    # thousandths: an object costs UNIT, a silent move EPSILON
    cost: int = 0

    @model_validator(mode="after")
    def _sides(self) -> Self:
        has_log, has_model = self.event is not None, self.transition is not None
        if (has_log, has_model) != {"sync": (True, True), "log": (True, False), "model": (False, True)}[self.kind]:
            raise ValueError(f"A {self.kind} move has the wrong sides.")
        return self

    @property
    def silent(self) -> bool:
        return self.kind == "model" and self.label is None

    def renamed(self, events: dict[str, str], objects: dict[str, str]) -> "Move":
        return self.model_copy(
            update={
                "event": events[self.event] if self.event is not None else None,
                "objects": tuple(sorted(objects[o] for o in self.objects)),
            }
        )


class Alignment(Model):
    """The moves in the order the search found them; the log side covers every event once."""

    moves: tuple[Move, ...]

    @computed_field
    @property
    def cost(self) -> int:
        """In thousandths of an object (see UNIT)."""
        return sum(move.cost for move in self.moves)

    @computed_field
    @property
    def deviations(self) -> int:
        """The cost of the deviations, in objects: log and visible model moves."""
        return sum(move.cost for move in self.moves if not move.silent) // UNIT

    def renamed(self, events: dict[str, str], objects: dict[str, str]) -> "Alignment":
        """The alignment of another execution of the same variant."""
        return Alignment(moves=tuple(move.renamed(events, objects) for move in self.moves))
