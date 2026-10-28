// Colors that carry meaning: one per object type, and one per kind of move.

const PALETTE = [
  "#4C8BD6", // blue
  "#F2C230", // yellow
  "#5BAA5B", // green
  "#E07B39", // orange
  "#9B6BC7", // purple
  "#D9538E", // pink
  "#45B5BF", // teal
  "#A0785A", // brown
];
const FALLBACK = "#adb5bd";

/** One color per object type, in the order of the sorted types. */
export function typeColors(
  objectTypes: Iterable<string>,
): (objectType: string | undefined) => string {
  const sorted = [...new Set(objectTypes)].sort();
  const colors = new Map(sorted.map((type, i) => [type, PALETTE[i % PALETTE.length] ?? FALLBACK]));
  return (objectType) => (objectType ? (colors.get(objectType) ?? FALLBACK) : FALLBACK);
}

// The kinds of moves in the colors r4pm's alignment strips use, so all views agree.
export const MOVE_COLORS = {
  sync: "var(--green-9)",
  log: "var(--amber-9)",
  model: "var(--orange-9)",
  silent: "var(--gray-9)",
} as const;

export type MoveColorKey = keyof typeof MOVE_COLORS;

/** Text on a move color, readable also on amber. */
export const MOVE_TEXT: Record<MoveColorKey, string> = {
  sync: "var(--green-contrast)",
  log: "var(--amber-contrast)",
  model: "var(--orange-contrast)",
  silent: "var(--gray-contrast)",
};
