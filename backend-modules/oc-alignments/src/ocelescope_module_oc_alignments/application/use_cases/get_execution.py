from dataclasses import dataclass

from ocelescope_module_oc_alignments.application.ports.alignment_repository import AlignmentRepository
from ocelescope_module_oc_alignments.domain.models.alignment_set import AlignedExecution


@dataclass(frozen=True, kw_only=True)
class GetExecutionCommand:
    alignments_id: str
    index: int


class GetExecution:
    """A process execution with its own events and its variant's alignment, renamed to them."""

    def __init__(self, *, alignments: AlignmentRepository) -> None:
        self._alignments = alignments

    def execute(self, command: GetExecutionCommand) -> AlignedExecution:
        _, alignments = self._alignments.get(command.alignments_id)
        return alignments.execution(command.index)
