from dataclasses import dataclass

from ocelescope_module_oc_alignments.application.ports.alignment_repository import AlignmentRepository
from ocelescope_module_oc_alignments.domain.models.alignment_set import AlignmentsOverview


@dataclass(frozen=True, kw_only=True)
class GetAlignmentsCommand:
    alignments_id: str


class GetAlignments:
    """The overview of kept alignments: summary, net and every variant."""

    def __init__(self, *, alignments: AlignmentRepository) -> None:
        self._alignments = alignments

    def execute(self, command: GetAlignmentsCommand) -> AlignmentsOverview:
        name, alignments = self._alignments.get(command.alignments_id)
        return alignments.overview(command.alignments_id, name)
