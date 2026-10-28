from collections.abc import Callable
from typing import Protocol

from ocelescope_module_oc_alignments.domain.models.run import Run


class RunRepository(Protocol):
    """The user's alignment runs. Changes are atomic: jobs report from their own threads."""

    def add(self, run: Run) -> None: ...

    def get(self, run_id: str) -> Run | None: ...

    def list(self) -> tuple[Run, ...]:
        """Newest first."""
        ...

    def change(self, run_id: str, change: Callable[[Run], Run]) -> Run | None:
        """Replaces the run by change(run); None if there is no such run."""
        ...

    def remove(self, run_id: str) -> None: ...
