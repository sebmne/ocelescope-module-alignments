from typing import Annotated

from fastapi import APIRouter, Depends

from ocelescope_module_oc_alignments.api.dependencies import get_get_execution
from ocelescope_module_oc_alignments.application.use_cases.get_execution import GetExecution, GetExecutionCommand
from ocelescope_module_oc_alignments.domain.models.alignment_set import AlignedExecution

router = APIRouter()


@router.get("/alignments/{alignments_id}/executions/{index}", operation_id="getExecution")
def get_execution(
    alignments_id: str, index: int, use_case: Annotated[GetExecution, Depends(get_get_execution)]
) -> AlignedExecution:
    """A process execution with its own events and its alignment."""
    return use_case.execute(GetExecutionCommand(alignments_id=alignments_id, index=index))
