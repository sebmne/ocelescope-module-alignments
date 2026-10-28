import { useResources } from "@ocelescope/api-base";

/**
 * The session's resources as one key, undefined until they are known. Lists the module derives
 * from them (Petri nets, alignments) put it in their query key: any resource added, renamed or
 * removed in Ocelescope gives them a new key, so they are fetched anew, also when it happened
 * while the page was closed. (Ocelescope refreshes its own resource list, not the module's, and
 * keeps fetched lists for minutes.)
 */
export function useResourcesVersion(): string | undefined {
  return useResources()
    .data?.map((resource) => `${resource.id}:${resource.name}`)
    .join();
}
