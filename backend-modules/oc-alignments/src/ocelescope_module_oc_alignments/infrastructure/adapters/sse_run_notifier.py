from ocelescope_backend.app.sse_manager import SystemNotification, sse_manager

from ocelescope_module_oc_alignments.domain.models.run import RunSummary


class SseRunNotifier:
    """A notification in Ocelescope, sent over the session's server-sent events."""

    def __init__(self, session_id: str) -> None:
        self._session_id = session_id

    def run_ended(self, run: RunSummary) -> None:
        aligned = sum(variant.status == "aligned" for variant in run.variants)
        sse_manager.send_safe(
            self._session_id,
            SystemNotification(
                title=f"{run.net_name} · {run.ocel_name}",
                message=f"{aligned}/{len(run.variants)} variants aligned",
                notification_type="info" if run.status == "done" else "error",
            ),
        )
