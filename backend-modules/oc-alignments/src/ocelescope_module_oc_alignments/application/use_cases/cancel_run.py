from dataclasses import dataclass

from ocelescope_module_oc_alignments.application.ports.job_registry import JobRegistry
from ocelescope_module_oc_alignments.application.ports.run_repository import RunRepository
from ocelescope_module_oc_alignments.domain.exceptions import UnknownRun
from ocelescope_module_oc_alignments.domain.models.run import RunSummary


@dataclass(frozen=True, kw_only=True)
class CancelRunCommand:
    run_id: str


class CancelRun:
    def __init__(self, *, runs: RunRepository, jobs: JobRegistry) -> None:
        self._runs = runs
        self._jobs = jobs

    def execute(self, command: CancelRunCommand) -> RunSummary:
        run = self._runs.change(command.run_id, lambda run: run.cancelled())
        if run is None:
            raise UnknownRun(command.run_id)
        job = self._jobs.take(command.run_id)
        if job is not None:
            job.cancel()
        return run.summary()
