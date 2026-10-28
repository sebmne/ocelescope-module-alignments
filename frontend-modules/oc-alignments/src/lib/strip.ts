import type { StripMove } from "../components";

/** A move as r4pm's alignment strips draw it: the event's activity on the log side, the fired
 *  transition's label on the model side, τ for a silent transition. */
export function toStripMove(move: {
  kind: "sync" | "log" | "model";
  activity?: string | null;
  label?: string | null;
}): StripMove {
  const silent = move.kind === "model" && move.label == null;
  return {
    kind: move.kind,
    label: move.kind === "model" ? (move.label ?? "τ") : (move.activity ?? ""),
    hidden: silent,
  };
}
