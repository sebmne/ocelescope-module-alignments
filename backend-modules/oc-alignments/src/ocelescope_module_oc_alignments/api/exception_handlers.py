from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from ocelescope_module_oc_alignments.domain.exceptions import (
    InvalidNet,
    UnknownAlignments,
    UnknownExecution,
    UnknownLog,
    UnknownNet,
    UnknownRun,
    UnknownVariant,
)

_STATUS: dict[type[Exception], int] = {
    UnknownNet: 404,
    UnknownLog: 404,
    UnknownRun: 404,
    UnknownAlignments: 404,
    UnknownVariant: 404,
    UnknownExecution: 404,
    InvalidNet: 422,
}


def register_exception_handlers(app: FastAPI) -> None:
    """Maps the module's own errors to HTTP statuses."""
    for error_type, status in _STATUS.items():

        def handle(request: Request, error: Exception, status: int = status) -> JSONResponse:
            return JSONResponse(status_code=status, content={"detail": str(error)})

        app.add_exception_handler(error_type, handle)
