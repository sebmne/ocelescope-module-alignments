"""Runs, end to end: a log and a net of the session, aligned, kept as a resource, explored."""

from api import Api
from conftest import finished_run
from fixtures import ORDERS, TYPES, ocel, order_process
from ocelescope import PetriNet
from ocelescope_backend.app.internal.session import Session

from ocelescope_module_oc_alignments.infrastructure.alignments_resource import OCAlignmentsResource


def setup(session: Session, weight: int = 1) -> tuple[str, str]:
    ocel_id = session.add_ocel(ocel(ORDERS, TYPES), name="orders")
    net_id = session.add_resource(order_process(weight), name="order process")
    return ocel_id, net_id


def test_a_run_keeps_its_alignments_as_a_resource(api: Api, session: Session) -> None:
    ocel_id, net_id = setup(session)
    assert [(n["name"], n["problem"]) for n in api.list_petri_nets().json()] == [("order process", None)]
    assert api.petri_net_resource_type().json() == PetriNet.get_schema_hash()

    started = api.start_run(ocel_id, net_id, secondsPerVariant=30)
    assert started.status_code == 201, started.text
    run = finished_run(api, started.json()["id"])
    assert run["status"] == "done", run
    assert run["executions"] == 3
    assert sorted((v["frequency"], v["status"], v["deviations"]) for v in run["variants"]) == [
        (1, "aligned", 1),  # pay is missing for o3
        (2, "aligned", 0),
    ]

    # kept as a resource of its own type, shown by the host as a table of variants
    alignments_id = run["alignmentsId"]
    resource = session.load_resource(alignments_id)
    assert isinstance(resource, OCAlignmentsResource)
    assert {row["variant"] for row in resource.visualize().rows} == {"v1", "v2"}

    (summary,) = api.list_alignments().json()
    assert summary["id"] == alignments_id
    # listed per log: the page shows the results of the log selected in Ocelescope
    assert (summary["ocelId"], summary["netId"]) == (ocel_id, net_id)
    assert api.list_alignments(ocelId=ocel_id).json() == [summary]
    assert api.list_alignments(ocelId="another log").json() == []
    assert [r["id"] for r in api.list_runs(ocelId=ocel_id).json()] == [run["id"]]
    assert api.list_runs(ocelId="another log").json() == []
    assert (summary["executions"], summary["variants"], summary["fittingExecutions"], summary["deviations"]) == (
        3,
        2,
        2,
        1,
    )

    overview = api.get_alignments(alignments_id).json()
    assert "net" not in overview  # Ocelescope shows nets itself
    assert overview["objectTypes"] == ["item", "order"]
    first, second = overview["variants"]
    assert (first["id"], first["frequency"], first["objects"]) == ("v1", 2, {"item": 1, "order": 1})
    assert second["activities"] == ["place order", "pick item", "pick item", "ship"]
    # its alignment strip: the representative's moves, pay missing for o3
    assert [(m["kind"], m["activity"] or m["label"]) for m in second["moves"]] == [
        ("sync", "place order"),
        ("sync", "pick item"),
        ("sync", "pick item"),
        ("model", "pay"),
        ("sync", "ship"),
    ]

    detail = api.get_variant(alignments_id, "v2").json()
    assert [x["objects"] for x in detail["executions"]] == [["i3", "i4", "o3"]]
    moves = detail["representative"]["alignment"]["moves"]
    assert [m for m in moves if m["kind"] != "sync"] == [
        {
            "kind": "model",
            "event": None,
            "activity": None,
            "transition": "pay",
            "label": "pay",
            "objects": ["o3"],
            "cost": 1000,
        }  # fmt: skip
    ]

    # the other execution of v1, with its own events and objects
    v1 = api.get_variant(alignments_id, "v1").json()
    other = next(x["index"] for x in v1["executions"] if "o2" in x["objects"])
    execution = api.get_execution(alignments_id, other).json()
    assert execution["variant"] == "v1"
    assert {m["event"] for m in execution["alignment"]["moves"]} == {e["id"] for e in execution["events"]}
    assert {o for m in execution["alignment"]["moves"] for o in m["objects"]} == {"o2", "i2"}


def test_unknown_things_are_404(api: Api, session: Session) -> None:
    ocel_id, net_id = setup(session)
    assert api.start_run("nope", net_id).status_code == 404
    assert api.start_run(ocel_id, "nope").status_code == 404
    assert api.get_run("nope").status_code == 404
    assert api.get_alignments("nope").status_code == 404
    run = finished_run(api, api.start_run(ocel_id, net_id).json()["id"])
    assert api.get_variant(run["alignmentsId"], "v9").status_code == 404
    assert api.get_execution(run["alignmentsId"], 99).status_code == 404


def test_nets_with_heavier_arcs_cannot_be_aligned_with(api: Api, session: Session) -> None:
    ocel_id, net_id = setup(session, weight=2)
    # listed, with the reason it cannot be used
    (listed,) = api.list_petri_nets().json()
    assert listed["id"] == net_id
    assert "weight 2" in listed["problem"]
    response = api.start_run(ocel_id, net_id)
    assert response.status_code == 422
    assert "weight 2" in response.json()["detail"]


def test_cancel_and_delete_a_run(api: Api, session: Session) -> None:
    ocel_id, net_id = setup(session)
    run_id = api.start_run(ocel_id, net_id).json()["id"]
    cancelled = api.cancel_run(run_id).json()
    assert cancelled["status"] in {"cancelled", "done"}
    assert api.delete_run(run_id).status_code == 204
    assert api.get_run(run_id).status_code == 404
    assert api.list_runs().json() == []
