"""Our alignments cost what the reference implementation of Liss et al. computes, on its own
example logs and nets: hand-made ones (the paper's example among them) and nets ocpa discovers.

Skipped unless the reference is set up (`uv run python scripts/reference.py`). Its results are
cached in vendor/, as computing them takes a minute or two.
"""

import hashlib
import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

import pytest

from ocelescope_module_oc_alignments.domain.models.alignment import UNIT
from ocelescope_module_oc_alignments.domain.models.log import Event, EventLog
from ocelescope_module_oc_alignments.domain.models.net import ObjectCentricNet
from ocelescope_module_oc_alignments.domain.services.executions import process_executions
from ocelescope_module_oc_alignments.domain.services.search import align

MODULE = Path(__file__).resolve().parents[2]
VENDOR = MODULE / "vendor"
CHECKOUT = VENDOR / "liss"
PYTHON = VENDOR / "liss-venv" / "bin" / "python"
SCRIPT = Path(__file__).with_name("liss_alignments.py")

AVAILABLE = CHECKOUT.exists() and PYTHON.exists()
pytestmark = pytest.mark.skipif(not AVAILABLE, reason="the reference is not set up: uv run python scripts/reference.py")


def reference_results() -> list[dict[str, Any]]:
    commit = subprocess.run(
        ["git", "-C", str(CHECKOUT), "rev-parse", "HEAD"], capture_output=True, text=True, check=True
    ).stdout.strip()
    key = hashlib.sha256(commit.encode() + SCRIPT.read_bytes()).hexdigest()[:16]
    cache = VENDOR / f"liss-results-{key}.json"
    if not cache.exists():
        out = subprocess.run(
            [str(PYTHON), str(SCRIPT)], cwd=CHECKOUT, capture_output=True, text=True, check=True
        ).stdout
        cache.write_text(out)
    return json.loads(cache.read_text())


def read_jsonocel(path: Path) -> EventLog:
    """An OCEL 1.0 JSON log, as the reference reads it."""
    data = json.loads(path.read_text())
    events = [
        Event(
            id=str(event_id),
            activity=event["ocel:activity"],
            timestamp=datetime.fromisoformat(event["ocel:timestamp"]),
            objects=tuple(sorted(event["ocel:omap"])),
        )
        for event_id, event in data["ocel:events"].items()
    ]
    events.sort(key=lambda e: (e.timestamp, e.id))
    types = {oid: obj["ocel:type"] for oid, obj in data["ocel:objects"].items()}
    return EventLog(name=path.stem, events=tuple(events), object_types=types)


CASES = reference_results() if AVAILABLE else []


@pytest.mark.parametrize("case", CASES, ids=[c["name"] for c in CASES])
def test_costs_equal_the_reference(case: dict[str, Any]) -> None:
    log = read_jsonocel(CHECKOUT / case["log"])
    net = ObjectCentricNet.model_validate(case["net"])
    events = {e.id: e for e in log.events}
    executions = {frozenset(x.objects): x for x in process_executions(log)}
    for variant in case["variants"]:
        execution = executions[frozenset(variant["objects"])]
        alignment = align([events[e] for e in execution.events], log.object_types, net, seconds=120)
        assert alignment.cost / UNIT == pytest.approx(variant["cost"]), (variant["objects"], alignment.moves)
