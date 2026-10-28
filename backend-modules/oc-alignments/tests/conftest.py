import shutil
import time
from collections.abc import Iterator
from typing import Any

import pytest
from api import Api
from fastapi.testclient import TestClient
from ocelescope_backend.app.dependencies import get_session
from ocelescope_backend.app.internal.session import Session
from ocelescope_backend.app.modules.loader import build_module

from ocelescope_module_oc_alignments.module import OCAlignments


@pytest.fixture
def session() -> Iterator[Session]:
    """A real Ocelescope session; its logs are DuckDB files in a temporary folder."""
    session = Session()
    yield session
    for ocel_id in list(session.ocels):
        session.delete_ocel(ocel_id)
    Session.sessions.pop(session.id, None)
    shutil.rmtree(session._ocel_dir, ignore_errors=True)  # pyright: ignore[reportPrivateUsage]


@pytest.fixture
def api(session: Session) -> Iterator[Api]:
    """The module's app as the host mounts it, its resources registered, every request in `session`."""
    module = build_module(OCAlignments)
    module.registry.load(OCAlignments.resources)
    app = module.create_app()
    app.dependency_overrides[get_session] = lambda: session
    with TestClient(app) as client:
        yield Api(client)


def finished_run(api: Api, run_id: str, seconds: float = 120) -> dict[str, Any]:
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        run = api.get_run(run_id).json()
        if run["status"] != "running" and (run["status"] != "done" or run["alignmentsId"]):
            return run
        time.sleep(0.2)
    raise AssertionError("the run did not finish")
