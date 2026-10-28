from ocelescope_module_oc_alignments.application.ports.run_repository import RunRepository
from ocelescope_module_oc_alignments.domain.models.run import RunSummary


class ListRuns:
    def __init__(self, *, runs: RunRepository) -> None:
        self._runs = runs

    def execute(self, ocel_id: str | None = None) -> tuple[RunSummary, ...]:
        """Newest first; only those of the log `ocel_id`, if given."""
        return tuple(run.summary() for run in self._runs.list() if ocel_id is None or run.ocel_id == ocel_id)
