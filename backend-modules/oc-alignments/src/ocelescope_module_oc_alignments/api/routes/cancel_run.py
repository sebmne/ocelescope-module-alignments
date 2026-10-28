from typing import Annotated

from fastapi import APIRouter, Depends

from ocelescope_module_oc_alignments.api.dependencies import get_cancel_run
from ocelescope_module_oc_alignments.application.use_cases.cancel_run import CancelRun, CancelRunCommand
from ocelescope_module_oc_alignments.domain.models.run import RunSummary

router = APIRouter()


@router.post("/runs/{run_id}/cancellation", operation_id="cancelRun")
def cancel_run(run_id: str, use_case: Annotated[CancelRun, Depends(get_cancel_run)]) -> RunSummary:
    return use_case.execute(CancelRunCommand(run_id=run_id))
