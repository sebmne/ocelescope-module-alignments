"""Process executions and their variants.

A process execution is a connected component of the graph that links every event to its objects
(Liss et al., as ocpa extracts them). Two executions belong to the same variant if they are
isomorphic as graphs of events (labelled by activity) and objects (labelled by type), where each
object is linked to its events in their order. That is everything an alignment depends on, so the
isomorphism carries one execution's alignment over to the other, events and objects renamed.
(ocpa hashes a graph of events only, which may join executions whose objects run differently.)
"""

import warnings
from collections import defaultdict
from collections.abc import Iterable

import networkx as nx
from networkx.algorithms.isomorphism import DiGraphMatcher

from ocelescope_module_oc_alignments.domain.models.log import EventLog, Execution, ExecutionMapping, Variant


def process_executions(log: EventLog) -> tuple[Execution, ...]:
    """The connected components of events and objects, in the order of their first events."""
    parent: dict[str, str] = {}

    def find(node: str) -> str:
        while parent.setdefault(node, node) != node:
            parent[node] = parent[parent[node]]
            node = parent[node]
        return node

    for event in log.events:
        root = find(f"e:{event.id}")
        for obj in event.objects:
            other = find(f"o:{obj}")
            if other != root:
                parent[other] = root

    components: dict[str, list[str]] = defaultdict(list)
    for event in log.events:  # in timestamp order: each component's events stay ordered
        components[find(f"e:{event.id}")].append(event.id)
    objects_of = {event.id: event.objects for event in log.events}
    return tuple(
        Execution(
            index=index,
            events=tuple(events),
            objects=tuple(sorted({o for e in events for o in objects_of[e]})),
        )
        for index, events in enumerate(components.values())
    )


def execution_graph(log: EventLog, execution: Execution) -> nx.DiGraph:
    """Events and objects as nodes; each object points to its events, numbered in their order."""
    graph = nx.DiGraph()
    events = {event.id: event for event in log.events}
    position: dict[str, int] = defaultdict(int)
    for event_id in execution.events:
        event = events[event_id]
        graph.add_node(("event", event_id), label=f"event:{event.activity}")
        for obj in event.objects:
            graph.add_node(("object", obj), label=f"object:{log.object_types[obj]}")
            graph.add_edge(("object", obj), ("event", event_id), position=position[obj])
            position[obj] += 1
    return graph


def _same_label(a: dict, b: dict) -> bool:
    return a["label"] == b["label"]


def _same_position(a: dict, b: dict) -> bool:
    return a["position"] == b["position"]


def _mapping(index: int, mapping: dict) -> ExecutionMapping:
    events = {rep[1]: mine[1] for rep, mine in mapping.items() if rep[0] == "event"}
    objects = {rep[1]: mine[1] for rep, mine in mapping.items() if rep[0] == "object"}
    return ExecutionMapping(execution=index, events=events, objects=objects)


def variants(log: EventLog, executions: Iterable[Execution]) -> tuple[Variant, ...]:
    """The variants, most frequent first; each maps its executions onto its representative."""
    classes: list[tuple[int, nx.DiGraph, list[ExecutionMapping]]] = []
    by_hash: dict[str, list[int]] = defaultdict(list)  # hash -> positions in `classes`
    for execution in executions:
        graph = execution_graph(log, execution)
        with warnings.catch_warnings():  # networkx 3.5 changed the hashes; they only bucket here
            warnings.simplefilter("ignore", UserWarning)
            key = nx.weisfeiler_lehman_graph_hash(graph, node_attr="label", edge_attr="position")
        for position in by_hash[key]:
            _, representative, members = classes[position]
            matcher = DiGraphMatcher(representative, graph, node_match=_same_label, edge_match=_same_position)
            if matcher.is_isomorphic():
                members.append(_mapping(execution.index, matcher.mapping))
                break
        else:
            identity = {node: node for node in graph.nodes}
            by_hash[key].append(len(classes))
            classes.append((execution.index, graph, [_mapping(execution.index, identity)]))

    ordered = sorted(classes, key=lambda c: (-len(c[2]), c[0]))
    return tuple(
        Variant(id=f"v{number}", representative=representative, executions=tuple(members))
        for number, (representative, _, members) in enumerate(ordered, start=1)
    )
