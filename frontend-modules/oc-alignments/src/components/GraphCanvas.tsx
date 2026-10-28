import { Box, Center, Loader } from "@mantine/core";
import {
  Background,
  Controls,
  type Edge,
  type EdgeTypes,
  type Node,
  type NodeTypes,
  Panel,
  ReactFlow,
  ReactFlowProvider,
  useReactFlow,
  useStore,
} from "@xyflow/react";
import { type ReactNode, useEffect } from "react";

export interface GraphCanvasProps {
  nodes: Node[];
  edges: Edge[];
  nodeTypes: NodeTypes;
  edgeTypes?: EdgeTypes;
  /** False while the layout is computed. */
  ready: boolean;
  /** Changes when the graph itself changes (not its highlighting): the view then fits again. */
  layoutKey: string;
  height: number;
  onNodeClick?: (id: string) => void;
  onPaneClick?: () => void;
  /** Shown in the top left corner, e.g. a legend. */
  overlay?: ReactNode;
}

// Small graphs are shown at their natural size rather than blown up.
const FIT = { padding: 0.08, maxZoom: 1 };

function FitOnChange({ layoutKey, height }: { layoutKey: string; height: number }) {
  const { fitView } = useReactFlow();
  // Fit whenever the graph or the canvas's size changes, a frame later, once React Flow knows
  // the new size. Nodes come with their sizes, so this needs no measuring first.
  const size = useStore((state) => `${state.width}x${state.height}`);
  useEffect(() => {
    if (!layoutKey || !height) return;
    const frame = requestAnimationFrame(() => void fitView(FIT));
    return () => cancelAnimationFrame(frame);
  }, [layoutKey, size, height, fitView]);
  return null;
}

// A node-link diagram in a framed box, as all graphs of the module are drawn.
export default function GraphCanvas({
  nodes,
  edges,
  nodeTypes,
  edgeTypes,
  ready,
  layoutKey,
  height,
  onNodeClick,
  onPaneClick,
  overlay,
}: GraphCanvasProps) {
  return (
    <Box
      style={{
        height,
        border: "1px solid var(--mantine-color-default-border)",
        borderRadius: "var(--mantine-radius-md)",
        overflow: "hidden",
        background: "var(--mantine-color-body)",
      }}
    >
      {ready ? (
        <ReactFlowProvider>
          <ReactFlow
            nodes={nodes}
            edges={edges}
            nodeTypes={nodeTypes}
            edgeTypes={edgeTypes}
            fitView
            fitViewOptions={FIT}
            minZoom={0.1}
            nodesDraggable={false}
            nodesConnectable={false}
            elementsSelectable={!!onNodeClick}
            panOnDrag
            // The wheel scrolls the page; zoom with a pinch or the controls.
            zoomOnScroll={false}
            preventScrolling={false}
            zoomOnPinch
            zoomOnDoubleClick
            onNodeClick={onNodeClick ? (_, node) => onNodeClick(node.id) : undefined}
            onPaneClick={onPaneClick}
            proOptions={{ hideAttribution: true }}
          >
            <FitOnChange layoutKey={layoutKey} height={height} />
            <Background gap={24} size={1} />
            <Controls showInteractive={false} />
            {overlay && <Panel position="top-left">{overlay}</Panel>}
          </ReactFlow>
        </ReactFlowProvider>
      ) : (
        <Center h="100%">
          <Loader size="sm" />
        </Center>
      )}
    </Box>
  );
}
