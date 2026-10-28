import { Handle, type Node, type NodeProps, Position } from "@xyflow/react";
import { Box, Flex, ObjectChips, Text, Tooltip } from "../../components";
import { MOVE_TEXT } from "../../lib/colors";
import { cost, dateTime } from "../../lib/format";
import { firing, hasLog, hasModel, isSilent, type ResolvedMove, type View } from "./moves";

export const MOVE_WIDTH = 184;
const INNER = MOVE_WIDTH - 20;
const hidden = { opacity: 0, pointerEvents: "none" as const };

// Rows of object chips a half needs, from the chips' approximate widths.
function chipRows(objects: readonly string[]) {
  let rows = 1;
  let width = 0;
  for (const object of objects) {
    const chip = 26 + 7 * object.length;
    if (width > 0 && width + 4 + chip > INNER) {
      rows += 1;
      width = chip;
    } else {
      width += (width > 0 ? 4 : 0) + chip;
    }
  }
  return rows;
}

const halfHeight = (objects: readonly string[]) => 36 + 22 * chipRows(objects);

/** The height of a move's box: one half per shown side, both halves equally tall. */
export function moveHeight(move: ResolvedMove, view: View) {
  const log = halfHeight(hasLog(move) ? move.objects : []);
  const model = halfHeight(hasModel(move) ? move.objects : []);
  if (view === "log") return log;
  if (view === "model") return model;
  return 2 * Math.max(log, model);
}

function Half({
  title,
  objects,
  muted,
  hint,
  colorOf,
}: {
  title: string | undefined;
  objects: readonly string[];
  muted?: boolean;
  hint?: string;
  colorOf: (object: string) => string;
}) {
  // A skipped side, as the papers write it.
  if (title === undefined) {
    return (
      <Flex
        align="center"
        justify="center"
        style={{ flex: 1, background: "var(--mantine-color-default-hover)" }}
      >
        <Text size="lg" c="dimmed">
          ≫
        </Text>
      </Flex>
    );
  }
  const half = (
    <Flex
      direction="column"
      align="center"
      justify="center"
      gap={4}
      style={{ flex: 1, padding: "4px 8px" }}
    >
      <Text size="sm" fw={700} ta="center" c={muted ? "dimmed" : undefined} truncate maw={INNER}>
        {title}
      </Text>
      {objects.length > 0 && <ObjectChips objects={objects} colorOf={colorOf} justify="center" />}
    </Flex>
  );
  return hint ? <Tooltip label={hint}>{half}</Tooltip> : half;
}

export type MoveNodeData = {
  move: ResolvedMove;
  view: View;
  height: number;
  selected: boolean;
  dimmed: boolean;
  colorOf: (object: string) => string;
};

// A move as Liss et al. and Gianola et al. draw it: the event above, the transition fired below,
// ≫ for a side the move skips. Its kind is its color; a deviation's cost sits in the corner.
export default function MoveNode({
  data: { move, view, height, selected, dimmed, colorOf },
}: NodeProps<Node<MoveNodeData>>) {
  return (
    <>
      <Handle type="target" position={Position.Left} style={hidden} />
      <Box
        style={{
          position: "relative",
          width: MOVE_WIDTH,
          height,
          borderRadius: 8,
          border: `2px solid ${move.color}`,
          background: `color-mix(in srgb, ${move.color} ${selected ? 18 : 5}%, var(--mantine-color-body))`,
          boxShadow: selected
            ? `0 0 0 3px color-mix(in srgb, ${move.color} 35%, transparent)`
            : undefined,
          opacity: dimmed ? 0.3 : 1,
          transition: "opacity 120ms",
        }}
      >
        {!isSilent(move) && move.cost > 0 && (
          <CostBadge cost={move.cost} color={move.color} text={MOVE_TEXT[move.colorKey]} />
        )}
        <Flex direction="column" h="100%" style={{ borderRadius: 6, overflow: "hidden" }}>
          {view !== "model" && (
            <Half
              title={hasLog(move) ? (move.activity ?? undefined) : undefined}
              objects={move.objects}
              hint={move.event ? `${move.event.id} · ${dateTime(move.event.timestamp)}` : undefined}
              colorOf={colorOf}
            />
          )}
          {view === "alignment" && (
            <Box
              style={{ borderTop: `1px solid color-mix(in srgb, ${move.color} 45%, transparent)` }}
            />
          )}
          {view !== "log" && (
            <Half
              title={hasModel(move) ? firing(move) : undefined}
              objects={move.objects}
              muted={isSilent(move)}
              hint={move.transition ?? undefined}
              colorOf={colorOf}
            />
          )}
        </Flex>
      </Box>
      <Handle type="source" position={Position.Right} style={hidden} />
    </>
  );
}

function CostBadge({
  cost: thousandths,
  color,
  text,
}: {
  cost: number;
  color: string;
  text: string;
}) {
  return (
    <Text
      size="xs"
      fw={700}
      style={{
        position: "absolute",
        top: -10,
        right: -8,
        background: color,
        color: text,
        borderRadius: 999,
        padding: "0 7px",
        lineHeight: "18px",
        zIndex: 1,
      }}
    >
      {cost(thousandths)}
    </Text>
  );
}
