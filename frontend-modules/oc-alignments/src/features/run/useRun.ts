import { keepPreviousData, useQueryClient } from "@tanstack/react-query";
import {
  getListAlignmentsQueryKey,
  getListPetriNetsQueryKey,
  getListRunsQueryKey,
  type RunSummary,
  useCancelRun,
  useDeleteRun,
  useListPetriNets,
  useListRuns,
  usePetriNetResourceType,
  useStartRun,
} from "../../api/ocAlignments";
import { useResourcesVersion } from "../../hooks/useResourcesVersion";

export type { RunSummary, VariantProgress } from "../../api/ocAlignments";

/** The log's newest run, followed while it runs, and how to start, cancel or dismiss one. */
export function useRun(ocelId: string) {
  const queryClient = useQueryClient();
  const runs = useListRuns(
    { ocelId },
    {
      query: {
        // follow a run until its alignments are kept
        refetchInterval: (query) =>
          query.state.data?.some(
            (run) => run.status === "running" || (run.status === "done" && !run.alignmentsId),
          )
            ? 1000
            : false,
      },
    },
  );
  const refresh = () => {
    void queryClient.invalidateQueries({ queryKey: getListRunsQueryKey() });
    void queryClient.invalidateQueries({ queryKey: getListAlignmentsQueryKey() });
  };
  const start = useStartRun({ mutation: { onSuccess: refresh } });
  const cancel = useCancelRun({ mutation: { onSuccess: refresh } });
  const dismiss = useDeleteRun({ mutation: { onSuccess: refresh } });
  return {
    latest: runs.data?.[0] ?? null,
    start: (petriNetId: string, secondsPerVariant: number) =>
      start.mutateAsync({ data: { ocelId, petriNetId, secondsPerVariant } }),
    starting: start.isPending,
    startError: start.error,
    cancel: (run: RunSummary) => cancel.mutate({ runId: run.id }),
    dismiss: (run: RunSummary) => dismiss.mutate({ runId: run.id }),
  };
}

/** The session's object-centric Petri nets: the resource type to pick them by, and why one cannot
 *  be aligned with. Fetched anew whenever the session's resources change. */
export function useNets() {
  const version = useResourcesVersion();
  const resourceType = usePetriNetResourceType({
    query: { staleTime: Number.POSITIVE_INFINITY },
  }).data;
  const nets = useListPetriNets({
    query: {
      queryKey: [...getListPetriNetsQueryKey(), version],
      enabled: version !== undefined,
      placeholderData: keepPreviousData,
    },
  }).data;
  return {
    resourceType,
    problemOf: (netId: string) => nets?.find((net) => net.id === netId)?.problem ?? null,
  };
}
