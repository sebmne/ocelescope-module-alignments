import { useEffect, useState } from "react";
import {
  type Layout,
  type LayoutEdge,
  type LayoutNode,
  type LayoutOptions,
  layeredLayout,
} from "../lib/layout";

/** A left-to-right layered layout of a graph (null while ELK is working). */
export const useLayeredLayout = (
  nodes: LayoutNode[],
  edges: LayoutEdge[],
  options: LayoutOptions = {},
): Layout | null => {
  const [layout, setLayout] = useState<Layout | null>(null);
  const key = JSON.stringify([nodes, edges, options]);

  useEffect(() => {
    let cancelled = false;
    setLayout(null);
    void layeredLayout(nodes, edges, options).then((result) => {
      if (!cancelled) setLayout(result);
    });
    return () => {
      cancelled = true;
    };
    // `key` captures nodes, edges and the options
  }, [key]);

  return layout;
};
