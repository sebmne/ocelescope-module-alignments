from typing import Annotated

from fastapi import APIRouter, Depends

from ocelescope_module_oc_alignments.api.dependencies import get_list_nets
from ocelescope_module_oc_alignments.application.use_cases.list_nets import ListNets
from ocelescope_module_oc_alignments.domain.models.net import NetSummary

router = APIRouter()


@router.get("/petri-nets", operation_id="listPetriNets")
def list_nets(use_case: Annotated[ListNets, Depends(get_list_nets)]) -> tuple[NetSummary, ...]:
    """The object-centric Petri nets among the session's resources; `problem` says why one cannot be
    aligned with."""
    return use_case.execute()


@router.get("/petri-nets/resource-type", operation_id="petriNetResourceType")
def petri_net_resource_type(use_case: Annotated[ListNets, Depends(get_list_nets)]) -> str:
    """The resource type the nets are stored as (a schema hash), to pick them with Ocelescope's
    resource picker."""
    return use_case.resource_type()
