"""Runs the reference implementation of Liss et al. and prints its results as JSON.

Runs in the reference's own environment (see scripts/reference.py), with its checkout as the
working directory:

    vendor/liss-venv/bin/python tests/reference/liss_alignments.py   (cwd: vendor/liss)

For every case: the log file, the net (as places, transitions and arcs), and per variant the
objects of the execution it aligned (executions do not share objects) and its cost.
"""

import contextlib
import json
import os
import sys
import warnings

warnings.filterwarnings("ignore")
sys.path.insert(0, os.getcwd())

from algorithm import calculate_oc_alignments  # noqa: E402
from localocpa.algo.discovery.ocpn import algorithm as ocpn_discovery  # noqa: E402
from localocpa.objects.log.importer.ocel import factory as ocel_import  # noqa: E402
from test_ocpns import TestOCPNS  # noqa: E402

LOGS = "sample-logs/jsonocel"


def discovered(log_file: str):
    return ocpn_discovery.apply(ocel_import.apply(log_file), parameters={"debug": False})


def cases():
    nets = TestOCPNS()
    for name in [
        "paper_example",
        "running_example",
        "silent_transitions",
        "nue_net_required",
        "inter_object_dependencies",
        "seperate_object_instances",
    ]:
        net, log_file = getattr(nets, name)()
        yield name, net, log_file
    yield "paper_example_discovered", discovered(f"{LOGS}/paper-example.jsonocel"), f"{LOGS}/paper-example.jsonocel"
    p2p = discovered(f"{LOGS}/p2p-normal.jsonocel")
    for log in [
        "p2p-normal-01-variant",
        "p2p-01-variant-cost-00",
        "p2p-01-variant-cost-03",
        "p2p-01-variant-cost-07",
        "p2p-01-variant-cost-08",
        "p2p-01-variant-cost-15",
        "p2p-01-variant-log-and-model-move",
    ]:
        yield f"p2p_discovered/{log}", p2p, f"{LOGS}/{log}.jsonocel"


def net_json(net) -> dict:
    return {
        "places": [
            {"id": p.name, "objectType": p.object_type, "initial": bool(p.initial), "final": bool(p.final)}
            for p in net.places
        ],
        "transitions": [{"id": t.name, "label": None if t.silent else t.name} for t in net.transitions],
        "arcs": [{"source": a.source.name, "target": a.target.name, "variable": bool(a.variable)} for a in net.arcs],
    }


def main() -> None:
    results = []
    out = sys.stdout
    with contextlib.redirect_stdout(sys.stderr):  # the reference prints as it goes
        for name, net, log_file in cases():
            results.append(case(name, net, log_file))
    json.dump(results, out)


def case(name: str, net, log_file: str) -> dict:
    exported = net_json(net)  # before the alignment preprocesses (a copy of) the net
    log = ocel_import.apply(log_file)
    alignments = calculate_oc_alignments(log, net)
    return {
        "name": name,
        "log": log_file,
        "net": exported,
        "variants": [
            {
                "objects": sorted(obj for _, obj in alignment.object_types),
                "frequency": len(log.variants_dict[variant]),
                "cost": alignment.get_cost(),
            }
            for variant, alignment in alignments.items()
        ],
    }


if __name__ == "__main__":
    main()
