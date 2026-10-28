from dataclasses import dataclass

from ocelescope_module_oc_alignments.application.ports.aligner import Aligner
from ocelescope_module_oc_alignments.application.ports.alignment_repository import AlignmentRepository
from ocelescope_module_oc_alignments.application.ports.event_log_source import EventLogSource
from ocelescope_module_oc_alignments.application.ports.job_registry import JobRegistry
from ocelescope_module_oc_alignments.application.ports.net_source import NetSource
from ocelescope_module_oc_alignments.application.ports.run_notifier import RunNotifier
from ocelescope_module_oc_alignments.application.ports.run_repository import RunRepository
from ocelescope_module_oc_alignments.application.workflows.record_run_progress import RecordRunProgress
from ocelescope_module_oc_alignments.domain.models.run import Run, RunSummary


@dataclass(frozen=True, kw_only=True)
class StartRunCommand:
    net_id: str
    ocel_id: str
    seconds_per_variant: float


class StartRun:
    """Starts aligning every variant of a log with a net, in the background."""

    def __init__(
        self,
        *,
        nets: NetSource,
        logs: EventLogSource,
        aligner: Aligner,
        runs: RunRepository,
        jobs: JobRegistry,
        alignments: AlignmentRepository,
        notifier: RunNotifier,
    ) -> None:
        self._nets = nets
        self._logs = logs
        self._aligner = aligner
        self._runs = runs
        self._jobs = jobs
        self._alignments = alignments
        self._notifier = notifier

    def execute(self, command: StartRunCommand) -> RunSummary:
        name, net = self._nets.get(command.net_id)
        log = self._logs.read(command.ocel_id)
        run = Run.start(
            net_id=command.net_id,
            net_name=name,
            net=net,
            ocel_id=command.ocel_id,
            log=log,
            seconds=command.seconds_per_variant,
        )
        self._runs.add(run)
        progress = RecordRunProgress(
            run_id=run.id, runs=self._runs, jobs=self._jobs, alignments=self._alignments, notifier=self._notifier
        )
        try:
            job = self._aligner.start(net, log, command.seconds_per_variant, progress)
        except Exception:
            self._runs.remove(run.id)
            raise
        self._jobs.keep(run.id, job)
        current = self._runs.get(run.id)
        return (current or run).summary()
