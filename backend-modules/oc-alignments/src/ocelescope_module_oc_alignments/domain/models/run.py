"""An alignment run: a log against a net, one variant at a time, kept as alignments when done."""

from datetime import UTC, datetime
from typing import Literal, Self
from uuid import uuid4

from pydantic import computed_field

from ocelescope_module_oc_alignments.domain.models.alignment_set import AlignmentSet, VariantAlignment, VariantOutcome
from ocelescope_module_oc_alignments.domain.models.base import Model
from ocelescope_module_oc_alignments.domain.models.log import EventLog, Execution, Variant
from ocelescope_module_oc_alignments.domain.models.net import ObjectCentricNet

RunStatus = Literal["running", "done", "failed", "cancelled"]
VariantStatus = Literal["queued", "aligned", "timeout", "no_alignment", "failed", "cancelled"]


class VariantProgress(Model):
    id: str
    frequency: int
    events: int
    objects: int
    status: VariantStatus
    deviations: int | None = None
    seconds: float | None = None
    error: str | None = None


class RunSummary(Model):
    id: str
    net_id: str
    net_name: str
    ocel_id: str
    ocel_name: str
    created_at: datetime
    seconds_per_variant: float
    status: RunStatus
    error: str | None
    # unknown until the executions are found
    executions: int | None
    variants: tuple[VariantProgress, ...]
    # the alignments kept once the run is done
    alignments_id: str | None

    @computed_field
    @property
    def finished(self) -> int:
        return sum(variant.status != "queued" for variant in self.variants)


class Run(Model):
    """The aggregate: it changes only through its methods, each returning the next state, so a
    late result cannot reopen a cancelled run."""

    id: str
    net_id: str
    net_name: str
    ocel_id: str
    net: ObjectCentricNet
    log: EventLog
    seconds_per_variant: float
    created_at: datetime
    status: RunStatus = "running"
    error: str | None = None
    executions: tuple[Execution, ...] | None = None
    variants: tuple[Variant, ...] = ()
    outcomes: dict[str, VariantOutcome] = {}
    alignments_id: str | None = None

    @classmethod
    def start(
        cls, *, net_id: str, net_name: str, net: ObjectCentricNet, ocel_id: str, log: EventLog, seconds: float
    ) -> Self:
        return cls(
            id=str(uuid4()),
            net_id=net_id,
            net_name=net_name,
            net=net,
            ocel_id=ocel_id,
            log=log,
            seconds_per_variant=seconds,
            created_at=datetime.now(UTC),
        )

    def with_variants(self, executions: tuple[Execution, ...], variants: tuple[Variant, ...]) -> Self:
        if self.status != "running":
            return self
        return self.model_copy(update={"executions": executions, "variants": variants})

    def with_outcome(self, variant_id: str, outcome: VariantOutcome) -> Self:
        if self.status != "running":
            return self
        return self.model_copy(update={"outcomes": {**self.outcomes, variant_id: outcome}})

    def finished(self, error: str | None = None) -> Self:
        if self.status != "running":
            return self
        missing = {
            v.id: VariantOutcome(status="failed", error=error or "The run ended before this variant was aligned.")
            for v in self.variants
            if v.id not in self.outcomes
        }
        failed = error is not None or self.executions is None
        return self.model_copy(
            update={
                "status": "failed" if failed else "done",
                "error": error or (None if self.executions is not None else "No executions were found."),
                "outcomes": {**self.outcomes, **missing},
            }
        )

    def cancelled(self) -> Self:
        if self.status != "running":
            return self
        return self.model_copy(update={"status": "cancelled"})

    def saved(self, alignments_id: str) -> Self:
        return self.model_copy(update={"alignments_id": alignments_id})

    def alignment_set(self) -> AlignmentSet:
        """The run's alignments, once it is done."""
        if self.status != "done" or self.executions is None:
            raise ValueError("Only a finished run has alignments.")
        return AlignmentSet(
            log_name=self.log.name,
            net_name=self.net_name,
            ocel_id=self.ocel_id,
            net_id=self.net_id,
            net=self.net,
            created_at=self.created_at,
            seconds_per_variant=self.seconds_per_variant,
            events=self.log.events,
            object_types=self.log.object_types,
            executions=self.executions,
            variants=tuple(VariantAlignment(variant=v, outcome=self.outcomes[v.id]) for v in self.variants),
        )

    def summary(self) -> RunSummary:
        progress = []
        for variant in self.variants:
            representative = self.executions[variant.representative] if self.executions else None
            outcome = self.outcomes.get(variant.id)
            status: VariantStatus = (
                outcome.status if outcome else ("cancelled" if self.status == "cancelled" else "queued")
            )
            progress.append(
                VariantProgress(
                    id=variant.id,
                    frequency=variant.frequency,
                    events=len(representative.events) if representative else 0,
                    objects=len(representative.objects) if representative else 0,
                    status=status,
                    deviations=outcome.alignment.deviations if outcome and outcome.alignment else None,
                    seconds=outcome.seconds if outcome else None,
                    error=outcome.error if outcome else None,
                )
            )
        return RunSummary(
            id=self.id,
            net_id=self.net_id,
            net_name=self.net_name,
            ocel_id=self.ocel_id,
            ocel_name=self.log.name,
            created_at=self.created_at,
            seconds_per_variant=self.seconds_per_variant,
            status=self.status,
            error=self.error,
            executions=len(self.executions) if self.executions is not None else None,
            variants=tuple(progress),
            alignments_id=self.alignments_id,
        )
