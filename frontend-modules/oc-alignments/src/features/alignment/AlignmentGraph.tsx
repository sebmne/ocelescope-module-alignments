import { type Edge, MarkerType, type Node } from "@xyflow/react";
import { useEffect, useMemo, useRef, useState } from "react";
import { GraphCanvas, RoutedEdge } from "../../components";
import { useLayeredLayout } from "../../hooks/useLayeredLayout";
import MoveNode, { MOVE_WIDTH, type MoveNodeData, moveHeight } from "./MoveNode";
import { objectFlow, objectsIn, projection, type ResolvedMove, type View } from "./moves";

const nodeTypes = { move: MoveNode };
const edgeTypes = { routed: RoutedEdge };
const NEUTRAL = "var(--gray-9)";

// The alignment as a graph of moves, linked along their objects, as Liss et al. draw it. A click
// on a move follows its objects: their paths stay, the rest fades.
export default function AlignmentGraph({
  moves,
  view,
  colorOf,
}: {
  moves: readonly ResolvedMove[];
  view: View;
  colorOf: (object: string) => string;
}) {
  const [selected, setSelected] = useState<number | null>(null);
  const shown = useMemo(() => projection(moves, view), [moves, view]);
  const flow = useMemo(() => objectFlow(shown, view), [shown, view]);
  const heights = useMemo(
    () => new Map(shown.map((move) => [move.position, moveHeight(move, view)])),
    [shown, view],
  );

  const layoutNodes = useMemo(
    () =>
      shown.map((move) => ({
        id: String(move.position),
        width: MOVE_WIDTH,
        height: heights.get(move.position) ?? 0,
      })),
    [shown, heights],
  );
  const layoutEdges = useMemo(
    () =>
      flow.map((e) => ({
        id: `${e.source}-${e.target}`,
        source: String(e.source),
        target: String(e.target),
      })),
    [flow],
  );
  const layout = useLayeredLayout(layoutNodes, layoutEdges, { spacing: 36, routing: "ORTHOGONAL" });
  const positions = layout?.nodes ?? null;

  // the objects of the selected move, if it is shown
  const focus = useMemo(() => {
    const move = shown.find((m) => m.position === selected);
    return move ? new Set(objectsIn(move, view)) : null;
  }, [shown, selected, view]);

  const nodes = useMemo<Node<MoveNodeData>[]>(
    () =>
      positions
        ? shown.map((move) => ({
            id: String(move.position),
            type: "move",
            position: positions[String(move.position)] ?? { x: 0, y: 0 },
            width: MOVE_WIDTH,
            height: heights.get(move.position) ?? 0,
            data: {
              move,
              view,
              height: heights.get(move.position) ?? 0,
              selected: move.position === selected,
              dimmed: focus !== null && !objectsIn(move, view).some((o) => focus.has(o)),
              colorOf,
            },
          }))
        : [],
    [shown, positions, heights, view, selected, focus, colorOf],
  );

  const edges = useMemo<Edge[]>(
    () =>
      flow.map((edge) => {
        const followed = focus ? edge.objects.filter((o) => focus.has(o)) : edge.objects;
        const lit = followed.length > 0;
        const types = new Set(followed.map(colorOf));
        const color = types.size === 1 ? ([...types][0] ?? NEUTRAL) : NEUTRAL;
        return {
          id: `${edge.source}-${edge.target}`,
          type: "routed",
          source: String(edge.source),
          target: String(edge.target),
          data: { points: layout?.edges[`${edge.source}-${edge.target}`] },
          // the objects are named only while followed
          label: focus && lit ? followed.join(", ") : undefined,
          style: { stroke: color, strokeWidth: lit && focus ? 3 : 2, opacity: lit ? 1 : 0.12 },
          markerEnd: { type: MarkerType.ArrowClosed, color },
        };
      }),
    [flow, focus, colorOf, layout],
  );

  // As tall as the laid-out graph at the zoom that fits its width, within limits. While a new
  // layout is computed, as tall as before, so the page does not jump.
  const box = useRef<HTMLDivElement>(null);
  const [width, setWidth] = useState(0);
  useEffect(() => {
    const element = box.current;
    if (!element) return;
    const observer = new ResizeObserver(([entry]) => setWidth(entry?.contentRect.width ?? 0));
    observer.observe(element);
    return () => observer.disconnect();
  }, []);
  const lastHeight = useRef(320);
  const height = useMemo(() => {
    if (!positions || width === 0) return lastHeight.current;
    const right = Math.max(
      0,
      ...shown.map((m) => (positions[String(m.position)]?.x ?? 0) + MOVE_WIDTH),
    );
    const bottom = Math.max(
      0,
      ...shown.map((m) => (positions[String(m.position)]?.y ?? 0) + (heights.get(m.position) ?? 0)),
    );
    // the canvas fits the graph with 8 % padding on each side, and never zooms in
    const zoom = Math.min(1, width / (right * 1.16));
    lastHeight.current = Math.round(Math.min(640, Math.max(160, bottom * zoom * 1.16 + 24)));
    return lastHeight.current;
  }, [positions, shown, heights, width]);

  return (
    <div ref={box}>
      <GraphCanvas
        nodes={nodes}
        edges={edges}
        nodeTypes={nodeTypes}
        edgeTypes={edgeTypes}
        ready={positions !== null}
        layoutKey={`${view}-${shown.length}`}
        height={height}
        onNodeClick={(id) => setSelected((current) => (current === Number(id) ? null : Number(id)))}
        onPaneClick={() => setSelected(null)}
      />
    </div>
  );
}
