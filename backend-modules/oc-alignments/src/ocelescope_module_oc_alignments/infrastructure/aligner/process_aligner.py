import json
import os
import shutil
import signal
import subprocess
import sys
import tempfile
import threading
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from ocelescope_module_oc_alignments.application.ports.aligner import AlignmentListener
from ocelescope_module_oc_alignments.domain.models.alignment_set import VariantOutcome
from ocelescope_module_oc_alignments.domain.models.log import EventLog, Execution, Variant
from ocelescope_module_oc_alignments.domain.models.net import ObjectCentricNet

_RUNNER = "ocelescope_module_oc_alignments.infrastructure.aligner.runner"


class ProcessAligner:
    """The search (domain/services/search.py), in a process of its own per run (runner.py): it
    can be cancelled, and it does not hold up the server."""

    def start(
        self, net: ObjectCentricNet, log: EventLog, seconds_per_variant: float, listener: AlignmentListener
    ) -> "_ProcessJob":
        workdir = Path(tempfile.mkdtemp(prefix="oc_alignments_"))
        payload = {
            "net": net.model_dump(mode="json", by_alias=True),
            "log": log.model_dump(mode="json", by_alias=True),
            "secondsPerVariant": seconds_per_variant,
        }
        (workdir / "input.json").write_text(json.dumps(payload))
        return _ProcessJob([sys.executable, "-m", _RUNNER, str(workdir / "input.json")], workdir, listener)


class _ProcessJob:
    def __init__(self, command: list[str], workdir: Path, listener: AlignmentListener) -> None:
        self._workdir = workdir
        self._listener = listener
        self._cancelled = threading.Event()
        self._stderr = (workdir / "stderr.log").open("w")
        # its own process group, so that cancelling also stops its worker processes
        self._process = subprocess.Popen(
            command, stdout=subprocess.PIPE, stderr=self._stderr, text=True, cwd=workdir, start_new_session=True
        )
        threading.Thread(target=self._follow, daemon=True).start()

    def cancel(self) -> None:
        self._cancelled.set()
        if self._process.poll() is None:
            try:
                os.killpg(self._process.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass

    def _follow(self) -> None:
        assert self._process.stdout is not None
        for line in self._process.stdout:
            if self._cancelled.is_set():
                break
            try:
                message = json.loads(line)
                self._handle(message)
            except (json.JSONDecodeError, KeyError, ValidationError):
                continue
        returncode = self._process.wait()
        self._stderr.close()
        error = None
        if returncode != 0 and not self._cancelled.is_set():
            error = _failure((self._workdir / "stderr.log").read_text(errors="replace"), returncode)
        shutil.rmtree(self._workdir, ignore_errors=True)
        self._listener.finished(error)

    def _handle(self, message: dict[str, Any]) -> None:
        if message["type"] == "variants":
            self._listener.variants_found(
                tuple(Execution.model_validate(x) for x in message["executions"]),
                tuple(Variant.model_validate(v) for v in message["variants"]),
            )
        elif message["type"] == "result":
            self._listener.variant_aligned(message["variant"], VariantOutcome.model_validate(message["outcome"]))


def _failure(stderr: str, returncode: int) -> str:
    """Why the aligner failed: its last traceback, not the warnings around it."""
    if returncode < 0 and -returncode == signal.SIGKILL:
        return "The aligner was stopped by the system, most likely because it ran out of memory."
    lines = stderr.strip().splitlines()
    start = max((i for i, line in enumerate(lines) if line.startswith("Traceback")), default=None)
    if start is not None:
        lines = lines[start:]
    return "\n".join(lines[-15:]) or f"The aligner exited with code {returncode}."
