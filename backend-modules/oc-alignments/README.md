# OC Alignments backend module

Object-centric alignments after Liss, Adams, van der Aalst (*Object-Centric Alignments*, ER
2023), for Ocelescope, mounted at `/modules/ocAlignments/v1`. FastAPI with a hexagonal
architecture.

A run aligns every **variant** of a log with an **object-centric Petri net** of the session
(Ocelescope's `PetriNet` resource, e.g. discovered by its inductive miner). When it is done, the
alignments are kept as a resource of their own type, **OC Alignments**: the host lists, shows (a
table of variants), exports and imports them, and other modules can read them.

The search is our own implementation, checked against the reference implementation of Liss et
al. (see [Reference check](#reference-check)).

```text
src/ocelescope_module_oc_alignments/
├── module.py                 Ocelescope module and its resource type
├── domain/
│   ├── models/
│   │   ├── log.py            Events, process executions, variants (with the mapping onto their representative)
│   │   ├── net.py            Accepting object-centric Petri nets
│   │   ├── alignment.py      Moves and alignments; costs in thousandths of an object (ε = 1)
│   │   ├── alignment_set.py  The alignments of a log with a net: what is kept and explored
│   │   └── run.py            The run aggregate
│   ├── services/
│   │   ├── executions.py     Process executions (connected components) and variants (isomorphism)
│   │   └── search.py         The optimal alignment of one execution (A*)
│   └── exceptions.py
├── application/
│   ├── ports/                Every external capability, as a structural protocol
│   ├── workflows/            RecordRunProgress: keeps a run up to date, keeps its alignments when done
│   └── use_cases/            Entry operations + dataclass commands
├── infrastructure/
│   ├── adapters/             <technology>_<port>.py
│   ├── aligner/              The search in a process of its own per run, variants in parallel workers
│   └── alignments_resource.py  OC Alignments as an Ocelescope resource
└── api/                      Composition root, error mapping, one route per file
```

## Semantics

As the reference implementation computes them:

- **Process executions** are the connected components of the graph of events and objects.
  **Variants** are isomorphism classes of executions: events labelled by activity, objects by
  type, each object linked to its events in their order. The isomorphism maps events and objects,
  so one alignment per variant carries over to each of its executions (`GET .../executions/{i}`).
  ocpa hashes a graph of events only, which may join executions whose objects run differently.
- **Log side:** each object's events in timestamp order; an event is enabled once the events
  before it, of each of its objects, are done.
- **Model side:** a place holds objects of one type. A normal arc moves one object, a variable
  arc any number (a binding with no objects at all is excluded). Only objects present in all
  input places of their type can be bound; they go to every output place of their type.
- **Markings:** every initial place starts with all objects of its type; a run ends when every
  final place holds all objects of its type and no other place holds any.
- **Moves and costs:** a synchronous move fires a transition labelled with an enabled event's
  activity, bound to exactly the event's objects (0). A log move costs the event's objects, a
  model move the bound objects, a silent model move ε. Costs are kept in thousandths of an object,
  so ε = 1 is exact; `deviations` is the cost without ε.
- **Search:** Dijkstra in the paper; here A* with an admissible estimate (events whose activity
  no transition has can only be log moves), with a time limit per variant and bounds on the
  states kept and the tokens their markings hold, checked within each step too (a variable arc
  alone binds any of 2^n subsets), so one large execution cannot exhaust the memory. A variant whose
  worker dies anyway fails alone; the other variants go on.

Costs count objects, as Liss et al. do; Ocelescope's case-centric alignments (one case per
object) count one per move.

## HTTP resources

| Method and path | Result |
| --- | --- |
| GET `/petri-nets` | The session's object-centric Petri nets; `problem` says why one cannot be aligned with |
| GET `/petri-nets/resource-type` | The resource type the nets are stored as, for Ocelescope's resource picker |
| POST `/runs` | `201`, a run started: `{ocelId, petriNetId, secondsPerVariant}` |
| GET `/runs` | The session's runs, newest first, with progress per variant; `?ocelId=` only a log's |
| GET `/runs/{run_id}` | One run; `alignmentsId` once its alignments are kept |
| POST `/runs/{run_id}/cancellation` | Stops a run |
| DELETE `/runs/{run_id}` | `204`, the run forgotten (its alignments stay) |
| GET `/alignments` | The session's OC Alignments, newest first, with the log and net they came from; `?ocelId=` only a log's |
| GET `/alignments/{id}` | Summary and every variant (activities, objects per type, cost, the representative's moves) |
| GET `/alignments/{id}/variants/{variant_id}` | A variant's executions and its representative's alignment |
| GET `/alignments/{id}/executions/{index}` | One execution with its own events and alignment |

Unknown logs, nets, runs, alignments, variants and executions are `404`; starting a run with a net
that cannot be aligned with (e.g. arcs of weight 2) is `422`.

## Rules

- Dependencies point inwards: `module → api → infrastructure → application → domain`;
  application and domain import no FastAPI or Ocelescope; routes reach adapters only through
  `api/dependencies.py`. import-linter enforces this (`pyproject.toml`).
- Models own their invariants: an `ObjectCentricNet` connects places and transitions and
  produces no type it does not consume; a `Move` has the sides of its kind; an `AlignmentSet`
  puts every execution in exactly one variant.
- `Run` changes only through its methods, each returning the next state, so a late result
  cannot reopen a cancelled run. `RunRepository.change` applies them atomically.

## Reference check

`tests/reference/` compares our costs with the reference implementation
(github.com/LukasLiss/object-centric-alignments) on its own examples: the six hand-made nets of
its tests (the paper's example among them) and nets ocpa discovers, against its sample logs.
The reference has no license file, so it is not copied here; it needs Python 3.10 and old
dependencies. Set it up once (into `vendor/`, gitignored):

```sh
uv run python scripts/reference.py
```

The tests are skipped without it. Its results are cached in `vendor/`. Changes to the search
(`domain/services/search.py`) should keep these tests green.

## Checks

`pnpm run check:backend` (repository root) runs ruff, pyright, import-linter and pytest: unit
tests of the search and of executions/variants, HTTP tests with real Ocelescope sessions, and
the reference check when set up.
