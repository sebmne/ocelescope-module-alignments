"""The runner: a worker that dies takes only its own variant down."""

import json
import os

import pytest

from ocelescope_module_oc_alignments.infrastructure.aligner.runner import Job, align_all


def work(variant: str) -> dict:
    if variant == "dies":
        os._exit(1)  # as when the system stops a worker that runs out of memory
    return {"status": "aligned"}


def test_a_dying_worker_fails_only_its_own_variant(capsys: pytest.CaptureFixture[str]) -> None:
    align_all([Job(v, (v,)) for v in ("a", "dies", "b", "c")], workers=2, work=work)

    results = [json.loads(line) for line in capsys.readouterr().out.splitlines()]
    outcomes = {r["variant"]: r["outcome"] for r in results}
    assert len(results) == 4
    assert outcomes["dies"]["status"] == "failed"
    assert "ran out of memory" in outcomes["dies"]["error"]
    assert [outcomes[v]["status"] for v in ("a", "b", "c")] == ["aligned"] * 3
