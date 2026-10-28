import { EyeIcon, EyeOffIcon } from "lucide-react";
import { useMemo, useState } from "react";
import { type AlignedExecution, useGetExecution, useGetVariant } from "../../api/ocAlignments";
import {
  ActionIcon,
  Badge,
  Center,
  Group,
  Loader,
  Paper,
  SegmentedControl,
  Select,
  Stack,
  Text,
  Title,
  Tooltip,
} from "../../components";
import { useColors } from "../../hooks/useColors";
import { MOVE_COLORS } from "../../lib/colors";
import { cost } from "../../lib/format";
import { statusOf } from "../../lib/status";
import AlignmentGraph from "./AlignmentGraph";
import { resolveMoves, shownMoves, type View } from "./moves";
import ObjectStrips from "./ObjectStrips";

type Mode = View | "objects";

const MODES: { value: Mode; label: string }[] = [
  { value: "alignment", label: "Graph" },
  { value: "log", label: "Log" },
  { value: "model", label: "Model" },
  { value: "objects", label: "Objects" },
];

const LEGEND = [
  ["sync", "synchronous"],
  ["log", "log"],
  ["model", "model"],
  ["silent", "τ"],
] as const;

// The alignment of a variant, through its representative or one of its executions: as a graph of
// moves linked along their objects (Liss et al., Fig. 5), its log or model projection, or each
// object's own path. Silent moves cost only ε and are hidden unless asked for.
export default function AlignmentDetail({
  alignmentsId,
  variantId,
  objectTypes,
}: {
  alignmentsId: string;
  variantId: string;
  objectTypes: readonly string[];
}) {
  const [executionIndex, setExecutionIndex] = useState<number | null>(null);
  const [mode, setMode] = useState<Mode>("alignment");
  const [showSilent, setShowSilent] = useState(false);
  const variant = useGetVariant(alignmentsId, variantId);
  const single = useGetExecution(alignmentsId, executionIndex ?? -1, {
    query: { enabled: executionIndex !== null },
  });
  const execution = executionIndex === null ? variant.data?.representative : single.data;
  const executions = variant.data?.executions ?? [];
  const alignment = execution?.alignment;

  return (
    <Paper withBorder radius="md" p="md">
      <Stack gap="sm">
        <Group justify="space-between" gap="sm">
          <Group gap="sm">
            <Title order={4}>Variant {variantId}</Title>
            {executions.length > 1 && (
              <Select
                aria-label="Execution"
                size="xs"
                w={220}
                allowDeselect={false}
                value={executionIndex === null ? "representative" : String(executionIndex)}
                onChange={(value) =>
                  setExecutionIndex(
                    value === "representative" || value === null ? null : Number(value),
                  )
                }
                data={[
                  { value: "representative", label: `All ${executions.length} executions` },
                  ...executions.map((x) => ({
                    value: String(x.index),
                    label: `#${x.index} · ${x.objects.join(", ")}`,
                  })),
                ]}
              />
            )}
          </Group>
          {alignment && (
            <Group gap="md">
              <SegmentedControl
                size="xs"
                value={mode}
                onChange={(value) => setMode(value as Mode)}
                data={MODES}
              />
              <Group gap={10}>
                {LEGEND.filter(([key]) => showSilent || key !== "silent").map(([key, label]) => (
                  <Group key={key} gap={4}>
                    <span
                      style={{
                        width: 10,
                        height: 10,
                        borderRadius: 2,
                        background: MOVE_COLORS[key],
                      }}
                    />
                    <Text size="xs" c="dimmed">
                      {label}
                    </Text>
                  </Group>
                ))}
              </Group>
              <Tooltip label={showSilent ? "Hide silent moves" : "Show silent moves"}>
                <ActionIcon
                  variant={showSilent ? "light" : "subtle"}
                  color="gray"
                  disabled={mode === "log"}
                  onClick={() => setShowSilent(!showSilent)}
                  aria-label="Silent moves"
                  aria-pressed={showSilent}
                >
                  {showSilent ? <EyeIcon size={16} /> : <EyeOffIcon size={16} />}
                </ActionIcon>
              </Tooltip>
              <Tooltip label="One per object of a log or model move, ε per silent move">
                <Badge
                  size="lg"
                  radius="sm"
                  color={alignment.deviations === 0 ? "green" : "orange"}
                >
                  {cost(alignment.cost)}
                </Badge>
              </Tooltip>
            </Group>
          )}
        </Group>
        {execution ? (
          <Body
            execution={execution}
            mode={mode}
            showSilent={showSilent}
            objectTypes={objectTypes}
          />
        ) : (
          <Center h={200}>
            <Loader size="sm" />
          </Center>
        )}
      </Stack>
    </Paper>
  );
}

function Body({
  execution,
  mode,
  showSilent,
  objectTypes,
}: {
  execution: AlignedExecution;
  mode: Mode;
  showSilent: boolean;
  objectTypes: readonly string[];
}) {
  const { colorOf } = useColors(objectTypes, execution.objectTypes);
  const moves = useMemo(
    () => shownMoves(resolveMoves(execution), showSilent),
    [execution, showSilent],
  );
  if (!execution.alignment) {
    const status = statusOf(execution.status);
    return (
      <Stack align="center" gap="xs" py="xl">
        <status.icon size={32} color={status.color} />
        <Text size="sm" c="dimmed" ta="center" maw={520}>
          {execution.error ?? status.label}
        </Text>
      </Stack>
    );
  }
  if (mode === "objects") {
    const objects = Object.keys(execution.objectTypes).sort(
      (a, b) =>
        (execution.objectTypes[a] ?? "").localeCompare(execution.objectTypes[b] ?? "") ||
        a.localeCompare(b),
    );
    return <ObjectStrips moves={moves} objects={objects} colorOf={colorOf} />;
  }
  return <AlignmentGraph key={execution.index} moves={moves} view={mode} colorOf={colorOf} />;
}
