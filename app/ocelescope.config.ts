import type { OcelescopeConfig } from "@ocelescope/core";
import management from "@ocelescope/management";
import discovery from "@ocelescope/discovery"
import ocAlignmentsModule from "@instance/oc-alignments";

// `pnpm run add:frontend` adds local frontend modules here.
export default {
	modules: [management,discovery, ocAlignmentsModule],
} satisfies OcelescopeConfig;
