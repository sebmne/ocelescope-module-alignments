"""The alignments of a log with a net: one per variant, carried over to each of its executions.
This is what is kept (as an Ocelescope resource) and explored."""

from collections import Counter
from datetime import datetime
from typing import Literal, Self

from pydantic import Field, model_validator

from ocelescope_module_oc_alignments.domain.exceptions import UnknownExecution, UnknownVariant
from ocelescope_module_oc_alignments.domain.models.alignment import Alignment, Move
from ocelescope_module_oc_alignments.domain.models.base import Model
from ocelescope_module_oc_alignments.domain.models.log import Event, Execution, Variant
from ocelescope_module_oc_alignments.domain.models.net import ObjectCentricNet

Outcome = Literal["aligned", "timeout", "no_alignment", "failed"]


class VariantOutcome(Model):
    """How aligning a variant ended."""

    status: Outcome
    alignment: Alignment | None = None
    seconds: float | None = None
    error: str | None = None


class VariantAlignment(Model):
    variant: Variant
    outcome: VariantOutcome


class AlignmentSetSummary(Model):
    id: str
    name: str
    log_name: str
    net_name: str
    # the session's log and net they were computed from (None for older resources)
    ocel_id: str | None
    net_id: str | None
    created_at: datetime
    executions: int
    variants: int
    aligned_variants: int
    fitting_executions: int
    # the deviations of all executions, in objects
    deviations: int


class VariantRow(Model):
    """A variant as the explorer lists it."""

    id: str
    frequency: int
    events: int
    objects: dict[str, int]  # per object type
    activities: tuple[str, ...]  # of its representative, in order
    # the representative's alignment, for the variant's alignment strip (empty if it has none)
    moves: tuple[Move, ...]
    status: Outcome
    deviations: int | None
    cost: int | None
    seconds: float | None
    # why it has no alignment, if it has none
    error: str | None = None


class ExecutionRow(Model):
    index: int
    variant: str
    objects: tuple[str, ...]
    object_types: dict[str, str]
    start: datetime
    end: datetime


class AlignedExecution(Model):
    """One process execution with its events and its alignment."""

    index: int
    variant: str
    events: tuple[Event, ...]
    object_types: dict[str, str]
    status: Outcome
    alignment: Alignment | None
    error: str | None


class AlignmentsOverview(Model):
    """What the explorer starts from: the summary and every variant."""

    summary: AlignmentSetSummary
    object_types: tuple[str, ...]
    variants: tuple[VariantRow, ...]


class VariantDetail(Model):
    row: VariantRow
    executions: tuple[ExecutionRow, ...]
    representative: AlignedExecution


class AlignmentSet(Model):
    log_name: str
    net_name: str
    # the session's log and net they were computed from
    ocel_id: str | None = None
    net_id: str | None = None
    net: ObjectCentricNet
    created_at: datetime
    seconds_per_variant: float = Field(gt=0)
    events: tuple[Event, ...]
    object_types: dict[str, str]
    executions: tuple[Execution, ...]
    variants: tuple[VariantAlignment, ...]

    @model_validator(mode="after")
    def _covers_every_execution_once(self) -> Self:
        covered = sorted(m.execution for v in self.variants for m in v.variant.executions)
        if covered != [x.index for x in self.executions]:
            raise ValueError("Every execution belongs to exactly one variant.")
        return self

    def summary(self, alignments_id: str, name: str) -> AlignmentSetSummary:
        aligned = [v for v in self.variants if v.outcome.alignment is not None]
        return AlignmentSetSummary(
            id=alignments_id,
            name=name,
            log_name=self.log_name,
            net_name=self.net_name,
            ocel_id=self.ocel_id,
            net_id=self.net_id,
            created_at=self.created_at,
            executions=len(self.executions),
            variants=len(self.variants),
            aligned_variants=len(aligned),
            fitting_executions=sum(
                v.variant.frequency for v in aligned if v.outcome.alignment and v.outcome.alignment.deviations == 0
            ),
            deviations=sum(
                v.variant.frequency * v.outcome.alignment.deviations for v in aligned if v.outcome.alignment
            ),
        )

    def rows(self) -> tuple[VariantRow, ...]:
        events = {e.id: e for e in self.events}
        rows = []
        for v in self.variants:
            representative = self.executions[v.variant.representative]
            alignment = v.outcome.alignment
            rows.append(
                VariantRow(
                    id=v.variant.id,
                    frequency=v.variant.frequency,
                    events=len(representative.events),
                    objects=dict(sorted(Counter(self.object_types[o] for o in representative.objects).items())),
                    activities=tuple(events[e].activity for e in representative.events),
                    moves=alignment.moves if alignment else (),
                    status=v.outcome.status,
                    deviations=alignment.deviations if alignment else None,
                    cost=alignment.cost if alignment else None,
                    seconds=v.outcome.seconds,
                    error=v.outcome.error,
                )
            )
        return tuple(rows)

    def variant(self, variant_id: str) -> VariantAlignment:
        found = next((v for v in self.variants if v.variant.id == variant_id), None)
        if found is None:
            raise UnknownVariant(variant_id)
        return found

    def executions_of(self, variant_id: str) -> tuple[ExecutionRow, ...]:
        events = {e.id: e for e in self.events}
        rows = []
        for mapping in self.variant(variant_id).variant.executions:
            execution = self.executions[mapping.execution]
            times = [events[e].timestamp for e in execution.events]
            rows.append(
                ExecutionRow(
                    index=execution.index,
                    variant=variant_id,
                    objects=execution.objects,
                    object_types={o: self.object_types[o] for o in execution.objects},
                    start=min(times),
                    end=max(times),
                )
            )
        return tuple(rows)

    def execution(self, index: int) -> AlignedExecution:
        if not 0 <= index < len(self.executions):
            raise UnknownExecution(index)
        execution = self.executions[index]
        owner = next(v for v in self.variants for m in v.variant.executions if m.execution == index)
        mapping = next(m for m in owner.variant.executions if m.execution == index)
        events = {e.id: e for e in self.events}
        alignment = owner.outcome.alignment
        return AlignedExecution(
            index=index,
            variant=owner.variant.id,
            events=tuple(events[e] for e in execution.events),
            object_types={o: self.object_types[o] for o in execution.objects},
            status=owner.outcome.status,
            alignment=alignment.renamed(mapping.events, mapping.objects) if alignment else None,
            error=owner.outcome.error,
        )

    def overview(self, alignments_id: str, name: str) -> AlignmentsOverview:
        return AlignmentsOverview(
            summary=self.summary(alignments_id, name),
            object_types=tuple(sorted(set(self.object_types.values()))),
            variants=self.rows(),
        )

    def variant_detail(self, variant_id: str) -> VariantDetail:
        found = self.variant(variant_id)
        return VariantDetail(
            row=next(row for row in self.rows() if row.id == variant_id),
            executions=self.executions_of(variant_id),
            representative=self.execution(found.variant.representative),
        )
