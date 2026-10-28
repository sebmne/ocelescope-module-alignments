"""Process executions and variants."""

from datetime import UTC, datetime

from nets import log, order_process

from ocelescope_module_oc_alignments.domain.models.alignment_set import AlignmentSet, VariantAlignment, VariantOutcome
from ocelescope_module_oc_alignments.domain.services.executions import process_executions, variants
from ocelescope_module_oc_alignments.domain.services.search import align

TYPES = {"o1": "order", "o2": "order", "o3": "order", "i1": "item", "i2": "item", "i3": "item", "i4": "item"}


def test_executions_are_the_connected_components() -> None:
    the_log = log(
        [
            ("place order", ["o1", "i1"]),
            ("place order", ["o2", "i2", "i3"]),
            ("pay", ["o1"]),
            ("pick item", ["i3"]),
            ("note", []),
        ],
        TYPES,
    )
    executions = process_executions(the_log)
    assert [(x.events, x.objects) for x in executions] == [
        (("e1", "e3"), ("i1", "o1")),
        (("e2", "e4"), ("i2", "i3", "o2")),
        (("e5",), ()),
    ]


def test_isomorphic_executions_share_a_variant_and_its_alignment() -> None:
    the_log = log(
        [
            ("place order", ["o1", "i1"]),
            ("place order", ["o2", "i2"]),
            ("pick item", ["i2"]),
            ("pick item", ["i1"]),
            ("ship", ["o1", "i1"]),
            ("ship", ["o2", "i2"]),
            ("place order", ["o3", "i3", "i4"]),
        ],
        TYPES,
    )
    executions = process_executions(the_log)
    found = variants(the_log, executions)
    assert [(v.id, v.frequency) for v in found] == [("v1", 2), ("v2", 1)]
    first = found[0]
    rep, other = first.executions
    assert rep.events == {e: e for e in rep.events}  # the representative maps onto itself
    assert other.objects == {"o1": "o2", "i1": "i2"}
    assert other.events == {"e1": "e2", "e4": "e3", "e5": "e6"}

    # the representative's alignment, renamed, is an optimal alignment of the other execution
    events = {e.id: e for e in the_log.events}
    rep_events = [events[e] for e in executions[rep.execution].events]
    other_events = [events[e] for e in executions[other.execution].events]
    rep_alignment = align(rep_events, TYPES, order_process())
    renamed = rep_alignment.renamed(other.events, other.objects)
    assert renamed.cost == align(other_events, TYPES, order_process()).cost
    assert {m.event for m in renamed.moves if m.event} == {"e2", "e3", "e6"}


def test_the_order_of_each_objects_events_tells_variants_apart() -> None:
    the_log = log(
        [
            ("a", ["o1"]),
            ("b", ["o1"]),
            ("b", ["o2"]),
            ("a", ["o2"]),
        ],
        TYPES,
    )
    assert len(variants(the_log, process_executions(the_log))) == 2


def test_each_execution_gets_its_variants_alignment_in_its_own_events_and_objects() -> None:
    """What the API serves for an execution (AlignmentSet.execution): the variant's alignment,
    renamed onto the execution, as optimal as aligning the execution itself."""
    the_log = log(
        [
            ("place order", ["o1", "i1"]),
            ("place order", ["o2", "i2"]),
            ("pick item", ["i2"]),
            ("ship", ["o2", "i2"]),
            ("pick item", ["i1"]),
            ("ship", ["o1", "i1"]),
        ],
        TYPES,
    )
    executions = process_executions(the_log)
    (variant,) = variants(the_log, executions)
    events = {e.id: e for e in the_log.events}
    representative = [events[e] for e in executions[variant.representative].events]
    alignments = AlignmentSet(
        log_name="log",
        net_name="net",
        net=order_process(),
        created_at=datetime(2024, 1, 1, tzinfo=UTC),
        seconds_per_variant=10,
        events=the_log.events,
        object_types=TYPES,
        executions=executions,
        variants=(
            VariantAlignment(
                variant=variant,
                outcome=VariantOutcome(status="aligned", alignment=align(representative, TYPES, order_process())),
            ),
        ),
    )
    for execution in executions:
        served = alignments.execution(execution.index)
        own = [events[e] for e in execution.events]
        assert served.alignment is not None
        assert {m.event for m in served.alignment.moves if m.event} == set(execution.events)
        assert {o for m in served.alignment.moves for o in m.objects} <= set(execution.objects)
        assert served.alignment.cost == align(own, TYPES, order_process()).cost
