from ocelescope_module_oc_alignments.application.ports.alignment_repository import AlignmentRepository
from ocelescope_module_oc_alignments.domain.models.alignment_set import AlignmentSetSummary


class ListAlignments:
    def __init__(self, *, alignments: AlignmentRepository) -> None:
        self._alignments = alignments

    def execute(self, ocel_id: str | None = None) -> tuple[AlignmentSetSummary, ...]:
        """Newest first; only those of the log `ocel_id`, if given."""
        return tuple(a for a in self._alignments.list() if ocel_id is None or a.ocel_id == ocel_id)
