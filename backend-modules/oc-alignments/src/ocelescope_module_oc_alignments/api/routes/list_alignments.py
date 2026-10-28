from typing import Annotated

from fastapi import APIRouter, Depends, Query

from ocelescope_module_oc_alignments.api.dependencies import get_list_alignments
from ocelescope_module_oc_alignments.application.use_cases.list_alignments import ListAlignments
from ocelescope_module_oc_alignments.domain.models.alignment_set import AlignmentSetSummary

router = APIRouter()


@router.get("/alignments", operation_id="listAlignments")
def list_alignments(
    use_case: Annotated[ListAlignments, Depends(get_list_alignments)],
    ocel_id: Annotated[str | None, Query(alias="ocelId")] = None,
) -> tuple[AlignmentSetSummary, ...]:
    """The alignments among the session's resources, newest first; `ocelId`: only those of a log."""
    return use_case.execute(ocel_id)
