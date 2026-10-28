"""Aligns every variant of a log with a net and prints the results as JSON lines.

Runs in a process of its own (see process_aligner.py), so that a run can be cancelled and a long
search does not hold up the server; variants are aligned in parallel worker processes.

    python -m ocelescope_module_oc_alignments.infrastructure.aligner.runner input.json [--workers N]

input.json: {"net": ObjectCentricNet, "log": EventLog, "secondsPerVariant": float}
Output, one JSON object per line:
    {"type": "variants", "executions": [...], "variants": [...]}
    {"type": "result", "variant": "v1", "outcome": VariantOutcome}   (as each finishes)
"""

import argparse
import json
import os
import sys
import time
from collections.abc import Callable
from concurrent.futures import Future, ProcessPoolExecutor, as_completed
from concurrent.futures.process import BrokenProcessPool
from typing import Any, NamedTuple

from ocelescope_module_oc_alignments.domain.exceptions import NoAlignment, SearchAborted
from ocelescope_module_oc_alignments.domain.models.alignment_set import VariantOutcome
from ocelescope_module_oc_alignments.domain.models.log import Event, EventLog
from ocelescope_module_oc_alignments.domain.models.net import ObjectCentricNet
from ocelescope_module_oc_alignments.domain.services.executions import process_executions, variants
from ocelescope_module_oc_alignments.domain.services.search import align

# Bounds on what one search keeps, so that one variant cannot exhaust the memory: the states, and
# the tokens their markings hold (shared between markings, ~10 bytes each: ~0.5 GB per worker).
MAX_STATES = 2_000_000
MAX_TOKENS = 50_000_000

KILLED = (
    "The search process was stopped by the system, most likely because it ran out of memory: "
    "the execution is too large."
)


class Job(NamedTuple):
    """One variant to align: the arguments of the work for it."""

    variant: str
    args: tuple


def _emit(payload: dict[str, Any]) -> None:
    sys.stdout.write(json.dumps(payload) + "\n")
    sys.stdout.flush()


def align_variant(events: list[dict], object_types: dict[str, str], net: dict, seconds: float) -> dict:
    """In a worker: the outcome of aligning one variant's representative, as JSON."""
    started = time.perf_counter()
    try:
        alignment = align(
            [Event.model_validate(e) for e in events],
            object_types,
            ObjectCentricNet.model_validate(net),
            seconds=seconds,
            max_states=MAX_STATES,
            max_tokens=MAX_TOKENS,
        )
        outcome = VariantOutcome(status="aligned", alignment=alignment)
    except SearchAborted as error:
        outcome = VariantOutcome(status="timeout", error=str(error))
    except NoAlignment as error:
        outcome = VariantOutcome(status="no_alignment", error=str(error))
    except Exception as error:  # report and go on with the other variants
        outcome = VariantOutcome(status="failed", error=f"{type(error).__name__}: {error}")
    outcome = outcome.model_copy(update={"seconds": round(time.perf_counter() - started, 3)})
    return outcome.model_dump(mode="json", by_alias=True)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Aligns every variant of a log with a net.")
    parser.add_argument("input")
    parser.add_argument("--workers", type=int, default=max(1, min(4, (os.cpu_count() or 2) - 1)))
    args = parser.parse_args(argv)

    with open(args.input) as file:
        data = json.load(file)
    net = ObjectCentricNet.model_validate(data["net"])
    log = EventLog.model_validate(data["log"])
    seconds = float(data["secondsPerVariant"])

    executions = process_executions(log)
    found = variants(log, executions)
    _emit(
        {
            "type": "variants",
            "executions": [x.model_dump(mode="json", by_alias=True) for x in executions],
            "variants": [v.model_dump(mode="json", by_alias=True) for v in found],
        }
    )

    events = {e.id: e for e in log.events}
    net_json = net.model_dump(mode="json", by_alias=True)
    # smallest first, so that results come early
    ordered = sorted(found, key=lambda v: len(executions[v.representative].events))
    jobs = []
    for variant in ordered:
        execution = executions[variant.representative]
        payload = [events[e].model_dump(mode="json", by_alias=True) for e in execution.events]
        types = {o: log.object_types[o] for o in execution.objects}
        jobs.append(Job(variant.id, (payload, types, net_json, seconds)))

    align_all(jobs, args.workers)


def align_all(jobs: list[Job], workers: int, work: Callable[..., dict] = align_variant) -> None:
    """Aligns every variant, emitting each result. A worker that dies (the system stops it, e.g.
    when memory runs out) breaks its whole pool: the variants lost with it are tried again, each in
    a pool of its own, so that only the culprit fails."""
    for job in _align(jobs, workers, work):
        if _align([job], 1, work):
            outcome = VariantOutcome(status="failed", error=KILLED)
            _emit({"type": "result", "variant": job.variant, "outcome": outcome.model_dump(mode="json", by_alias=True)})


def _align(jobs: list[Job], workers: int, work: Callable[..., dict] = align_variant) -> list[Job]:
    """Aligns the variants in a pool of workers, emitting each result; returns those lost when a
    worker died."""
    lost = []
    with ProcessPoolExecutor(max_workers=workers) as pool:
        futures: dict[Future, Job] = {pool.submit(work, *job.args): job for job in jobs}
        for future in as_completed(futures):
            job = futures[future]
            try:
                outcome = future.result()
            except BrokenProcessPool:
                lost.append(job)
                continue
            _emit({"type": "result", "variant": job.variant, "outcome": outcome})
    return lost


if __name__ == "__main__":
    main()
