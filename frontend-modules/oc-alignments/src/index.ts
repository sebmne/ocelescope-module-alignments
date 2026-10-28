import { defineModule, defineModuleRoute } from "@ocelescope/core";
import { GitCompareArrowsIcon } from "lucide-react";
import dynamic from "next/dynamic";

// The page is built from r4pm and React Flow components, which reach for `document` as they are
// imported: it stays out of the server render.
const ObjectCentricAlignmentsPage = dynamic(() => import("./pages/ObjectCentricAlignmentsPage"), {
  ssr: false,
});

// Object-centric alignments (Liss, Adams, van der Aalst) of the log selected in Ocelescope.
export default defineModule({
  name: "ocAlignments",
  label: "Object-Centric Alignments",
  description:
    "Object-centric alignments after Liss, Adams and van der Aalst: compute, explore and keep them",
  authors: [{ name: "Sebastian Menne" }],
  icon: GitCompareArrowsIcon,
  routes: [
    defineModuleRoute({
      name: "objectCentric",
      label: "Object-Centric",
      component: ObjectCentricAlignmentsPage,
      requiresOcel: true,
    }),
  ],
});
