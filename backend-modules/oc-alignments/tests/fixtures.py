"""Logs and nets as Ocelescope keeps them, for the HTTP tests."""

from datetime import UTC, datetime, timedelta

import pandas as pd
from ocelescope import OCEL, PetriNet
from ocelescope.resource.default.petri_net import Arc, ArcType, Place, Transition

START = datetime(2024, 1, 1, 9, tzinfo=UTC)


def ocel(events: list[tuple[str, list[str]]], types: dict[str, str]) -> OCEL:
    """events: (activity, objects), one minute apart; ids e1, e2, ..."""
    frame = pd.DataFrame(
        [
            {"ocel:eid": f"e{i}", "ocel:timestamp": START + timedelta(minutes=i), "ocel:activity": activity}
            for i, (activity, _) in enumerate(events, start=1)
        ]
    )
    objects = pd.DataFrame([{"ocel:oid": o, "ocel:type": t} for o, t in types.items()])
    relations = pd.DataFrame(
        [
            {"ocel:eid": f"e{i}", "ocel:oid": o, "ocel:qualifier": "", "ocel:type": types[o]}
            for i, (_, objs) in enumerate(events, start=1)
            for o in objs
        ]
    )
    return OCEL.from_frames(events=frame, objects=objects, relations=relations)


def order_process(weight: int = 1) -> PetriNet:
    """Place an order with its items (variable arcs), pay, pick each item, ship all together."""
    net = PetriNet()
    for name, object_type in [("o0", "order"), ("o1", "order"), ("o2", "order"), ("o3", "order"),
                              ("i0", "item"), ("i1", "item"), ("i2", "item"), ("i3", "item")]:  # fmt: skip
        net.add_place(Place(name=name, object_type=object_type))
    for name in ["place order", "pay", "pick item", "ship"]:
        net.add_transition(Transition(name=name, label=name))
    variable = ArcType.VARIABLE
    for source, target, kind in [
        ("o0", "place order", None), ("place order", "o1", None), ("o1", "pay", None), ("pay", "o2", None),
        ("o2", "ship", None), ("ship", "o3", None), ("i0", "place order", variable), ("place order", "i1", variable),
        ("i1", "pick item", None), ("pick item", "i2", None), ("i2", "ship", variable), ("ship", "i3", variable),
    ]:  # fmt: skip
        net.add_arc(Arc(source=source, target=target, type=kind or ArcType.NORMAL, weight=weight if kind else 1))
    net.initial_marking = {"o0": 1, "i0": 1}
    net.final_marking = {"o3": 1, "i3": 1}
    return net


TYPES = {"o1": "order", "o2": "order", "o3": "order", "i1": "item", "i2": "item", "i3": "item", "i4": "item"}

# two orders of the same variant (one item, fitting), and one with two items where pay is missing
ORDERS = [
    ("place order", ["o1", "i1"]),
    ("place order", ["o2", "i2"]),
    ("pick item", ["i1"]),
    ("pay", ["o1"]),
    ("pick item", ["i2"]),
    ("pay", ["o2"]),
    ("ship", ["o1", "i1"]),
    ("ship", ["o2", "i2"]),
    ("place order", ["o3", "i3", "i4"]),
    ("pick item", ["i3"]),
    ("pick item", ["i4"]),
    ("ship", ["o3", "i3", "i4"]),
]
