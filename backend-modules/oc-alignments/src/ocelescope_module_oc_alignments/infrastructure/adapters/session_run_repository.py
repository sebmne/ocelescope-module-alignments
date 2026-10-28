from collections.abc import Callable
from threading import Lock

from ocelescope_backend.app.internal.session import Session

from ocelescope_module_oc_alignments.domain.models.run import Run

_STATE_KEY = "ocAlignments:runs"


class _Runs(dict[str, Run]):
    def __init__(self) -> None:
        super().__init__()
        self.lock = Lock()


class SessionRunRepository:
    """Runs kept in memory with the user's Ocelescope session, gone when it ends."""

    def __init__(self, session: Session) -> None:
        self._runs = session.get_module_state(_STATE_KEY, _Runs)

    def add(self, run: Run) -> None:
        with self._runs.lock:
            self._runs[run.id] = run

    def get(self, run_id: str) -> Run | None:
        with self._runs.lock:
            return self._runs.get(run_id)

    def list(self) -> tuple[Run, ...]:
        with self._runs.lock:
            return tuple(sorted(self._runs.values(), key=lambda run: run.created_at, reverse=True))

    def change(self, run_id: str, change: Callable[[Run], Run]) -> Run | None:
        with self._runs.lock:
            run = self._runs.get(run_id)
            if run is None:
                return None
            self._runs[run_id] = changed = change(run)
            return changed

    def remove(self, run_id: str) -> None:
        with self._runs.lock:
            self._runs.pop(run_id, None)
