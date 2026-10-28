import {
  BanIcon,
  CircleCheckIcon,
  CircleDashedIcon,
  CircleXIcon,
  HourglassIcon,
  LoaderCircleIcon,
  type LucideIcon,
  SearchXIcon,
  TriangleAlertIcon,
} from "lucide-react";

type Status = { icon: LucideIcon; color: string; label: string };

/** How a trace graph or run status looks: an icon and a color, the label only on hover. */
export const STATUS: Record<string, Status> = {
  queued: { icon: CircleDashedIcon, color: "var(--gray-8)", label: "Queued" },
  aligning: { icon: LoaderCircleIcon, color: "var(--accent-9)", label: "Aligning" },
  running: { icon: LoaderCircleIcon, color: "var(--accent-9)", label: "Running" },
  aligned: { icon: CircleCheckIcon, color: "var(--green-9)", label: "Aligned" },
  done: { icon: CircleCheckIcon, color: "var(--green-9)", label: "Done" },
  timeout: {
    icon: HourglassIcon,
    color: "var(--amber-9)",
    label: "Search limit reached (time or size)",
  },
  no_alignment: { icon: SearchXIcon, color: "var(--red-9)", label: "No alignment exists" },
  failed: { icon: CircleXIcon, color: "var(--red-9)", label: "Failed" },
  cancelled: { icon: BanIcon, color: "var(--gray-9)", label: "Cancelled" },
};

export const statusOf = (status: string): Status =>
  STATUS[status] ?? { icon: TriangleAlertIcon, color: "var(--gray-9)", label: status };

/** The color of an aligned trace graph by its cost: green fits, orange deviates. */
export const costColor = (cost: number | null | undefined) =>
  cost === 0 ? "var(--green-9)" : "var(--orange-9)";
