"""Optimal object-centric alignments (Liss, Adams, van der Aalst: Object-Centric Alignments, ER 2023).

The search runs over the states of the synchronous product without building it: a state is the
set of events done (the log side) and the marking of the net, a set of (place, object) tokens.

- An event is enabled once the events before it, of each of its objects, are done.
- A transition fires with a binding: for each type it consumes, objects present in all of its
  input places of that type; one object for a normal arc, any number for a variable arc (not
  none at all). Each object goes to every output place of its type.
- Initially every initial place holds all objects of its type; the run ends when every event is
  done and the marking is exactly: every final place holds all objects of its type.
- A synchronous move fires a transition labelled with an enabled event's activity, bound to
  exactly the event's objects (cost 0). A log move does the event alone, a model move fires alone;
  both cost their number of objects, a silent model move ε.

Dijkstra in the paper; here A*, with the cost of events no transition can match as the estimate
(they can only be log moves), so the cost is the same and fewer states are visited.

The state space grows exponentially with the objects of an execution (a variable arc can bind any
subset of them), so the search keeps to its limits even inside one step: a time limit, and a bound
on the states it keeps and on the tokens their markings hold, which bounds its memory.
"""

import heapq
import itertools
import time
from collections import defaultdict
from collections.abc import Callable, Iterator, Mapping, Sequence
from dataclasses import dataclass

from ocelescope_module_oc_alignments.domain.exceptions import NoAlignment, SearchAborted
from ocelescope_module_oc_alignments.domain.models.alignment import EPSILON, UNIT, Alignment, Move
from ocelescope_module_oc_alignments.domain.models.log import Event
from ocelescope_module_oc_alignments.domain.models.net import ObjectCentricNet

Token = tuple[str, str]  # (place, object)
Marking = frozenset[Token]
State = tuple[int, Marking]  # (events done as a bit set, marking)
Binding = tuple[tuple[str, tuple[str, ...]], ...]  # ((type, objects), ...), types sorted


@dataclass(frozen=True)
class _Transition:
    id: str
    label: str | None
    inputs: dict[str, tuple[str, ...]]  # type -> input places
    outputs: dict[str, tuple[str, ...]]  # type -> output places
    variable: frozenset[str]  # types with variable arcs


@dataclass(frozen=True)
class _Event:
    id: str
    activity: str
    objects: tuple[str, ...]
    by_type: dict[str, tuple[str, ...]]
    before: int  # bit set of the events directly before it, per object
    cost: int


def _transitions(net: ObjectCentricNet) -> list[_Transition]:
    types = {p.id: p.object_type for p in net.places}
    result = []
    for t in net.transitions:
        inputs: dict[str, list[str]] = defaultdict(list)
        outputs: dict[str, list[str]] = defaultdict(list)
        variable: set[str] = set()
        for arc in net.arcs:
            if arc.target == t.id:
                inputs[types[arc.source]].append(arc.source)
                if arc.variable:
                    variable.add(types[arc.source])
            elif arc.source == t.id:
                outputs[types[arc.target]].append(arc.target)
                if arc.variable:
                    variable.add(types[arc.target])
        result.append(
            _Transition(
                id=t.id,
                label=t.label,
                inputs={k: tuple(v) for k, v in sorted(inputs.items())},
                outputs={k: tuple(v) for k, v in sorted(outputs.items())},
                variable=frozenset(variable),
            )
        )
    return result


def _events(events: Sequence[Event], object_types: Mapping[str, str]) -> list[_Event]:
    last: dict[str, int] = {}
    result = []
    for index, event in enumerate(events):
        before = 0
        by_type: dict[str, list[str]] = defaultdict(list)
        for obj in event.objects:
            if obj in last:
                before |= 1 << last[obj]
            last[obj] = index
            by_type[object_types[obj]].append(obj)
        result.append(
            _Event(
                id=event.id,
                activity=event.activity,
                objects=tuple(sorted(event.objects)),
                by_type={k: tuple(sorted(v)) for k, v in sorted(by_type.items())},
                before=before,
                cost=UNIT * max(1, len(event.objects)),
            )
        )
    return result


def _subsets(objects: tuple[str, ...]) -> Iterator[tuple[str, ...]]:
    for size in range(len(objects) + 1):
        yield from itertools.combinations(objects, size)


def _bindings(transition: _Transition, holding: dict[str, set[str]]) -> Iterator[Binding]:
    """The bindings the marking enables: per type, objects in all its input places. Generated one
    at a time: a variable arc alone has 2^n of them."""
    choices: list[tuple[str, tuple[str, ...], bool]] = []
    for object_type, places in transition.inputs.items():
        eligible = tuple(sorted(set.intersection(*(holding.get(p, set()) for p in places))))
        if not eligible:
            return
        choices.append((object_type, eligible, object_type in transition.variable))
    for binding in _product(choices):
        if any(objects for _, objects in binding):
            yield binding


def _product(choices: list[tuple[str, tuple[str, ...], bool]]) -> Iterator[Binding]:
    if not choices:
        yield ()
        return
    (object_type, eligible, variable), rest = choices[0], choices[1:]
    options = _subsets(eligible) if variable else ((o,) for o in eligible)
    for objects in options:
        for binding in _product(rest):
            yield ((object_type, objects), *binding)


def _fire(marking: Marking, transition: _Transition, binding: Binding, shared: dict[Token, Token]) -> Marking:
    """The marking after firing; `shared` holds one copy of each token for all markings."""
    tokens = set(marking)
    for object_type, objects in binding:
        for place in transition.inputs.get(object_type, ()):
            tokens.difference_update((place, o) for o in objects)
        for place in transition.outputs.get(object_type, ()):
            tokens.update(shared.setdefault((place, o), (place, o)) for o in objects)
    return frozenset(tokens)


def _synchronizes(event: _Event, transition: _Transition) -> Binding | None:
    """The binding to the event's objects, if the transition can fire with exactly them."""
    if transition.label != event.activity or not set(event.by_type) <= set(transition.inputs):
        return None
    for object_type in transition.inputs:
        count = len(event.by_type.get(object_type, ()))
        if object_type not in transition.variable and count != 1:
            return None
    if not event.objects:
        return None
    return tuple((t, event.by_type.get(t, ())) for t in transition.inputs)


def _enabled_by(binding: Binding, transition: _Transition, holding: dict[str, set[str]]) -> bool:
    return all(
        set(objects) <= holding.get(place, set())
        for object_type, objects in binding
        for place in transition.inputs[object_type]
    )


def align(
    events: Sequence[Event],
    object_types: Mapping[str, str],
    net: ObjectCentricNet,
    *,
    seconds: float | None = None,
    max_states: int | None = None,
    max_tokens: int | None = None,
    clock: Callable[[], float] = time.monotonic,
) -> Alignment:
    """An optimal alignment of one process execution (its events in timestamp order) with the
    net. Raises NoAlignment if no run reaches the final marking, SearchAborted at a limit:
    `seconds`, the states kept (`max_states`) or the tokens their markings hold (`max_tokens`)."""
    log = _events(events, object_types)
    transitions = _transitions(net)
    objects = sorted({o for e in log for o in e.objects})
    initial: Marking = frozenset(
        (p.id, o) for p in net.places if p.initial for o in objects if object_types[o] == p.object_type
    )
    final: Marking = frozenset(
        (p.id, o) for p in net.places if p.final for o in objects if object_types[o] == p.object_type
    )
    everything = (1 << len(log)) - 1
    labels = net.labels
    unmatched = [(1 << i, e.cost) for i, e in enumerate(log) if e.activity not in labels]

    def estimate(done: int) -> int:
        return sum(cost for bit, cost in unmatched if not done & bit)

    shared: dict[Token, Token] = {token: token for token in initial}
    start: State = (0, initial)
    best: dict[State, int] = {start: 0}
    came_from: dict[State, tuple[State, Move]] = {}
    tie = itertools.count()
    queue: list[tuple[int, int, int, State]] = [(estimate(0), 0, next(tie), start)]
    deadline = clock() + seconds if seconds is not None else None
    tokens = len(initial)
    steps = 0

    def check() -> None:
        if max_states is not None and len(best) > max_states:
            raise SearchAborted(
                f"The search kept {max_states:,} states without finding an alignment: the execution is too large."
            )
        if max_tokens is not None and tokens > max_tokens:
            raise SearchAborted(
                f"The search kept {len(best):,} states with {tokens:,} tokens without finding an alignment: "
                "the execution is too large."
            )
        if deadline is not None and clock() > deadline:
            raise SearchAborted(f"The search took longer than {seconds:g} s.")

    while queue:
        _, cost, _, state = heapq.heappop(queue)
        if cost > best.get(state, cost):
            continue
        done, marking = state
        if done == everything and marking == final:
            moves: list[Move] = []
            while state in came_from:
                state, move = came_from[state]
                moves.append(move)
            return Alignment(moves=tuple(reversed(moves)))

        check()

        holding: dict[str, set[str]] = defaultdict(set)
        for place, obj in marking:
            holding[place].add(obj)

        def push(next_state: State, step: int, move: Move, current: State = state, base: int = cost) -> None:
            nonlocal tokens, steps
            steps += 1
            if steps % 256 == 0:
                check()  # one step can have very many successors
            total = base + step
            if total < best.get(next_state, total + 1):
                if next_state not in best:
                    tokens += len(next_state[1])
                best[next_state] = total
                came_from[next_state] = (current, move)
                heapq.heappush(queue, (total + estimate(next_state[0]), total, next(tie), next_state))

        enabled = [i for i, e in enumerate(log) if not done >> i & 1 and done & e.before == e.before]
        for i in enabled:
            event = log[i]
            push(
                (done | 1 << i, marking),
                event.cost,
                Move(kind="log", event=event.id, activity=event.activity, objects=event.objects, cost=event.cost),
            )
            for transition in transitions:
                binding = _synchronizes(event, transition)
                if binding is not None and _enabled_by(binding, transition, holding):
                    push(
                        (done | 1 << i, _fire(marking, transition, binding, shared)),
                        0,
                        Move(
                            kind="sync",
                            event=event.id,
                            activity=event.activity,
                            transition=transition.id,
                            label=transition.label,
                            objects=event.objects,
                        ),
                    )
        for transition in transitions:
            for binding in _bindings(transition, holding):
                bound = tuple(sorted(o for _, objects in binding for o in objects))
                step = EPSILON if transition.label is None else UNIT * len(bound)
                push(
                    (done, _fire(marking, transition, binding, shared)),
                    step,
                    Move(kind="model", transition=transition.id, label=transition.label, objects=bound, cost=step),
                )

    raise NoAlignment("No run of the net reaches its final marking: the net cannot explain this execution.")
