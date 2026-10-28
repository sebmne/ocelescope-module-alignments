import { BaseEdge, type Edge, EdgeLabelRenderer, type EdgeProps } from "@xyflow/react";

type Point = { x: number; y: number };
export type RoutedEdgeData = { points?: Point[] };

const RADIUS = 10;

// A polyline with rounded corners.
function roundedPath(points: readonly Point[]) {
  const [first, ...rest] = points;
  if (!first) return "";
  let path = `M ${first.x} ${first.y}`;
  for (let i = 0; i < rest.length; i++) {
    const corner = rest[i] as Point;
    const before = points[i] as Point;
    const after = rest[i + 1];
    if (!after) {
      path += ` L ${corner.x} ${corner.y}`;
      break;
    }
    const into = Math.hypot(corner.x - before.x, corner.y - before.y);
    const out = Math.hypot(after.x - corner.x, after.y - corner.y);
    const r = Math.min(RADIUS, into / 2, out / 2);
    const start = {
      x: corner.x - ((corner.x - before.x) / (into || 1)) * r,
      y: corner.y - ((corner.y - before.y) / (into || 1)) * r,
    };
    const end = {
      x: corner.x + ((after.x - corner.x) / (out || 1)) * r,
      y: corner.y + ((after.y - corner.y) / (out || 1)) * r,
    };
    path += ` L ${start.x} ${start.y} Q ${corner.x} ${corner.y} ${end.x} ${end.y}`;
  }
  return path;
}

// The middle of the longest segment: where a label is least in the way.
function labelPoint(points: readonly Point[]): Point {
  let best = { x: 0, y: 0 };
  let longest = -1;
  for (let i = 1; i < points.length; i++) {
    const a = points[i - 1] as Point;
    const b = points[i] as Point;
    const length = Math.hypot(b.x - a.x, b.y - a.y);
    if (length > longest) {
      longest = length;
      best = { x: (a.x + b.x) / 2, y: (a.y + b.y) / 2 };
    }
  }
  return best;
}

// An edge along the route the layout found around the nodes (a straight line without one).
export default function RoutedEdge({
  id,
  data,
  sourceX,
  sourceY,
  targetX,
  targetY,
  style,
  markerEnd,
  label,
}: EdgeProps<Edge<RoutedEdgeData>>) {
  const points =
    data?.points && data.points.length > 1
      ? data.points
      : [
          { x: sourceX, y: sourceY },
          { x: targetX, y: targetY },
        ];
  const at = labelPoint(points);
  return (
    <>
      <BaseEdge id={id} path={roundedPath(points)} style={style} markerEnd={markerEnd} />
      {label && (
        <EdgeLabelRenderer>
          <div
            className="nodrag nopan"
            style={{
              position: "absolute",
              transform: `translate(-50%, -50%) translate(${at.x}px, ${at.y}px)`,
              fontSize: 11,
              fontWeight: 600,
              color: "var(--gray-12)",
              background: "var(--color-panel-solid)",
              border: "1px solid var(--gray-a5)",
              borderRadius: 4,
              padding: "0 4px",
              pointerEvents: "none",
            }}
          >
            {label}
          </div>
        </EdgeLabelRenderer>
      )}
    </>
  );
}
