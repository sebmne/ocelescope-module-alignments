import { useState } from "react";
import {
  AlignmentStrip,
  Badge,
  CoverageBar,
  Group,
  Paper,
  ScrollArea,
  SegmentedControl,
  Table,
  Text,
  Title,
  Tooltip,
} from "../../components";
import { cost } from "../../lib/format";
import { statusOf } from "../../lib/status";
import { toStripMove } from "../../lib/strip";
import type { VariantRow } from "./useResults";

type Style = "trace" | "deviation";

// The variants of a result, as r4pm lists case-centric alignments: how many executions follow
// each, the cost of its alignment, its objects, and the alignment as a strip. A click opens it.
export default function VariantList({
  variants,
  selected,
  onSelect,
  colorOfType,
}: {
  variants: readonly VariantRow[];
  selected: string | null;
  onSelect: (variantId: string) => void;
  colorOfType: (objectType: string) => string;
}) {
  const [style, setStyle] = useState<Style>("trace");
  const total = variants.reduce((sum, variant) => sum + variant.frequency, 0);
  return (
    <Paper withBorder radius="md" p="md">
      <Group justify="space-between" mb="sm">
        <div>
          <Title order={4}>Variants</Title>
          <Text size="xs" c="dimmed">
            {variants.length} variants of {total} process executions
          </Text>
        </div>
        <SegmentedControl
          size="xs"
          value={style}
          onChange={(value) => setStyle(value as Style)}
          data={[
            { value: "trace", label: "Trace" },
            { value: "deviation", label: "Deviation" },
          ]}
        />
      </Group>
      <ScrollArea.Autosize mah={440}>
        <Table highlightOnHover verticalSpacing={6} style={{ cursor: "pointer" }}>
          <Table.Thead>
            <Table.Tr>
              <Table.Th ta="right">Executions</Table.Th>
              <Table.Th ta="right">Share</Table.Th>
              <Table.Th ta="right">Cost</Table.Th>
              <Table.Th>Objects</Table.Th>
              <Table.Th>Alignment</Table.Th>
            </Table.Tr>
          </Table.Thead>
          <Table.Tbody>
            {variants.map((variant) => (
              <Table.Tr
                key={variant.id}
                onClick={() => onSelect(variant.id)}
                bg={variant.id === selected ? "var(--mantine-primary-color-light)" : undefined}
                aria-selected={variant.id === selected}
              >
                <Table.Td ta="right" ff="monospace">
                  {variant.frequency.toLocaleString()}
                </Table.Td>
                <Table.Td w={1}>
                  <CoverageBar
                    value={(100 * variant.frequency) / total}
                    label={`${((100 * variant.frequency) / total).toFixed(1)} %`}
                  />
                </Table.Td>
                <Table.Td ta="right" w={1}>
                  <Cost variant={variant} />
                </Table.Td>
                <Table.Td w={1}>
                  <TypeCounts objects={variant.objects} colorOfType={colorOfType} />
                </Table.Td>
                <Table.Td style={{ maxWidth: 0, width: "100%" }}>
                  {variant.moves.length > 0 ? (
                    <div style={{ overflowX: "auto", overflowY: "hidden" }}>
                      <AlignmentStrip
                        singleLine
                        variant={style}
                        moves={variant.moves.map(toStripMove)}
                      />
                    </div>
                  ) : (
                    <Text size="xs" c="dimmed">
                      {variant.error ?? statusOf(variant.status).label}
                    </Text>
                  )}
                </Table.Td>
              </Table.Tr>
            ))}
          </Table.Tbody>
        </Table>
      </ScrollArea.Autosize>
    </Paper>
  );
}

// The cost of a variant's alignment (objects in deviating moves, ε per silent move), or how its
// search ended.
function Cost({ variant }: { variant: VariantRow }) {
  if (variant.cost == null) {
    const status = statusOf(variant.status);
    return (
      <Tooltip label={variant.error ?? status.label} multiline maw={360}>
        <status.icon size={16} color={status.color} />
      </Tooltip>
    );
  }
  return (
    <Tooltip label="One per object of a log or model move, ε per silent move">
      <Badge variant="light" color={variant.deviations === 0 ? "green" : "gray"} radius="sm">
        {cost(variant.cost)}
      </Badge>
    </Tooltip>
  );
}

// How many objects of each type a variant's executions have.
function TypeCounts({
  objects,
  colorOfType,
}: {
  objects: Record<string, number>;
  colorOfType: (objectType: string) => string;
}) {
  return (
    <Group gap={8} wrap="nowrap">
      {Object.entries(objects).map(([type, count]) => (
        <Tooltip key={type} label={`${count} ${type}`}>
          <Group gap={4} wrap="nowrap">
            <span
              aria-hidden
              style={{ width: 8, height: 8, borderRadius: "50%", background: colorOfType(type) }}
            />
            <Text size="xs" c="dimmed">
              {count}
            </Text>
          </Group>
        </Tooltip>
      ))}
    </Group>
  );
}
