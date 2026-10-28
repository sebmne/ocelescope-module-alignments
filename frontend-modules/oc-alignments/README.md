# OC Alignments frontend module

The page of the module (`@instance/oc-alignments`): **Object-Centric Alignments** of the log
selected in Ocelescope's header (the route requires a log). Controls and layout are Mantine's, as
in Ocelescope; the alignment visuals are r4pm's, as in Ocelescope's case-centric alignments.

From top to bottom:
- **Run bar:** the object-centric Petri net (Ocelescope's resource picker, Petri nets only), the
  time limit per variant, ▶ Align. A net the module cannot align with (e.g. arcs of weight 2) shows
  the reason and cannot be aligned. While a run goes, a bar shows its variants as shares weighted
  by their executions (green fit, orange deviate, amber hit a search limit, red no alignment or
  failed) with a stop button; a failed run says why until dismissed. When its alignments are kept,
  they open.
- **Result picker** (next to the title, from two kept results of the log on): the newest result
  by default; `?alignments=` opens a given one.
- **Summary:** r4pm stat cards: process executions, variants, fitting executions, deviations.
- **Variants,** as r4pm lists case-centric alignments: executions, share, cost, objects per type,
  and the representative's alignment as a strip (trace or deviation style). A click opens it.
- **The variant's alignment,** of the representative or of one of its executions:
  - **Graph:** the moves as Liss et al. draw them, the event above, the firing below, ≫ for a
    skipped side, linked along their objects; a click on a move follows its objects;
  - **Log** / **Model:** its projections;
  - **Objects:** each object's own path through the alignment, as r4pm strips.

Moves are colored as r4pm colors them: green synchronous, amber log, orange model, gray silent
(hidden unless the eye toggle shows them). A cost counts the objects of log and model moves, ε per
silent move ("3 + 2ε"); Ocelescope's case-centric alignments count one per move.

```text
src/
├── index.ts      the module and its one route
├── pages/        ObjectCentricAlignmentsPage: composes the features
├── features/
│   ├── run/          the run bar: net, time limit, Align, the run's progress
│   ├── results/      result picker, summary, variant list
│   └── alignment/    a variant's alignment: graph of moves, projections, object strips
├── components/   the only place that knows the component libraries (Mantine, Ocelescope's
│                 resource picker, r4pm), plus the graph canvas (React Flow, laid out by ELK)
├── hooks/        shared hooks (colors, layout, the resources' version)
├── lib/          colors, numbers, status visuals, strip moves
└── api/          the generated backend client (not committed)
```

`.dependency-cruiser.cjs` enforces the layout: features do not import each other, shared folders
know no feature, only `components/` imports the component libraries, no cycles.

| Script | What it does |
| --- | --- |
| `pnpm run build` | Regenerates the API client and builds the module into `dist/`. |
| `pnpm run typecheck` | Type-checks the module. |
| `pnpm run check:architecture` | Checks the layout rules. |

`pnpm run check:frontend` (repository root) runs Biome, the type check and the layout rules.
