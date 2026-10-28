from ocelescope_module_oc_alignments.application.ports.alignment_repository import AlignmentRepository
from ocelescope_module_oc_alignments.application.ports.job_registry import JobRegistry
from ocelescope_module_oc_alignments.application.ports.run_notifier import RunNotifier
from ocelescope_module_oc_alignments.application.ports.run_repository import RunRepository
from ocelescope_module_oc_alignments.domain.models.alignment_set import VariantOutcome
from ocelescope_module_oc_alignments.domain.models.log import Execution, Variant


class RecordRunProgress:
    """Keeps a run up to date while its job reports; when it is done, keeps its alignments and
    tells the user."""

    def __init__(
        self,
        *,
        run_id: str,
        runs: RunRepository,
        jobs: JobRegistry,
        alignments: AlignmentRepository,
        notifier: RunNotifier,
    ) -> None:
        self._run_id = run_id
        self._runs = runs
        self._jobs = jobs
        self._alignments = alignments
        self._notifier = notifier

    def variants_found(self, executions: tuple[Execution, ...], variants: tuple[Variant, ...]) -> None:
        self._runs.change(self._run_id, lambda run: run.with_variants(executions, variants))

    def variant_aligned(self, variant_id: str, outcome: VariantOutcome) -> None:
        self._runs.change(self._run_id, lambda run: run.with_outcome(variant_id, outcome))

    def finished(self, error: str | None) -> None:
        self._jobs.take(self._run_id)
        run = self._runs.change(self._run_id, lambda run: run.finished(error))
        if run is None or run.status == "cancelled":
            return
        if run.status == "done":
            kept = self._alignments.add(run.alignment_set(), f"{run.net_name} · {run.log.name}")
            run = self._runs.change(self._run_id, lambda run: run.saved(kept.id)) or run
        self._notifier.run_ended(run.summary())
