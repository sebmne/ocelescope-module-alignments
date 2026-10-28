class AlignmentError(Exception):
    """Something the user asked for cannot be done. The message says why."""


class InvalidNet(AlignmentError):
    """A net is no object-centric Petri net as the alignments need it."""


class UnknownNet(AlignmentError):
    def __init__(self, net_id: str) -> None:
        super().__init__(f"There is no object-centric Petri net {net_id!r}.")


class UnknownLog(AlignmentError):
    def __init__(self, ocel_id: str) -> None:
        super().__init__(f"There is no event log {ocel_id!r}.")


class UnknownRun(AlignmentError):
    def __init__(self, run_id: str) -> None:
        super().__init__(f"There is no alignment run {run_id!r}.")


class UnknownAlignments(AlignmentError):
    def __init__(self, alignments_id: str) -> None:
        super().__init__(f"There are no alignments {alignments_id!r}.")


class UnknownVariant(AlignmentError):
    def __init__(self, variant_id: str) -> None:
        super().__init__(f"There is no variant {variant_id!r}.")


class UnknownExecution(AlignmentError):
    def __init__(self, execution: int) -> None:
        super().__init__(f"There is no process execution {execution}.")


class SearchAborted(AlignmentError):
    """The search for an optimal alignment ran out of time or states."""


class NoAlignment(AlignmentError):
    """No run of the net reaches the final marking: the net cannot explain the execution."""
