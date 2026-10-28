from typing import Annotated

from fastapi import APIRouter, Depends

from ocelescope_module_oc_alignments.api.dependencies import get_get_alignments
from ocelescope_module_oc_alignments.application.use_cases.get_alignments import GetAlignments, GetAlignmentsCommand
from ocelescope_module_oc_alignments.domain.models.alignment_set import AlignmentsOverview

router = APIRouter()


@router.get("/alignments/{alignments_id}", operation_id="getAlignments")
def get_alignments(
    alignments_id: str, use_case: Annotated[GetAlignments, Depends(get_get_alignments)]
) -> AlignmentsOverview:
    """Summary, net and every variant of kept alignments."""
    return use_case.execute(GetAlignmentsCommand(alignments_id=alignments_id))
