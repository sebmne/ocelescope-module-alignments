from typing import Annotated

from fastapi import APIRouter, Depends, Query

from ocelescope_module_oc_alignments.api.dependencies import get_list_runs
from ocelescope_module_oc_alignments.application.use_cases.list_runs import ListRuns
from ocelescope_module_oc_alignments.domain.models.run import RunSummary

router = APIRouter()


@router.get("/runs", operation_id="listRuns")
def list_runs(
    use_case: Annotated[ListRuns, Depends(get_list_runs)],
    ocel_id: Annotated[str | None, Query(alias="ocelId")] = None,
) -> tuple[RunSummary, ...]:
    """The session's runs, newest first; `ocelId`: only those of a log."""
    return use_case.execute(ocel_id)
