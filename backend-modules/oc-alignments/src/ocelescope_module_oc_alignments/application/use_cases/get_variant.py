from dataclasses import dataclass

from ocelescope_module_oc_alignments.application.ports.alignment_repository import AlignmentRepository
from ocelescope_module_oc_alignments.domain.models.alignment_set import VariantDetail


@dataclass(frozen=True, kw_only=True)
class GetVariantCommand:
    alignments_id: str
    variant_id: str


class GetVariant:
    """A variant: its executions and the alignment of its representative."""

    def __init__(self, *, alignments: AlignmentRepository) -> None:
        self._alignments = alignments

    def execute(self, command: GetVariantCommand) -> VariantDetail:
        _, alignments = self._alignments.get(command.alignments_id)
        return alignments.variant_detail(command.variant_id)
