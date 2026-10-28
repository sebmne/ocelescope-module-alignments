from threading import Lock

from ocelescope_backend.app.internal.session import Session

from ocelescope_module_oc_alignments.application.ports.aligner import AlignmentJob

_STATE_KEY = "ocAlignments:jobs"


class _Jobs(dict[str, AlignmentJob]):
    def __init__(self) -> None:
        super().__init__()
        self.lock = Lock()


class SessionJobRegistry:
    """The jobs of the session's running runs."""

    def __init__(self, session: Session) -> None:
        self._jobs = session.get_module_state(_STATE_KEY, _Jobs)

    def keep(self, run_id: str, job: AlignmentJob) -> None:
        with self._jobs.lock:
            self._jobs[run_id] = job

    def take(self, run_id: str) -> AlignmentJob | None:
        with self._jobs.lock:
            return self._jobs.pop(run_id, None)
