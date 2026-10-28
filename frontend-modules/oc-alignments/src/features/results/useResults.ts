import { keepPreviousData } from "@tanstack/react-query";
import {
  getListAlignmentsQueryKey,
  useGetAlignments,
  useListAlignments,
} from "../../api/ocAlignments";
import { useResourcesVersion } from "../../hooks/useResourcesVersion";

export type { AlignmentSetSummary, AlignmentsOverview, VariantRow } from "../../api/ocAlignments";

/** The alignments kept for the log, newest first, fetched anew whenever the session's resources
 *  change. */
export function useResults(ocelId: string) {
  const version = useResourcesVersion();
  return useListAlignments(
    { ocelId },
    {
      query: {
        queryKey: [...getListAlignmentsQueryKey({ ocelId }), version],
        enabled: version !== undefined,
        placeholderData: keepPreviousData,
      },
    },
  );
}

/** One kept result: its summary and every variant. */
export const useResult = (alignmentsId: string | null) =>
  useGetAlignments(alignmentsId ?? "", { query: { enabled: !!alignmentsId } });
