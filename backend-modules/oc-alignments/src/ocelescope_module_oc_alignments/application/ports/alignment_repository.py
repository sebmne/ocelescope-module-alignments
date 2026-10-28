from typing import Protocol

from ocelescope_module_oc_alignments.domain.models.alignment_set import AlignmentSet, AlignmentSetSummary


class AlignmentRepository(Protocol):
    """Alignments kept for good (as resources of the user's session)."""

    def add(self, alignments: AlignmentSet, name: str) -> AlignmentSetSummary: ...

    def get(self, alignments_id: str) -> tuple[str, AlignmentSet]:
        """The name and the alignments; raises UnknownAlignments if there are none."""
        ...

    def list(self) -> tuple[AlignmentSetSummary, ...]: ...
