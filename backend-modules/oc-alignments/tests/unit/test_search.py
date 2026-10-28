"""The search, move by move, on small nets."""

import pytest
from nets import log, net, order_process

from ocelescope_module_oc_alignments.domain.exceptions import NoAlignment, SearchAborted
from ocelescope_module_oc_alignments.domain.models.alignment import EPSILON, UNIT, Alignment
from ocelescope_module_oc_alignments.domain.models.log import EventLog
from ocelescope_module_oc_alignments.domain.models.net import ObjectCentricNet
from ocelescope_module_oc_alignments.domain.services.search import align

TYPES = {"o1": "order", "o2": "order", "i1": "item", "i2": "item", "i3": "item"}


def aligned(the_log: EventLog, the_net: ObjectCentricNet, **limits) -> Alignment:
    return align(the_log.events, the_log.object_types, the_net, **limits)


def kinds(alignment: Alignment) -> list[tuple[str, str | None, tuple[str, ...]]]:
    return [(m.kind, m.activity or m.label, m.objects) for m in alignment.moves]


FITTING = [
    ("place order", ["o1", "i1", "i2"]),
    ("pick item", ["i1"]),
    ("pay", ["o1"]),
    ("pick item", ["i2"]),
    ("ship", ["o1", "i1", "i2"]),
]


def test_a_fitting_execution_is_all_synchronous_moves() -> None:
    alignment = aligned(log(FITTING, TYPES), order_process())
    assert alignment.cost == 0
    assert [kind for kind, _, _ in kinds(alignment)] == ["sync"] * 5
    # every event once, in an order that respects each object's events
    assert sorted(m.event for m in alignment.moves if m.event) == ["e1", "e2", "e3", "e4", "e5"]


def test_an_event_the_net_does_not_know_is_a_log_move() -> None:
    events = [*FITTING[:2], ("call customer", ["o1", "i1"]), *FITTING[2:]]
    alignment = aligned(log(events, TYPES), order_process())
    assert alignment.deviations == 2  # two objects
    assert [k for k in kinds(alignment) if k[0] != "sync"] == [("log", "call customer", ("i1", "o1"))]


def test_a_missing_event_is_a_model_move() -> None:
    events = [e for e in FITTING if e[0] != "pay"]
    alignment = aligned(log(events, TYPES), order_process())
    assert alignment.deviations == 1
    assert [k for k in kinds(alignment) if k[0] != "sync"] == [("model", "pay", ("o1",))]


def test_a_variable_arc_moves_any_number_of_objects() -> None:
    # with normal arcs, place order takes one item: the second item can never reach the end
    with pytest.raises(NoAlignment):
        aligned(log(FITTING, TYPES), order_process(variable_items=False))
    one_item = [("place order", ["o1", "i1"]), ("pick item", ["i1"]), ("pay", ["o1"]), ("ship", ["o1", "i1"])]
    assert aligned(log(one_item, TYPES), order_process(variable_items=False)).cost == 0


def test_objects_must_be_in_all_input_places_of_their_type() -> None:
    """ship takes the order from o2 and the items from i2: an unpicked item cannot ship, so a
    shipment of an unpicked item is a deviation even though the activity order fits."""
    events = [e for e in FITTING if e != ("pick item", ["i2"])]
    alignment = aligned(log(events, TYPES), order_process())
    # pick item for i2 is missing: a model move (1 object)
    assert alignment.deviations == 1
    assert ("model", "pick item", ("i2",)) in kinds(alignment)


def test_silent_moves_cost_epsilon() -> None:
    silent = net(
        places={"p0": "order", "p1": "order", "p2": "order", "p3": "order"},
        transitions={"a": "create", "tau": None, "b": "ship"},
        arcs=[("p0", "a"), ("a", "p1"), ("p1", "tau"), ("tau", "p2"), ("p2", "b"), ("b", "p3")],
        initial={"p0"},
        final={"p3"},
    )
    alignment = aligned(log([("create", ["o1"]), ("ship", ["o1"])], TYPES), silent)
    assert (alignment.cost, alignment.deviations) == (EPSILON, 0)
    assert kinds(alignment)[1] == ("model", None, ("o1",))


def test_every_final_place_must_hold_all_objects_of_its_type() -> None:
    """As Liss et al. read a final marking: two orders both have to end in the final place."""
    two = log([("place order", ["o1", "i1"]), ("place order", ["o2", "i2"])], TYPES)
    alignment = aligned(two, order_process())
    # each order still has to be paid and shipped, its item picked: model moves
    assert alignment.deviations == 2 * (1 + 1 + 2)


def test_the_search_stops_at_its_limits() -> None:
    with pytest.raises(SearchAborted):
        aligned(log(FITTING, TYPES), order_process(), max_states=3)
    ticks = iter(range(10_000))
    with pytest.raises(SearchAborted):
        aligned(log(FITTING * 2, TYPES), order_process(), seconds=0.5, clock=lambda: next(ticks))
    with pytest.raises(SearchAborted, match="too large"):
        aligned(log(FITTING, TYPES), order_process(), max_tokens=10)


def test_a_variable_arc_with_many_objects_stops_at_the_time_limit() -> None:
    """A variable arc binds any of the 2^60 subsets of 60 items: the search has to check its time
    limit while it enumerates them, not only between steps."""
    items = [f"i{n}" for n in range(60)]
    many = log([("pay", ["o1"]), ("ship", ["o1", *items])], {"o1": "order"} | dict.fromkeys(items, "item"))
    ticks = iter(range(100_000))
    with pytest.raises(SearchAborted, match="longer than"):
        aligned(many, order_process(), seconds=1_000, clock=lambda: next(ticks))


def test_costs_are_counted_in_thousandths_of_an_object() -> None:
    assert UNIT == 1000


def test_objects_of_a_type_the_net_does_not_know_are_log_moves() -> None:
    """An invoice the net has no places for: its own events, and events it takes part in, cannot
    be synchronous; the rest of the execution still aligns."""
    types = TYPES | {"x1": "invoice"}
    events = [*FITTING[:2], ("pay", ["o1", "x1"]), ("send invoice", ["x1"]), *FITTING[3:]]
    alignment = aligned(log(events, types), order_process())
    deviations = sorted(k for k in kinds(alignment) if k[0] != "sync")
    assert deviations == [
        ("log", "pay", ("o1", "x1")),
        ("log", "send invoice", ("x1",)),
        ("model", "pay", ("o1",)),
    ]
    assert alignment.deviations == 2 + 1 + 1


def fig1a() -> ObjectCentricNet:
    """Fig. 1(a) of Gianola, Montali, Winkler (CAiSE 2024): the order process as an object-centric
    Petri net; place order and ship take any number of products."""
    return net(
        places={"o0": "order", "o1": "order", "o2": "order", "o3": "order",
                "p0": "product", "p1": "product", "p2": "product", "p3": "product"},
        transitions={"place": "place order", "pay": "payment", "pick": "pick item", "ship": "ship"},
        arcs=[
            ("o0", "place"), ("place", "o1"), ("o1", "pay"), ("pay", "o2"), ("o2", "ship"), ("ship", "o3"),
            ("p0", "place", "var"), ("place", "p1", "var"), ("p1", "pick"), ("pick", "p2"),
            ("p2", "ship", "var"), ("ship", "p3", "var"),
        ],
        initial={"o0", "p0"},
        final={"o3", "p3"},
    )  # fmt: skip


def test_the_running_example_fits_the_object_centric_petri_net() -> None:
    """Example 1 of Gianola et al.: the products are shipped with the wrong orders, but an
    object-centric Petri net does not track which product belongs to which order, so every event
    is a synchronous move."""
    types = {"o1": "order", "o2": "order", "p1": "product", "p2": "product"}
    events = [
        ("place order", ["o1", "p1"]), ("payment", ["o1"]), ("pick item", ["p1"]),
        ("place order", ["o2", "p2"]), ("pick item", ["p2"]), ("payment", ["o2"]),
        ("ship", ["o1", "p2"]), ("ship", ["o2", "p1"]),
    ]  # fmt: skip
    alignment = aligned(log(events, types), fig1a())
    assert alignment.cost == 0
    assert [m.kind for m in alignment.moves] == ["sync"] * 8
