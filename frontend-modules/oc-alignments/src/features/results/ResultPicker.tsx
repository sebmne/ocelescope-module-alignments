import { Select } from "../../components";
import { dateTime } from "../../lib/format";
import type { AlignmentSetSummary } from "./useResults";

// Which of the log's kept results is shown: the newest by default, earlier ones on demand.
export default function ResultPicker({
  results,
  selected,
  onSelect,
}: {
  results: readonly AlignmentSetSummary[];
  selected: string | null;
  onSelect: (alignmentsId: string) => void;
}) {
  if (results.length < 2) return null;
  return (
    <Select
      aria-label="Result"
      data={results.map((result) => ({
        value: result.id,
        label: `${result.netName} · ${dateTime(result.createdAt)}`,
      }))}
      value={selected}
      onChange={(value) => value && onSelect(value)}
      allowDeselect={false}
      w={320}
    />
  );
}
