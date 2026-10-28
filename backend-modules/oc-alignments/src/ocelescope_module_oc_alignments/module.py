from fastapi import FastAPI
from ocelescope_backend.app.modules import Module, ModuleMeta
from packaging.version import Version

from ocelescope_module_oc_alignments.api.exception_handlers import register_exception_handlers
from ocelescope_module_oc_alignments.api.router import router
from ocelescope_module_oc_alignments.infrastructure.alignments_resource import OCAlignmentsResource


class OCAlignments(Module):
    """Object-centric alignments after Liss, Adams, van der Aalst (ER 2023): computed per variant
    of a log against an object-centric Petri net, explored, and kept as a resource."""

    meta = ModuleMeta(key="ocAlignments", version=Version("1.0"))
    resources = [OCAlignmentsResource]

    def create_app(self) -> FastAPI:
        app = FastAPI(title="OC Alignments", version=str(self.meta.version))
        register_exception_handlers(app)
        app.include_router(router)
        return app
