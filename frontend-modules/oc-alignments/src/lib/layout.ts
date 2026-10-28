import ELK from "elkjs/lib/elk.bundled.js";
import type { ElkExtendedEdge } from "elkjs/lib/elk-api";

const elk = new ELK();

export type LayoutNode = { id: string; width: number; height: number };
export type LayoutEdge = { id: string; source: string; target: string };
export type Point = { x: number; y: number };
export type Positions = Record<string, Point>;
/** A laid-out graph: the nodes' top left corners, and each edge's route around the nodes. */
export type Layout = { nodes: Positions; edges: Record<string, Point[]> };
export type LayoutOptions = { spacing?: number; routing?: "POLYLINE" | "ORTHOGONAL" };

/** A left-to-right layered layout of a graph, computed by ELK. */
export async function layeredLayout(
  nodes: LayoutNode[],
  edges: LayoutEdge[],
  { spacing = 40, routing = "POLYLINE" }: LayoutOptions = {},
): Promise<Layout> {
  const graph = await elk.layout({
    id: "root",
    layoutOptions: {
      "elk.algorithm": "layered",
      "elk.direction": "RIGHT",
      "elk.spacing.nodeNode": String(spacing),
      "elk.layered.spacing.nodeNodeBetweenLayers": String(spacing * 1.5),
      "elk.edgeRouting": routing,
      // within a layer, keep the order the nodes are given in (e.g. the moves' order)
      "elk.layered.considerModelOrder.strategy": "NODES_AND_EDGES",
    },
    children: nodes,
    edges: edges.map((e) => ({ id: e.id, sources: [e.source], targets: [e.target] })),
  });
  return {
    nodes: Object.fromEntries(
      (graph.children ?? []).map((n) => [n.id, { x: n.x ?? 0, y: n.y ?? 0 }]),
    ),
    edges: Object.fromEntries(
      ((graph.edges ?? []) as ElkExtendedEdge[]).map((e) => [
        e.id,
        (e.sections ?? []).flatMap((s) => [s.startPoint, ...(s.bendPoints ?? []), s.endPoint]),
      ]),
    ),
  };
}
