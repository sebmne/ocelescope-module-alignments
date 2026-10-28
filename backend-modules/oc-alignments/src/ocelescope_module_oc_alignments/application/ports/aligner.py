from typing import Protocol

from ocelescope_module_oc_alignments.domain.models.alignment_set import VariantOutcome
from ocelescope_module_oc_alignments.domain.models.log import EventLog, Execution, Variant
from ocelescope_module_oc_alignments.domain.models.net import ObjectCentricNet


class AlignmentListener(Protocol):
    """Hears how an alignment job proceeds. Called from the job's own thread."""

    def variants_found(self, executions: tuple[Execution, ...], variants: tuple[Variant, ...]) -> None: ...

    def variant_aligned(self, variant_id: str, outcome: VariantOutcome) -> None: ...

    def finished(self, error: str | None) -> None:
        """The job ended, normally (no error) or not."""
        ...


class AlignmentJob(Protocol):
    def cancel(self) -> None: ...


class Aligner(Protocol):
    """Computes the optimal alignment of every variant of a log with a net, in the background."""

    def start(
        self, net: ObjectCentricNet, log: EventLog, seconds_per_variant: float, listener: AlignmentListener
    ) -> AlignmentJob: ...
