"""Small nets and logs for the tests, written compactly."""

from datetime import UTC, datetime, timedelta

from ocelescope_module_oc_alignments.domain.models.log import Event, EventLog
from ocelescope_module_oc_alignments.domain.models.net import NetArc, NetPlace, NetTransition, ObjectCentricNet

START = datetime(2024, 1, 1, 9, tzinfo=UTC)


def net(
    places: dict[str, str],
    transitions: dict[str, str | None],
    arcs: list[tuple[str, str] | tuple[str, str, str]],
    initial: set[str],
    final: set[str],
) -> ObjectCentricNet:
    """places: id -> type; transitions: id -> label (None: silent); arcs: (source, target[, "var"])."""
    return ObjectCentricNet(
        places=tuple(NetPlace(id=p, object_type=t, initial=p in initial, final=p in final) for p, t in places.items()),
        transitions=tuple(NetTransition(id=t, label=label) for t, label in transitions.items()),
        arcs=tuple(NetArc(source=a[0], target=a[1], variable=len(a) == 3) for a in arcs),
    )


def log(events: list[tuple[str, list[str]]], types: dict[str, str], name: str = "log") -> EventLog:
    """events: (activity, objects), one minute apart; ids e1, e2, ..."""
    return EventLog(
        name=name,
        events=tuple(
            Event(id=f"e{i}", activity=activity, timestamp=START + timedelta(minutes=i), objects=tuple(sorted(objs)))
            for i, (activity, objs) in enumerate(events, start=1)
        ),
        object_types=types,
    )


def order_process(variable_items: bool = True) -> ObjectCentricNet:
    """An order is placed with its items (variable arc), then the order is paid and the items are
    picked one by one, then all ship together."""
    v = ("var",) if variable_items else ()
    item_arcs: list = [("i0", "place", *v), ("place", "i1", *v), ("i2", "ship", *v), ("ship", "i3", *v)]
    return net(
        places={
            "o0": "order",
            "o1": "order",
            "o2": "order",
            "o3": "order",
            "i0": "item",
            "i1": "item",
            "i2": "item",
            "i3": "item",
        },
        transitions={"place": "place order", "pay": "pay", "pick": "pick item", "ship": "ship"},
        arcs=[
            ("o0", "place"),
            ("place", "o1"),
            ("o1", "pay"),
            ("pay", "o2"),
            ("o2", "ship"),
            ("ship", "o3"),
            ("i1", "pick"),
            ("pick", "i2"),
            *item_arcs,
        ],
        initial={"o0", "i0"},
        final={"o3", "i3"},
    )
