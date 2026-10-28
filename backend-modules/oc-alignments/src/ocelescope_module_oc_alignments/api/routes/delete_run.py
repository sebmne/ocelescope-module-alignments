from typing import Annotated

from fastapi import APIRouter, Depends, Response

from ocelescope_module_oc_alignments.api.dependencies import get_delete_run
from ocelescope_module_oc_alignments.application.use_cases.delete_run import DeleteRun, DeleteRunCommand

router = APIRouter()


@router.delete("/runs/{run_id}", operation_id="deleteRun", status_code=204)
def delete_run(run_id: str, use_case: Annotated[DeleteRun, Depends(get_delete_run)]) -> Response:
    """Forgets the run (and stops it). Alignments it kept stay."""
    use_case.execute(DeleteRunCommand(run_id=run_id))
    return Response(status_code=204)
