import { StatCards } from "../../components";
import type { AlignmentSetSummary } from "./useResults";

// The result at a glance, as r4pm sums up case-centric alignments.
export default function Summary({ summary }: { summary: AlignmentSetSummary }) {
  const fitting = summary.executions === 0 ? 0 : summary.fittingExecutions / summary.executions;
  return (
    <StatCards
      items={[
        { label: "Process executions", value: summary.executions.toLocaleString() },
        {
          label: "Variants",
          value: summary.variants.toLocaleString(),
          hint:
            summary.alignedVariants < summary.variants
              ? `${summary.alignedVariants} aligned`
              : undefined,
        },
        {
          label: "Fitting executions",
          value: `${Math.round(100 * fitting)} %`,
          progress: fitting,
          tone: "good",
        },
        {
          label: "Deviations",
          value: summary.deviations.toLocaleString(),
          hint: "objects in log and model moves",
        },
      ]}
    />
  );
}
