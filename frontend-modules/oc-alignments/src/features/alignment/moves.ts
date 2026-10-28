import type { AlignedExecution, Event, Move } from "../../api/ocAlignments";
import { MOVE_COLORS, type MoveColorKey } from "../../lib/colors";

/** A move with its event looked up, its position in the alignment and its color. */
export type ResolvedMove = {
  position: number;
  kind: Move["kind"];
  event: Event | null;
  activity: string | null;
  transition: string | null;
  /** The transition's label; null for a silent one. */
  label: string | null;
  objects: string[];
  cost: number;
  colorKey: MoveColorKey;
  color: string;
};

export const hasLog = (move: ResolvedMove) => move.kind !== "model";
export const hasModel = (move: ResolvedMove) => move.kind !== "log";
export const isSilent = (move: ResolvedMove) => move.kind === "model" && move.label == null;
/** What a move fired: its transition's label, or τ. */
export const firing = (move: ResolvedMove) => move.label ?? "τ";

export function resolveMoves(execution: AlignedExecution): ResolvedMove[] {
  const events = new Map(execution.events.map((event) => [event.id, event]));
  return (execution.alignment?.moves ?? []).map((move, position) => {
    const colorKey: MoveColorKey =
      move.kind === "model" && move.label == null ? "silent" : move.kind;
    return {
      position,
      kind: move.kind,
      event: move.event ? (events.get(move.event) ?? null) : null,
      activity: move.activity ?? null,
      transition: move.transition ?? null,
      label: move.label ?? null,
      objects: [...(move.objects ?? [])],
      cost: move.cost ?? 0,
      colorKey,
      color: MOVE_COLORS[colorKey],
    };
  });
}

/** The moves to show: silent model moves only if asked for. */
export const shownMoves = (moves: readonly ResolvedMove[], showSilent: boolean) =>
  showSilent ? [...moves] : moves.filter((move) => !isSilent(move));

/**
 * What is shown: the whole alignment, or its log or model projection (Liss et al., Fig. 4): only
 * the moves with a log or a model side, and only that side.
 */
export type View = "alignment" | "log" | "model";

export const projection = (moves: readonly ResolvedMove[], view: View) =>
  moves.filter((move) =>
    view === "log" ? hasLog(move) : view === "model" ? hasModel(move) : true,
  );

/** The objects of a move on the shown sides (a synchronous move has the same on both). */
export const objectsIn = (move: ResolvedMove, view: View): readonly string[] =>
  (view === "log" && !hasLog(move)) || (view === "model" && !hasModel(move)) ? [] : move.objects;

export type FlowEdge = { source: number; target: number; objects: string[] };

/**
 * How the objects flow through the moves, as Liss et al. draw an object-centric alignment (Fig.
 * 5): for every object, an edge from each move holding it to the next one. In the log projection
 * this is the process execution; in the model projection, the run as a partial order.
 */
export function objectFlow(moves: readonly ResolvedMove[], view: View): FlowEdge[] {
  const last = new Map<string, number>();
  const edges = new Map<string, FlowEdge>();
  for (const move of moves) {
    for (const object of objectsIn(move, view)) {
      const source = last.get(object);
      last.set(object, move.position);
      if (source === undefined) continue;
      const key = `${source}-${move.position}`;
      const edge = edges.get(key) ?? { source, target: move.position, objects: [] };
      edge.objects.push(object);
      edges.set(key, edge);
    }
  }
  return [...edges.values()];
}
