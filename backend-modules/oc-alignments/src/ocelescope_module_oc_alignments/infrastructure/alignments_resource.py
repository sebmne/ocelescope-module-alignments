"""Alignments as an Ocelescope resource: listed, viewed, exported and imported by the host, and
readable by other modules."""

from datetime import datetime

from ocelescope import Resource, TableColumn, TableViz

from ocelescope_module_oc_alignments.domain.models.alignment import UNIT
from ocelescope_module_oc_alignments.domain.models.alignment_set import AlignmentSet, VariantAlignment
from ocelescope_module_oc_alignments.domain.models.log import Event, Execution
from ocelescope_module_oc_alignments.domain.models.net import ObjectCentricNet


class OCAlignmentsResource(Resource):
    label = "OC Alignments"
    description = (
        "Object-centric alignments (Liss, Adams, van der Aalst, ER 2023) of a log with an "
        "object-centric Petri net: per variant, the moves of an optimal alignment, and how each "
        "process execution maps onto its variant."
    )

    log_name: str
    net_name: str
    ocel_id: str | None = None
    net_id: str | None = None
    net: ObjectCentricNet
    created_at: datetime
    seconds_per_variant: float
    events: tuple[Event, ...]
    object_types: dict[str, str]
    executions: tuple[Execution, ...]
    variants: tuple[VariantAlignment, ...]

    @classmethod
    def from_alignment_set(cls, alignments: AlignmentSet) -> "OCAlignmentsResource":
        return cls(**{name: getattr(alignments, name) for name in AlignmentSet.model_fields})

    def to_alignment_set(self) -> AlignmentSet:
        return AlignmentSet(**{name: getattr(self, name) for name in AlignmentSet.model_fields})

    def visualize(self) -> TableViz:
        rows = self.to_alignment_set().rows()
        return TableViz(
            columns=[
                TableColumn(id="variant", label="Variant"),
                TableColumn(id="frequency", label="Executions", data_type="number"),
                TableColumn(id="events", label="Events", data_type="number"),
                TableColumn(id="objects", label="Objects"),
                TableColumn(id="deviations", label="Deviations", data_type="number"),
                TableColumn(id="cost", label="Cost", data_type="number"),
                TableColumn(id="status", label="Status"),
            ],
            rows=[
                {
                    "variant": row.id,
                    "frequency": row.frequency,
                    "events": row.events,
                    "objects": ", ".join(f"{count} {t}" for t, count in row.objects.items()),
                    "deviations": row.deviations,
                    "cost": row.cost / UNIT if row.cost is not None else None,
                    "status": row.status,
                }
                for row in rows
            ],
        )
