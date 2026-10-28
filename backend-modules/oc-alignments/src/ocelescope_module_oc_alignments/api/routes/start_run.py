from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import Field

from ocelescope_module_oc_alignments.api.dependencies import get_start_run
from ocelescope_module_oc_alignments.api.schema import ApiModel
from ocelescope_module_oc_alignments.application.use_cases.start_run import StartRun, StartRunCommand
from ocelescope_module_oc_alignments.domain.models.run import RunSummary

router = APIRouter()


class StartRunRequest(ApiModel):
    ocel_id: str
    petri_net_id: str
    seconds_per_variant: float = Field(default=60, gt=0, le=24 * 3600)


@router.post(
    "/runs",
    operation_id="startRun",
    status_code=201,
    responses={404: {"description": "No such log or net."}, 422: {"description": "The net cannot be aligned with."}},
)
def start_run(request: StartRunRequest, use_case: Annotated[StartRun, Depends(get_start_run)]) -> RunSummary:
    """Starts aligning every variant of the log with the net, in the background. When done, the
    alignments are kept as a resource (`alignmentsId`)."""
    return use_case.execute(
        StartRunCommand(
            net_id=request.petri_net_id, ocel_id=request.ocel_id, seconds_per_variant=request.seconds_per_variant
        )
    )
