from fastapi import APIRouter

from ocelescope_module_oc_alignments.api.routes import (
    cancel_run,
    delete_run,
    get_alignments,
    get_execution,
    get_run,
    get_variant,
    list_alignments,
    list_nets,
    list_runs,
    start_run,
)

router = APIRouter(tags=["OC alignments"])

for resource in (
    list_nets,
    start_run,
    list_runs,
    get_run,
    cancel_run,
    delete_run,
    list_alignments,
    get_alignments,
    get_variant,
    get_execution,
):
    router.include_router(resource.router)
