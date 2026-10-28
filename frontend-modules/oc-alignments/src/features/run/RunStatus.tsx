import { CircleStopIcon } from "lucide-react";
import { ActionIcon, Alert, Group, Loader, Paper, Progress, Text, Tooltip } from "../../components";
import type { RunSummary, VariantProgress } from "./useRun";

// What a share of the progress bar stands for: variants that fit, deviate, or ended otherwise.
const SHARES: { label: string; color: string; matches: (v: VariantProgress) => boolean }[] = [
  {
    label: "fit",
    color: "var(--green-9)",
    matches: (v) => v.status === "aligned" && v.deviations === 0,
  },
  {
    label: "deviate",
    color: "var(--orange-9)",
    matches: (v) => v.status === "aligned" && v.deviations !== 0,
  },
  { label: "hit a search limit", color: "var(--amber-9)", matches: (v) => v.status === "timeout" },
  {
    label: "have no alignment or failed",
    color: "var(--red-9)",
    matches: (v) => ["no_alignment", "failed"].includes(v.status),
  },
];

// The log's newest run, while it runs: its variants as shares of a bar, weighted by their
// executions, and a way to stop it. A failed run says why until it is dismissed.
export default function RunStatus({
  run,
  onCancel,
  onDismiss,
}: {
  run: RunSummary;
  onCancel: () => void;
  onDismiss: () => void;
}) {
  if (run.status === "failed") {
    return (
      <Alert
        color="red"
        title="The alignment failed"
        withCloseButton
        closeButtonLabel="Dismiss"
        onClose={onDismiss}
      >
        {run.error}
      </Alert>
    );
  }
  if (run.status !== "running") return null;
  const executions = run.variants.reduce((sum, v) => sum + v.frequency, 0);
  return (
    <Paper withBorder p="sm" radius="md">
      <Group gap="sm" wrap="nowrap">
        <Loader size="xs" />
        <Text size="sm" style={{ whiteSpace: "nowrap" }}>
          {run.variants.length === 0
            ? "Finding variants…"
            : `${run.finished} of ${run.variants.length} variants`}
        </Text>
        <Progress.Root size="lg" style={{ flex: 1 }}>
          {SHARES.map((share) => {
            const variants = run.variants.filter(share.matches);
            const covered = variants.reduce((sum, v) => sum + v.frequency, 0);
            if (covered === 0) return null;
            return (
              <Tooltip
                key={share.label}
                label={`${variants.length} variants (${covered} executions) ${share.label}`}
              >
                <Progress.Section value={(100 * covered) / executions} color={share.color} />
              </Tooltip>
            );
          })}
        </Progress.Root>
        <Tooltip label="Stop">
          <ActionIcon variant="subtle" color="gray" onClick={onCancel} aria-label="Stop the run">
            <CircleStopIcon size={16} />
          </ActionIcon>
        </Tooltip>
      </Group>
    </Paper>
  );
}
