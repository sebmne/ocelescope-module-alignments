from typing import Annotated

from fastapi import APIRouter, Depends

from ocelescope_module_oc_alignments.api.dependencies import get_get_variant
from ocelescope_module_oc_alignments.application.use_cases.get_variant import GetVariant, GetVariantCommand
from ocelescope_module_oc_alignments.domain.models.alignment_set import VariantDetail

router = APIRouter()


@router.get("/alignments/{alignments_id}/variants/{variant_id}", operation_id="getVariant")
def get_variant(
    alignments_id: str, variant_id: str, use_case: Annotated[GetVariant, Depends(get_get_variant)]
) -> VariantDetail:
    """A variant: its executions and the alignment of its representative."""
    return use_case.execute(GetVariantCommand(alignments_id=alignments_id, variant_id=variant_id))
