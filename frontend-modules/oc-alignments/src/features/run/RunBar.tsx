import { PlayIcon } from "lucide-react";
import { useEffect, useState } from "react";
import { Alert, Button, Group, NumberInput, Paper, ResourceSelect, Stack } from "../../components";
import { errorMessage } from "../../lib/errors";
import RunStatus from "./RunStatus";
import { useNets, useRun } from "./useRun";

// Align the log selected in Ocelescope with an object-centric Petri net of the session: pick the
// net, set the time limit per variant, press Align. The run shows its progress here; when its
// alignments are kept, they open.
export default function RunBar({
  ocelId,
  onAligned,
}: {
  ocelId: string;
  /** The alignments of a run started here, once they are kept. */
  onAligned: (alignmentsId: string) => void;
}) {
  const { resourceType, problemOf } = useNets();
  const run = useRun(ocelId);
  const [netId, setNetId] = useState<string | null>(null);
  const [seconds, setSeconds] = useState(60);
  const [started, setStarted] = useState<string | null>(null);

  const latest = run.latest;
  useEffect(() => {
    if (latest && latest.id === started && latest.alignmentsId) {
      setStarted(null);
      onAligned(latest.alignmentsId);
    }
  }, [latest, started, onAligned]);

  const problem = netId ? problemOf(netId) : null;
  const running = latest?.status === "running";
  const align = async () => {
    if (!netId) return;
    const startedRun = await run.start(netId, seconds);
    setStarted(startedRun.id);
  };

  return (
    <Stack gap="sm">
      <Paper withBorder p="sm" radius="md">
        <Group align="flex-end" gap="sm">
          <ResourceSelect
            label="Petri net"
            placeholder="An object-centric Petri net of the session"
            type={resourceType}
            disabled={!resourceType}
            value={netId}
            onChange={(value) => setNetId(value)}
            error={problem}
            style={{ flex: 1, minWidth: 240 }}
          />
          <NumberInput
            label="Time limit per variant"
            suffix=" s"
            min={1}
            max={86400}
            value={seconds}
            onChange={(value) => setSeconds(Number(value) || 60)}
            w={170}
          />
          <Button
            leftSection={<PlayIcon size={16} />}
            disabled={!netId || !!problem || running}
            loading={run.starting}
            onClick={() => void align()}
          >
            Align
          </Button>
        </Group>
      </Paper>
      {run.startError != null && (
        <Alert color="red" title="The alignment could not start">
          {errorMessage(run.startError, "The backend refused the run.")}
        </Alert>
      )}
      {latest && (
        <RunStatus
          run={latest}
          onCancel={() => run.cancel(latest)}
          onDismiss={() => run.dismiss(latest)}
        />
      )}
    </Stack>
  );
}
