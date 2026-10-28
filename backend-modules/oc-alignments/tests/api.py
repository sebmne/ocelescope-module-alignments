from typing import Any

from fastapi.testclient import TestClient
from httpx import Response


class Api:
    """The module's HTTP operations, by operation id. The paths live here only."""

    def __init__(self, client: TestClient) -> None:
        self._client = client

    def list_petri_nets(self) -> Response:
        return self._client.get("/petri-nets")

    def petri_net_resource_type(self) -> Response:
        return self._client.get("/petri-nets/resource-type")

    def start_run(self, ocel_id: str, petri_net_id: str, **body: Any) -> Response:
        return self._client.post("/runs", json={"ocelId": ocel_id, "petriNetId": petri_net_id, **body})

    def list_runs(self, **params: str) -> Response:
        return self._client.get("/runs", params=params)

    def get_run(self, run_id: str) -> Response:
        return self._client.get(f"/runs/{run_id}")

    def cancel_run(self, run_id: str) -> Response:
        return self._client.post(f"/runs/{run_id}/cancellation")

    def delete_run(self, run_id: str) -> Response:
        return self._client.delete(f"/runs/{run_id}")

    def list_alignments(self, **params: str) -> Response:
        return self._client.get("/alignments", params=params)

    def get_alignments(self, alignments_id: str) -> Response:
        return self._client.get(f"/alignments/{alignments_id}")

    def get_variant(self, alignments_id: str, variant_id: str) -> Response:
        return self._client.get(f"/alignments/{alignments_id}/variants/{variant_id}")

    def get_execution(self, alignments_id: str, index: int) -> Response:
        return self._client.get(f"/alignments/{alignments_id}/executions/{index}")
