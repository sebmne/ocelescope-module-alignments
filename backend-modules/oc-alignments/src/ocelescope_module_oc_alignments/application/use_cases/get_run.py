from dataclasses import dataclass

from ocelescope_module_oc_alignments.application.ports.run_repository import RunRepository
from ocelescope_module_oc_alignments.domain.exceptions import UnknownRun
from ocelescope_module_oc_alignments.domain.models.run import RunSummary


@dataclass(frozen=True, kw_only=True)
class GetRunCommand:
    run_id: str


class GetRun:
    def __init__(self, *, runs: RunRepository) -> None:
        self._runs = runs

    def execute(self, command: GetRunCommand) -> RunSummary:
        run = self._runs.get(command.run_id)
        if run is None:
            raise UnknownRun(command.run_id)
        return run.summary()
