from dataclasses import dataclass

from ocelescope_module_oc_alignments.application.ports.job_registry import JobRegistry
from ocelescope_module_oc_alignments.application.ports.run_repository import RunRepository
from ocelescope_module_oc_alignments.domain.exceptions import UnknownRun


@dataclass(frozen=True, kw_only=True)
class DeleteRunCommand:
    run_id: str


class DeleteRun:
    """Forgets a run, cancelling it first if it still runs. Its alignments, once kept, stay."""

    def __init__(self, *, runs: RunRepository, jobs: JobRegistry) -> None:
        self._runs = runs
        self._jobs = jobs

    def execute(self, command: DeleteRunCommand) -> None:
        if self._runs.get(command.run_id) is None:
            raise UnknownRun(command.run_id)
        job = self._jobs.take(command.run_id)
        if job is not None:
            job.cancel()
        self._runs.remove(command.run_id)
