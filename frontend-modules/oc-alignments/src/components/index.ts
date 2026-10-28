// The module's building blocks: the only place that knows the component libraries. Controls and
// layout are Mantine's, as in Ocelescope itself; alignment visuals are r4pm's, as in Ocelescope's
// case-centric alignments; the graph canvas is React Flow.

export {
  ActionIcon,
  Alert,
  Badge,
  Box,
  Button,
  Center,
  Flex,
  Group,
  Loader,
  NumberInput,
  Paper,
  Progress,
  ScrollArea,
  SegmentedControl,
  Select,
  Stack,
  Table,
  Text,
  Title,
  Tooltip,
} from "@mantine/core";
export { ResourceSelect } from "@ocelescope/resources";
export {
  AlignmentStrip,
  CoverageBar,
  type ResolvedMove as StripMove,
  StatCards,
  type StatItem,
  TraceAlignmentStrip,
} from "@r4pm/components";
export { default as GraphCanvas, type GraphCanvasProps } from "./GraphCanvas";
export { default as ObjectChips } from "./ObjectChips";
export { default as RoutedEdge, type RoutedEdgeData } from "./RoutedEdge";
